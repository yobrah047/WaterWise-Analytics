import pandas as pd
import xgboost as xgb

# === Load Trained Model ===
model = xgb.XGBClassifier()
model.load_model("xgboost_waterwise.model")  # Replace with your trained model path

# === Input from Chiromo ===
data = {
    'pH': 4,
    'turbidity': 5,
    'temperature': 15,
    'conductivity': 32,
    'dissolved_oxygen': 143,
    'salinity': 54,
    'total_dissolved_solids': 13,
    'hardness': 434,
    'alkalinity': 435,
    'chlorine': 35,
    'total_coliforms': 432,
    'e_coli': 343
}

input_data = pd.DataFrame([data])

# === Predict Water Safety ===
prediction = model.predict(input_data)[0]
label = "Safe" if prediction == 1 else "Unsafe"

# === Generate Recommendations ===
def generate_recommendations(data):
    messages = []
    if data['pH'] < 6.5:
        messages.append("Low pH detected. Neutralize with a base like lime.")
    if data['turbidity'] > 5:
        messages.append("Turbidity is high. Filter water before use.")
    if data['conductivity'] < 50:
        messages.append("Very low conductivity. Check for calibration errors.")
    if data['dissolved_oxygen'] > 12:
        messages.append("Dissolved Oxygen unusually high. Recheck measurement.")
    if data['chlorine'] > 4:
        messages.append("Chlorine levels too high. Reduce chlorination.")
    if data['total_coliforms'] > 0 or data['e_coli'] > 0:
        messages.append("Microbial contamination detected! Boil or treat the water.")
    return messages

# === Display Output ===
print("Water Status:", label)
print("\nRecommendations:")
for rec in generate_recommendations(data):
    print("-", rec)
