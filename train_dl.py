"""
KhetBuddy — Deep Learning Training Script (PyTorch MLP)
=========================================================
Trains an MLP regressor for crop yield prediction using:
  - PyTorch MLP with BatchNorm, GELU, Dropout
  - Optuna hyperparameter optimization (20 trials, fast inner loop)
  - K-Fold Cross-Validation during tuning
  - Early Stopping to prevent overfitting
  - CosineAnnealingLR learning rate scheduling
  - Gaussian noise data augmentation (handles small dataset)
  - StandardScaler for feature normalization

Output:
  models/dl_yield_model.pt   -- trained PyTorch model state dict + config
  models/dl_scaler.pkl       -- fitted StandardScaler
  models/dl_metrics.json     -- test metrics for comparison report
"""

import sys
import json
import time
import warnings
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict

warnings.filterwarnings("ignore")

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
except ImportError:
    print("PyTorch not found. Install with: pip install torch")
    sys.exit(1)

from sklearn.model_selection import KFold, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
except ImportError:
    print("Optuna not found. Install with: pip install optuna")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))

# ── Config ────────────────────────────────────────────────────────────────────
DATASET_PATH    = Path("datasets/05_complete_training_dataset.csv")
MODEL_DIR       = Path("models")
DL_MODEL_PATH   = MODEL_DIR / "dl_yield_model.pt"
DL_SCALER_PATH  = MODEL_DIR / "dl_scaler.pkl"
DL_METRICS_PATH = MODEL_DIR / "dl_metrics.json"

FEATURE_COLUMNS = [
    "nitrogen", "phosphorus", "potassium", "soil_ph", "soil_moisture",
    "avg_temperature", "total_rainfall", "humidity",
    "nutrient_index", "temperature_deviation", "stress_indicator",
    "crop_enc", "season_enc", "district_enc", "irrigation_enc",
]
TARGET_COLUMN = "yield_qtl_ha"

RANDOM_SEED      = 42
N_OPTUNA_TRIALS  = 20          # fast but sufficient for 89-row dataset
N_FOLDS          = 5
HPO_AUG_FACTOR   = 2           # light augmentation inside Optuna trials
FINAL_AUG_FACTOR = 8           # heavy augmentation for final training
DEVICE           = torch.device("cpu")

torch.manual_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ── Model ─────────────────────────────────────────────────────────────────────
class YieldMLP(nn.Module):
    def __init__(self, input_dim: int, hidden_sizes: List[int], dropout_rates: List[float]):
        super().__init__()
        layers = []
        in_dim = input_dim
        for h, d in zip(hidden_sizes, dropout_rates):
            layers += [nn.Linear(in_dim, h), nn.BatchNorm1d(h), nn.GELU(), nn.Dropout(d)]
            in_dim = h
        layers.append(nn.Linear(in_dim, 1))
        self.network = nn.Sequential(*layers)
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                nn.init.zeros_(m.bias)

    def forward(self, x):
        return self.network(x).squeeze(-1)


# ── Data utilities ────────────────────────────────────────────────────────────
def load_dataset() -> Tuple[np.ndarray, np.ndarray]:
    print(f"\n[DL] Loading dataset: {DATASET_PATH}")
    if not DATASET_PATH.exists():
        print(f"[ERROR] Dataset not found. Run datasets/generate_training_dataset.py first.")
        sys.exit(1)
    df = pd.read_csv(DATASET_PATH)
    missing = [c for c in FEATURE_COLUMNS + [TARGET_COLUMN] if c not in df.columns]
    if missing:
        print(f"[ERROR] Missing columns: {missing}")
        sys.exit(1)
    X = df[FEATURE_COLUMNS].values.astype(np.float32)
    y = df[TARGET_COLUMN].values.astype(np.float32)
    print(f"   X shape: {X.shape}, y range: [{y.min():.1f}, {y.max():.1f}] quintal/ha")
    return X, y


def augment_data(X, y, noise_std, factor):
    n_cont = 11  # continuous features (nitrogen...stress_indicator)
    Xl, yl = [X], [y]
    for _ in range(factor):
        noise = np.zeros_like(X)
        noise[:, :n_cont] = np.random.normal(0, noise_std, (len(X), n_cont))
        Xl.append(X + noise)
        yl.append(y + np.random.normal(0, noise_std * 0.5, len(y)))
    return np.vstack(Xl).astype(np.float32), np.concatenate(yl).astype(np.float32)


