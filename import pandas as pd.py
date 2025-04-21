default_api.write_file(
    path='predict_water_safety.py',
    content='''import pandas as pd
import xgboost as xgb
import argparse
import json

# === Setup Argument Parser ===
parser = argparse.ArgumentParser(description='Predict water safety based on input parameters.')
parser.add_argument('--pH', type=float, required=True, help='pH level')
parser.add_argument('--turbidity', type=float, required=True, help='Turbidity level')
parser.add_argument('--temperature', type=float, required=True, help='Temperature in Celsius')
parser.add_argument('--conductivity', type=float, required=True, help='Conductivity level')
parser.add_argument('--dissolved_oxygen', type=float, required=True, help='Dissolved Oxygen level')
parser.add_argument('--salinity', type=float, required=True, help='Salinity level')
parser.add_argument('--total_dissolved_solids', type=float, required=True, help='Total Dissolved Solids')
parser.add_argument('--hardness', type=float, required=True, help='Hardness level')
parser.add_argument('--alkalinity', type=float, required=True, help='Alkalinity level')
parser.add_argument('--chlorine', type=float, required=True, help='Chlorine level')
parser.add_argument('--total_coliforms', type=float, required=True, help='Total Coliforms count')
parser.add_argument('--e_coli', type=float, required=True, help='E. coli count')

args = parser.parse_args()

# === Load Trained Model ===
try:
    model = xgb.XGBClassifier()
    model.load_model("xgboost_waterwise.model")
except Exception as e:
    print(json.dumps({"error": f"Failed to load model: {e}"}))
    exit(1)

# === Prepare Input Data ===
data = {
    'pH': args.pH,
    'turbidity': args.turbidity,
    'temperature': args.temperature,
    'conductivity': args.conductivity,
    'dissolved_oxygen': args.dissolved_oxygen,
    'salinity': args.salinity,
    'total_dissolved_solids': args.total_dissolved_solids,
    'hardness': args.hardness,
    'alkalinity': args.alkalinity,
    'chlorine': args.chlorine,
    'total_coliforms': args.total_coliforms,
    'e_coli': args.e_coli
}
input_data = pd.DataFrame([data])

# === Predict Water Safety ===
try:
    prediction = model.predict(input_data)[0]
    label = "Safe" if prediction == 1 else "Unsafe"
except Exception as e:
    print(json.dumps({"error": f"Prediction failed: {e}"}))
    exit(1)

# === Generate Recommendations ===
def generate_recommendations(data):
    messages = []
    if data['pH'] < 6.5 or data['pH'] > 8.5:
        messages.append(f"pH ({data['pH']}) is outside the typical safe range (6.5-8.5). Adjustment may be needed.")
    if data['turbidity'] > 5:
        messages.append(f"Turbidity ({data['turbidity']}) is high (> 5 NTU). Consider filtration.")
    if data['chlorine'] > 4:
        messages.append(f"Chlorine level ({data['chlorine']}) is high (> 4 mg/L). Check disinfection process.")
    if data['total_coliforms'] > 0 or data['e_coli'] > 0:
        messages.append(f"Microbial contamination detected (Coliforms: {data['total_coliforms']}, E.coli: {data['e_coli']})! Water is unsafe for drinking without treatment.")
    return messages

recommendations = generate_recommendations(data)

# === Output Results as JSON ===
output = {
    "status": label,
    "recommendations": recommendations,
    "input_data": data
}
print(json.dumps(output))
'''
)
