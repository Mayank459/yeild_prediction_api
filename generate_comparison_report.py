"""
KhetBuddy — Model Comparison Report Generator
Generates docs/model_comparison_report.html comparing RF vs DL.
Run: python generate_comparison_report.py
"""
import json, sys, math
from pathlib import Path

RF_METRICS = Path("models/rf_metrics.json")
DL_METRICS = Path("models/dl_metrics.json")
OUT_PATH   = Path("docs/model_comparison_report.html")

def load(p):
    if not p.exists():
        print(f"❌ Missing {p}. Run extract_rf_metrics.py and train_dl.py first.")
        sys.exit(1)
    return json.loads(p.read_text())

def badge(val, other, lower_is_better=True):
    if lower_is_better:
        if val < other: return "🟢"
        if val > other: return "🔴"
    else:
        if val > other: return "🟢"
        if val < other: return "🔴"
    return "🟡"

def sparkline_svg(values, color, width=200, height=60):
    if not values: return ""
    mn, mx = min(values), max(values)
    rng = mx - mn or 1
    pts = []
    for i, v in enumerate(values):
        x = i / max(len(values)-1, 1) * width
        y = height - (v - mn) / rng * (height - 4) - 2
        pts.append(f"{x:.1f},{y:.1f}")
    return f'<svg width="{width}" height="{height}" style="display:block"><polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2"/></svg>'

def scatter_svg(y_true, y_pred, color, size=220):
    if not y_true: return ""
    mn = min(min(y_true), min(y_pred)); mx = max(max(y_true), max(y_pred))
    rng = mx - mn or 1
    pad = 20
    inner = size - 2*pad
    def sc(v): return pad + (v - mn)/rng * inner
    circles = "".join(
        f'<circle cx="{sc(yt):.1f}" cy="{size - sc(yp):.1f}" r="3.5" fill="{color}" opacity="0.7"/>'
        for yt, yp in zip(y_true, y_pred)
    )
    diag = f'<line x1="{pad}" y1="{size-pad}" x2="{size-pad}" y2="{pad}" stroke="#888" stroke-dasharray="4" stroke-width="1.2"/>'
    axes = f'<line x1="{pad}" y1="{size-pad}" x2="{size-pad}" y2="{size-pad}" stroke="#aaa" stroke-width="1"/><line x1="{pad}" y1="{pad}" x2="{pad}" y2="{size-pad}" stroke="#aaa" stroke-width="1"/>'
    return f'<svg width="{size}" height="{size}">{axes}{diag}{circles}</svg>'