def tensors(X, y):
    return torch.tensor(X).to(DEVICE), torch.tensor(y).to(DEVICE)


# ── Training loop ─────────────────────────────────────────────────────────────
def train_epoch(model, loader, opt, crit):
    model.train()
    total = 0.0
    for xb, yb in loader:
        opt.zero_grad()
        loss = crit(model(xb), yb)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        total += loss.item() * len(xb)
    return total / len(loader.dataset)


@torch.no_grad()
def eval_rmse(model, Xt, yt):
    model.eval()
    pred = model(Xt).cpu().numpy()
    return float(np.sqrt(mean_squared_error(yt.cpu().numpy(), pred)))


def fit(model, X_tr, y_tr, X_val, y_val, lr, wd, bs, noise, aug_factor,
        max_ep=300, patience=25, verbose=False):
    Xa, ya = augment_data(X_tr, y_tr, noise, aug_factor)
    Xat, yat = tensors(Xa, ya)
    Xvt, yvt = tensors(X_val, y_val)
    loader   = DataLoader(TensorDataset(Xat, yat), batch_size=bs, shuffle=True)
    crit     = nn.HuberLoss(delta=1.0)
    opt      = optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    sched    = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max_ep, eta_min=lr * 0.01)

    best_rmse, best_state, no_imp = float("inf"), None, 0
    hist_loss, hist_val = [], []

    for ep in range(max_ep):
        tl = train_epoch(model, loader, opt, crit)
        vr = eval_rmse(model, Xvt, yvt)
        sched.step()
        hist_loss.append(tl); hist_val.append(vr)

        if vr < best_rmse - 1e-4:
            best_rmse = vr
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            no_imp = 0
        else:
            no_imp += 1

        if verbose and (ep + 1) % 100 == 0:
            print(f"   Epoch {ep+1:4d} | loss={tl:.4f} | val_rmse={vr:.4f}")
        if no_imp >= patience:
            if verbose: print(f"   Early stop at epoch {ep+1}")
            break

    if best_state:
        model.load_state_dict(best_state)
    return {"best_val_rmse": best_rmse, "epochs": ep + 1,
            "history": {"train_loss": hist_loss, "val_rmse": hist_val}}


