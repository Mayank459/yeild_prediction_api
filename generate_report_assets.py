import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import os

# Create plots directory if not exists
os.makedirs("plots", exist_ok=True)

# 1. Load the complete training dataset
csv_path = r"d:\API\khetBuddy\datasets\05_complete_training_dataset.csv"
df = pd.read_csv(csv_path)

# 2. Features for training
feature_columns = [
    "nitrogen", "phosphorus", "potassium", "soil_ph", "soil_moisture",
    "avg_temperature", "total_rainfall", "humidity",
    "nutrient_index", "temperature_deviation", "stress_indicator",
    "crop_enc", "season_enc", "district_enc", "irrigation_enc"
]

X = df[feature_columns]
y = df["yield_qtl_ha"]

# 3. Train Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Train Model
model = RandomForestRegressor(
    n_estimators=100, 
    random_state=42,
    min_samples_split=2
)
model.fit(X_train, y_train)

# 5. Evaluate Model
y_pred = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)
mape = np.mean(np.abs((y_test - y_pred) / np.maximum(y_test, 1))) * 100

print("=== REAL EVALUATION NUMBERS ===")
print(f"RMSE: {rmse:.2f} quintal/ha")
print(f"R² Score: {r2:.4f}")
print(f"MAPE: {mape:.2f}%")
print("===============================\n")

# 6. Generate Feature Importance Plot
importances = model.feature_importances_
importance_df = pd.DataFrame({"Feature": feature_columns, "Importance": importances})
importance_df = importance_df.sort_values(by="Importance", ascending=False)

plt.figure(figsize=(10, 6))
sns.barplot(x="Importance", y="Feature", data=importance_df, palette="viridis", hue="Feature", legend=False)
plt.title("Random Forest Feature Importance for Yield Prediction")
plt.xlabel("Importance Score")
plt.ylabel("Feature")
plt.tight_layout()
plt.savefig(r"d:\API\khetBuddy\plots\feature_importance.png", dpi=300)
plt.close()

# 7. Generate Correlation Heatmap
# Select only numeric columns suitable for correlation
corr_features = [
    "nitrogen", "phosphorus", "potassium", "soil_ph", "soil_moisture",
    "avg_temperature", "total_rainfall", "humidity", "yield_qtl_ha"
]
corr_df = df[corr_features].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_df, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
plt.title("Environmental Factors vs Crop Yield Correlation Matrix")
plt.tight_layout()
plt.savefig(r"d:\API\khetBuddy\plots\correlation_heatmap.png", dpi=300)
plt.close()

print("Plots saved successfully to:")
print(r"1. d:\API\khetBuddy\plots\feature_importance.png")
print(r"2. d:\API\khetBuddy\plots\correlation_heatmap.png")
