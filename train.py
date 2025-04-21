import pandas as pd
from sklearn.model_selection import train_test_split
import xgboost as xgb
import joblib

# === Load dataset ===
df = pd.read_excel("full_waterwise_dataset.xlsx")

# === Rename and clean column names ===
df = df.rename(columns={
    "ph level ": "pH",
    "turbidity": "turbidity",
    "tempreture": "temperature",
    "electrcal conductivity": "conductivity",
    "Dissolved oxygen": "dissolved_oxygen",
    "salinity": "salinity",
    "Total dissolved solids": "total_dissolved_solids",
    "Hardness": "hardness",
    "Alkalinity": "alkalinity",
    "chlorine": "chlorine",
    "total coliforms": "total_coliforms",
    "E.coli": "e_coli",
    "location ": "location",
    "Water source": "water_source",
    "Date": "date",
    "Additional notes ": "notes"
})

# === Drop unused columns ===
df = df.drop(columns=["location", "water_source", "date", "notes"], errors="ignore")

# === Handle missing values ===
df = df.dropna()

# === Add 'label' column: 1 = Safe, 0 = Unsafe ===
df["label"] = df.apply(lambda row: 1 if row["e_coli"] == 0 and row["total_coliforms"] == 0 else 0, axis=1)

# === Split features and target ===
X = df.drop(columns=["label"])
y = df["label"]

# === Train/test split ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === Train model ===
model = xgb.XGBClassifier()
model.fit(X_train, y_train)

# === Save model ===
model.save_model("xgboost_waterwise.model")
joblib.dump(model, "xgboost_waterwise.joblib")

print("✅ Model trained and saved successfully with clean column names!")