# ── Optuna objective ──────────────────────────────────────────────────────────
def make_objective(X_raw, y):
    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_SEED)

    def objective(trial):
        n_lay = trial.suggest_int("n_layers", 2, 4)
        hs    = [trial.suggest_int(f"h{i}", 32, 256, step=16) for i in range(n_lay)]
        dr    = [trial.suggest_float(f"drop{i}", 0.1, 0.5)   for i in range(n_lay)]
        lr    = trial.suggest_float("lr",   1e-4, 1e-2, log=True)
        wd    = trial.suggest_float("wd",   1e-5, 1e-2, log=True)
        bs    = trial.suggest_categorical("batch_size", [8, 16, 32])
        noise = trial.suggest_float("noise_std", 0.01, 0.10)

        fold_rmses = []
        for fi, (tri, vi) in enumerate(kf.split(X_raw)):
            sc = StandardScaler()
            Xtr = sc.fit_transform(X_raw[tri]).astype(np.float32)
            Xvl = sc.transform(X_raw[vi]).astype(np.float32)

            m = YieldMLP(Xtr.shape[1], hs, dr).to(DEVICE)
            r = fit(m, Xtr, y[tri], Xvl, y[vi], lr, wd, bs, noise,
                    aug_factor=HPO_AUG_FACTOR, max_ep=120, patience=15)
            fold_rmses.append(r["best_val_rmse"])
            trial.report(np.mean(fold_rmses), fi)
            if trial.should_prune():
                raise optuna.exceptions.TrialPruned()

        return float(np.mean(fold_rmses))

    return objective


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    MODEL_DIR.mkdir(exist_ok=True)

    # 1. Load
    X, y = load_dataset()

    # 2. Split
    X_tr_raw, X_te_raw, y_tr, y_te = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED)
    print(f"\n[DL] Split: {len(X_tr_raw)} train / {len(X_te_raw)} test")

    # 3. Scale (fit on train only)
    scaler = StandardScaler()
    X_tr = scaler.fit_transform(X_tr_raw).astype(np.float32)
    X_te = scaler.transform(X_te_raw).astype(np.float32)
    print("[DL] StandardScaler fitted (train only -- no leakage)")

    # 4. Optuna HPO
    print(f"\n[DL] Running Optuna HPO ({N_OPTUNA_TRIALS} trials, {N_FOLDS}-fold CV)...")
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=4, n_warmup_steps=2),
    )
    study.optimize(make_objective(X_tr_raw, y_tr), n_trials=N_OPTUNA_TRIALS,
                   show_progress_bar=True)

    bp = study.best_params
    print(f"\n[DL] Best val_RMSE = {study.best_value:.4f}")
    print(f"     Best params: {json.dumps(bp, indent=4)}")

    # 5. Final model with best params
    n_lay = bp["n_layers"]
    hs = [bp[f"h{i}"] for i in range(n_lay)]
    dr = [bp[f"drop{i}"] for i in range(n_lay)]

    print("\n[DL] Training final model (full train set, heavy augmentation)...")
    model = YieldMLP(X_tr.shape[1], hs, dr).to(DEVICE)
    result = fit(model, X_tr, y_tr, X_te, y_te,
                 lr=bp["lr"], wd=bp["wd"], bs=bp["batch_size"], noise=bp["noise_std"],
                 aug_factor=FINAL_AUG_FACTOR, max_ep=800, patience=60, verbose=True)

    elapsed = time.time() - t0

    # 6. Evaluate
    def eval_all(Xt, y_np):
        model.eval()
        with torch.no_grad():
            yp = model(Xt).cpu().numpy()
        return {
            "rmse": round(float(np.sqrt(mean_squared_error(y_np, yp))), 4),
            "r2":   round(float(r2_score(y_np, yp)), 4),
            "mae":  round(float(np.mean(np.abs(y_np - yp))), 4),
            "mape": round(float(np.mean(np.abs((y_np - yp) / np.maximum(y_np, 1))) * 100), 4),
            "y_pred": yp.tolist(), "y_true": y_np.tolist(),
        }

    X_tr_t, y_tr_t = tensors(X_tr, y_tr)
    X_te_t, y_te_t = tensors(X_te, y_te)
    tr_m = eval_all(X_tr_t, y_tr)
    te_m = eval_all(X_te_t, y_te)

    print(f"\n{'='*55}")
    print(f"  FINAL TEST  | RMSE={te_m['rmse']:.4f}  R2={te_m['r2']:.4f}  MAPE={te_m['mape']:.2f}%")
    print(f"  FINAL TRAIN | RMSE={tr_m['rmse']:.4f}  R2={tr_m['r2']:.4f}  MAPE={tr_m['mape']:.2f}%")
    print(f"  Total time  : {elapsed:.1f}s (incl. HPO)")
    print(f"{'='*55}")

    # 7. Save artifacts
    torch.save({
        "model_state_dict": model.state_dict(),
        "config": {"input_dim": X_tr.shape[1], "hidden_sizes": hs, "dropout_rates": dr},
        "best_params": bp,
        "feature_columns": FEATURE_COLUMNS,
    }, DL_MODEL_PATH)
    joblib.dump(scaler, DL_SCALER_PATH)

    metrics_out = {
        "model": "DL_MLP",
        "training_time_sec": round(elapsed, 2),
        "best_params": bp,
        "train": {k: v for k, v in tr_m.items() if k not in ("y_pred", "y_true")},
        "test":  {k: v for k, v in te_m.items() if k not in ("y_pred", "y_true")},
        "test_y_pred":  te_m["y_pred"],
        "test_y_true":  te_m["y_true"],
        "train_y_pred": tr_m["y_pred"],
        "train_y_true": tr_m["y_true"],
        "training_history": result["history"],
    }
    DL_METRICS_PATH.write_text(json.dumps(metrics_out, indent=2))

    print(f"\n[DL] Model saved   -> {DL_MODEL_PATH}")
    print(f"[DL] Scaler saved  -> {DL_SCALER_PATH}")
    print(f"[DL] Metrics saved -> {DL_METRICS_PATH}")
    print("\n[DONE] Now run: python generate_comparison_report.py")


if __name__ == "__main__":
    main()