def residual_bars_svg(y_true, y_pred, color, width=220, height=80):
    residuals = [yp - yt for yt, yp in zip(y_true, y_pred)]
    mx = max(abs(r) for r in residuals) or 1
    mid = height // 2
    bw = max(2, width // len(residuals) - 1)
    bars = ""
    for i, r in enumerate(residuals):
        h = abs(r) / mx * (mid - 4)
        x = i * (bw + 1)
        y = mid - h if r > 0 else mid
        bars += f'<rect x="{x}" y="{y:.1f}" width="{bw}" height="{h:.1f}" fill="{color}" opacity="0.75"/>'
    baseline = f'<line x1="0" y1="{mid}" x2="{width}" y2="{mid}" stroke="#888" stroke-width="1"/>'
    return f'<svg width="{width}" height="{height}">{baseline}{bars}</svg>'

def fi_bars_svg(fi_dict, color, width=280, height=200):
    items = sorted(fi_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    if not items: return ""
    bar_h = 18
    gap = 4
    mx = items[0][1] or 1
    label_w = 130
    svgs = []
    for i, (name, val) in enumerate(items):
        bw = (val / mx) * (width - label_w - 10)
        y = i * (bar_h + gap)
        svgs.append(f'<text x="{label_w-4}" y="{y+13}" text-anchor="end" font-size="11" fill="#ccc">{name}</text>')
        svgs.append(f'<rect x="{label_w}" y="{y+2}" width="{bw:.1f}" height="{bar_h-4}" rx="3" fill="{color}" opacity="0.85"/>')
        svgs.append(f'<text x="{label_w + bw + 4}" y="{y+13}" font-size="10" fill="#aaa">{val:.3f}</text>')
    total_h = len(items) * (bar_h + gap)
    return f'<svg width="{width}" height="{total_h}">{"".join(svgs)}</svg>'

def main():
    rf = load(RF_METRICS)
    dl = load(DL_METRICS)
    OUT_PATH.parent.mkdir(exist_ok=True)

    rt, dt = rf["test"], dl["test"]
    rtr, dtr = rf["train"], dl["train"]

    # Verdict logic
    dl_wins = sum([
        dt["rmse"] < rt["rmse"],
        dt["r2"]   > rt["r2"],
        dt["mape"] < rt["mape"],
        dt["mae"]  < rt["mae"],
    ])
    winner = "Deep Learning (MLP)" if dl_wins >= 3 else "Random Forest"
    winner_color = "#7c3aed" if dl_wins >= 3 else "#059669"
    if dl_wins == 2:
        winner = "Tie / Context-Dependent"
        winner_color = "#d97706"

    reason = {
        "Random Forest": (
            "Random Forest performs better on this small structured tabular dataset (89 rows). "
            "Tree-based ensembles handle low data regimes without overfitting and require no feature scaling. "
            "<strong>Recommended for production.</strong>"
        ),
        "Deep Learning (MLP)": (
            "The MLP with Optuna tuning achieves superior generalisation, suggesting the neural network "
            "captures non-linear feature interactions not exploited by the forest. "
            "<strong>Recommended for production if dataset grows >500 rows.</strong>"
        ),
        "Tie / Context-Dependent": (
            "Both models perform similarly. Random Forest is simpler to deploy; "
            "choose DL if you plan to expand the dataset significantly."
        ),
    }[winner]

    # Training history sparkline
    dl_history  = dl.get("training_history", {})
    spark_loss  = sparkline_svg(dl_history.get("train_loss", []), "#7c3aed")
    spark_rmse  = sparkline_svg(dl_history.get("val_rmse",   []), "#06b6d4")

    # Scatter plots
    rf_scatter = scatter_svg(rf["test_y_true"], rf["test_y_pred"], "#059669")
    dl_scatter = scatter_svg(dl["test_y_true"], dl["test_y_pred"], "#7c3aed")

    # Residual bars
    rf_res = residual_bars_svg(rf["test_y_true"], rf["test_y_pred"], "#059669")
    dl_res = residual_bars_svg(dl["test_y_true"], dl["test_y_pred"], "#7c3aed")

    # Feature importance (RF only)
    fi_svg = fi_bars_svg(rf.get("feature_importances", {}), "#059669")

    # Best DL params
    bp = dl.get("best_params", {})
    lr_str = f"{bp['lr']:.2e}" if isinstance(bp.get('lr'), float) else str(bp.get('lr','?'))
    wd_str = f"{bp['wd']:.2e}" if isinstance(bp.get('wd'), float) else str(bp.get('wd','?'))
    ns_str = f"{bp['noise_std']:.4f}" if isinstance(bp.get('noise_std'), float) else str(bp.get('noise_std','?'))
    n_layers = bp.get("n_layers", "?")
    layers_str = " -&gt; ".join(str(bp.get(f"h{i}", "?")) for i in range(n_layers)) if isinstance(n_layers, int) else "?"

    def row(metric, rf_val, dl_val, lower_is_better=True):
        rb = badge(rf_val, dl_val, lower_is_better)
        db = badge(dl_val, rf_val, lower_is_better)
        return f"""
        <tr>
          <td>{metric}</td>
          <td class="rf">{rb} {rf_val:.4f}</td>
          <td class="dl">{db} {dl_val:.4f}</td>
          <td>{"Lower = better" if lower_is_better else "Higher = better"}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>KhetBuddy — Model Comparison Report</title>
<style>
  :root {{
    --bg:#0f172a; --card:#1e293b; --border:#334155;
    --rf:#059669; --dl:#7c3aed; --text:#e2e8f0; --muted:#94a3b8;
    --gold:#f59e0b;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;padding:24px;line-height:1.6}}
  h1{{font-size:2rem;font-weight:800;background:linear-gradient(135deg,var(--rf),var(--dl));-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px}}
  .subtitle{{color:var(--muted);margin-bottom:32px;font-size:.95rem}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}}
  .grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-bottom:24px}}
  .card{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:22px}}
  .card h2{{font-size:1rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:16px}}
  .card h3{{font-size:.85rem;font-weight:600;color:var(--muted);margin-bottom:8px}}
  .verdict{{border:2px solid {winner_color};background:rgba(0,0,0,.3)}}
  .verdict .tag{{display:inline-block;background:{winner_color};color:#fff;border-radius:999px;padding:2px 14px;font-size:.85rem;font-weight:700;margin-bottom:10px}}
  .winner{{font-size:1.6rem;font-weight:800;color:{winner_color};margin-bottom:8px}}
  table{{width:100%;border-collapse:collapse;font-size:.9rem}}
  th{{padding:10px 12px;text-align:left;background:#0f172a;color:var(--muted);font-weight:600;font-size:.8rem;text-transform:uppercase;letter-spacing:.06em}}
  td{{padding:10px 12px;border-top:1px solid var(--border)}}
  td.rf{{color:var(--rf);font-weight:600}}
  td.dl{{color:var(--dl);font-weight:600}}
  tr:hover td{{background:rgba(255,255,255,.03)}}
  .chip{{display:inline-block;border-radius:6px;padding:2px 10px;font-size:.8rem;font-weight:600;margin:2px}}
  .chip-rf{{background:rgba(5,150,105,.2);color:var(--rf)}}
  .chip-dl{{background:rgba(124,58,237,.2);color:var(--dl)}}
  .metric-big{{font-size:2.2rem;font-weight:800;line-height:1}}
  .metric-label{{font-size:.75rem;color:var(--muted);margin-top:4px}}
  .param-table td{{font-size:.82rem;color:var(--muted)}}
  .param-table td:first-child{{color:var(--text);font-weight:500}}
  .section-label{{font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}}
  .note{{background:rgba(245,158,11,.08);border-left:3px solid var(--gold);padding:12px 16px;border-radius:0 8px 8px 0;font-size:.85rem;color:#fcd34d;margin-top:16px}}
  footer{{text-align:center;color:var(--muted);font-size:.78rem;margin-top:40px;padding-top:16px;border-top:1px solid var(--border)}}
</style>
</head>
<body>

<h1>🌾 KhetBuddy Model Comparison Report</h1>
<p class="subtitle">Random Forest (sklearn) vs Deep Learning MLP (PyTorch + Optuna) — Crop Yield Prediction • Punjab</p>

<!-- VERDICT -->
<div class="card verdict" style="margin-bottom:24px">
  <span class="tag">⚖️ VERDICT</span>
  <div class="winner">🏆 {winner}</div>
  <p style="color:var(--muted);font-size:.92rem">{reason}</p>
</div>

<!-- KEY METRICS GRID -->
<div class="grid3" style="margin-bottom:24px">
  <div class="card" style="text-align:center">
    <div class="section-label">Test RMSE (quintal/ha)</div>
    <div style="display:flex;justify-content:space-around;align-items:flex-end;margin-top:12px">
      <div><div class="metric-big" style="color:var(--rf)">{rt['rmse']:.3f}</div><div class="metric-label chip chip-rf">Random Forest</div></div>
      <div><div class="metric-big" style="color:var(--dl)">{dt['rmse']:.3f}</div><div class="metric-label chip chip-dl">Deep Learning</div></div>
    </div>
  </div>
  <div class="card" style="text-align:center">
    <div class="section-label">Test R² Score</div>
    <div style="display:flex;justify-content:space-around;align-items:flex-end;margin-top:12px">
      <div><div class="metric-big" style="color:var(--rf)">{rt['r2']:.4f}</div><div class="metric-label chip chip-rf">Random Forest</div></div>
      <div><div class="metric-big" style="color:var(--dl)">{dt['r2']:.4f}</div><div class="metric-label chip chip-dl">Deep Learning</div></div>
    </div>
  </div>
  <div class="card" style="text-align:center">
    <div class="section-label">Test MAPE (%)</div>
    <div style="display:flex;justify-content:space-around;align-items:flex-end;margin-top:12px">
      <div><div class="metric-big" style="color:var(--rf)">{rt['mape']:.2f}</div><div class="metric-label chip chip-rf">Random Forest</div></div>
      <div><div class="metric-big" style="color:var(--dl)">{dt['mape']:.2f}</div><div class="metric-label chip chip-dl">Deep Learning</div></div>
    </div>
  </div>
</div>

<!-- FULL METRICS TABLE -->
<div class="card" style="margin-bottom:24px">
  <h2>📊 Full Metrics Comparison</h2>
  <table>
    <tr><th>Metric</th><th>🌲 Random Forest</th><th>🧠 Deep Learning</th><th>Note</th></tr>
    {row("RMSE — Test (quintal/ha)", rt['rmse'], dt['rmse'])}
    {row("RMSE — Train (quintal/ha)", rtr['rmse'], dtr['rmse'])}
    {row("R² — Test", rt['r2'], dt['r2'], lower_is_better=False)}
    {row("R² — Train", rtr['r2'], dtr['r2'], lower_is_better=False)}
    {row("MAE — Test (quintal/ha)", rt['mae'], dt['mae'])}
    {row("MAPE — Test (%)", rt['mape'], dt['mape'])}
    <tr><td>Training Time</td><td class="rf">~seconds (RF fit)</td><td class="dl">{dl.get('training_time_sec','?')}s (incl. Optuna)</td><td>DL includes HPO</td></tr>
    <tr><td>Model Size</td><td class="rf">~2.5 MB (.pkl)</td><td class="dl">~50–200 KB (.pt)</td><td>DL smaller on disk</td></tr>
    <tr><td>Feature Scaling Required</td><td class="rf">No ✅</td><td class="dl">Yes (StandardScaler)</td><td>RF more robust</td></tr>
    <tr><td>Interpretability</td><td class="rf">Feature importance ✅</td><td class="dl">Black-box (limited)</td><td>RF wins</td></tr>
    <tr><td>Scalability (more data)</td><td class="rf">Moderate</td><td class="dl">Excellent ✅</td><td>DL wins</td></tr>
  </table>
  <div class="note">🟢 = wins on this metric&nbsp;&nbsp;🔴 = loses&nbsp;&nbsp;🟡 = tie</div>
</div>

<!-- SCATTER PLOTS -->
<div class="grid2">
  <div class="card">
    <h2>🌲 RF: Predicted vs Actual</h2>
    <p class="section-label">Each dot = one test sample. Diagonal = perfect predictions.</p>
    <div style="margin-top:12px">{rf_scatter}</div>
    <p style="font-size:.78rem;color:var(--muted);margin-top:8px">X = Actual yield &nbsp;|&nbsp; Y = Predicted yield (quintal/ha)</p>
  </div>
  <div class="card">
    <h2>🧠 DL: Predicted vs Actual</h2>
    <p class="section-label">Each dot = one test sample. Diagonal = perfect predictions.</p>
    <div style="margin-top:12px">{dl_scatter}</div>
    <p style="font-size:.78rem;color:var(--muted);margin-top:8px">X = Actual yield &nbsp;|&nbsp; Y = Predicted yield (quintal/ha)</p>
  </div>
</div>

<!-- RESIDUALS -->
<div class="grid2">
  <div class="card">
    <h2>🌲 RF: Residuals</h2>
    <p class="section-label">Each bar = prediction error (positive = overestimate)</p>
    <div style="margin-top:12px">{rf_res}</div>
  </div>
  <div class="card">
    <h2>🧠 DL: Residuals</h2>
    <p class="section-label">Each bar = prediction error (positive = overestimate)</p>
    <div style="margin-top:12px">{dl_res}</div>
  </div>
</div>

<!-- DL TRAINING HISTORY + BEST PARAMS -->
<div class="grid2" style="margin-top:20px">
  <div class="card">
    <h2>🧠 DL Training History</h2>
    <h3>Training Loss (HuberLoss)</h3>
    {spark_loss}
    <h3 style="margin-top:16px">Validation RMSE</h3>
    {spark_rmse}
    <p style="font-size:.78rem;color:var(--muted);margin-top:8px">Purple = loss &nbsp;|&nbsp; Cyan = val RMSE — both should decrease</p>
  </div>
  <div class="card">
    <h2>⚙️ Best Optuna Hyperparameters</h2>
    <table class="param-table">
      <tr><td>Architecture</td><td style="color:var(--dl)">Input(15) → {layers_str} → 1</td></tr>
      <tr><td>Layers</td><td>{n_layers}</td></tr>
      <tr><td>Learning Rate</td><td>{lr_str}</td></tr>
      <tr><td>Weight Decay</td><td>{wd_str}</td></tr>
      <tr><td>Batch Size</td><td>{bp.get('batch_size','?')}</td></tr>
      <tr><td>Noise Std (augmentation)</td><td>{ns_str}</td></tr>
      <tr><td>Optuna Trials</td><td>40</td></tr>
      <tr><td>K-Folds</td><td>5</td></tr>
      <tr><td>Augmentation Factor</td><td>8× (Gaussian noise)</td></tr>
      <tr><td>Activation</td><td>GELU</td></tr>
      <tr><td>LR Schedule</td><td>CosineAnnealingLR</td></tr>
      <tr><td>Loss Function</td><td>HuberLoss (δ=1.0)</td></tr>
    </table>
  </div>
</div>

<!-- FEATURE IMPORTANCE (RF) -->
<div class="card" style="margin-top:20px">
  <h2>🌲 RF Feature Importances (Top 10)</h2>
  <p class="section-label">Higher = more influence on prediction. DL does not expose per-feature importance natively.</p>
  <div style="margin-top:14px">{fi_svg}</div>
</div>

<!-- WHEN TO USE WHICH -->
<div class="grid2" style="margin-top:20px">
  <div class="card">
    <h2 style="color:var(--rf)">🌲 Choose Random Forest when…</h2>
    <ul style="padding-left:18px;color:var(--muted);font-size:.88rem;line-height:2">
      <li>Dataset is small (&lt;500 rows) — RF handles this gracefully</li>
      <li>You need <strong>explainability</strong> (feature importances)</li>
      <li>No GPU or PyTorch available</li>
      <li>Fast inference without scaling overhead</li>
      <li>Robustness to outliers and noisy labels</li>
      <li>Production simplicity (single .pkl file)</li>
    </ul>
  </div>
  <div class="card">
    <h2 style="color:var(--dl)">🧠 Choose Deep Learning when…</h2>
    <ul style="padding-left:18px;color:var(--muted);font-size:.88rem;line-height:2">
      <li>Dataset grows beyond 500–1000 rows</li>
      <li>Complex non-linear feature interactions exist</li>
      <li>You want a smaller model file on disk</li>
      <li>Future plans: add image/satellite features (CNN branch)</li>
      <li>Need uncertainty estimation (MC-Dropout)</li>
      <li>Ensemble with RF for maximum accuracy</li>
    </ul>
  </div>
</div>

<!-- DATASET NOTE -->
<div class="card" style="margin-top:20px">
  <h2>⚠️ Dataset Size Advisory</h2>
  <p style="color:var(--muted);font-size:.9rem">
    This comparison is based on <strong>89 structured rows</strong> — a deterministic, district-aggregated dataset.
    Deep Learning models typically require 500–10,000+ rows to surpass tree-based methods on tabular data.
    The DL pipeline compensates with <strong>8× Gaussian noise augmentation</strong>, k-fold CV, BatchNorm, and Dropout,
    but the fundamental data constraint remains.
    <br><br>
    <strong>Recommendation:</strong> Use Random Forest for current production deployment.
    Re-benchmark once the dataset is enriched with historical APY data (&gt;500 rows) — at that scale, DL typically overtakes RF.
  </p>
</div>

<footer>Generated by KhetBuddy Model Comparison Tool • RF vs PyTorch MLP (Optuna HPO) • Punjab Crop Yield Prediction</footer>
</body>
</html>"""

    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"\n✅ Report generated → {OUT_PATH}")
    print(f"   Open in browser: {OUT_PATH.resolve()}")
    print(f"\n  Winner: {winner}")
    print(f"  RF  Test RMSE={rt['rmse']:.4f}  R²={rt['r2']:.4f}  MAPE={rt['mape']:.2f}%")
    print(f"  DL  Test RMSE={dt['rmse']:.4f}  R²={dt['r2']:.4f}  MAPE={dt['mape']:.2f}%")

if __name__ == "__main__":
    main()
