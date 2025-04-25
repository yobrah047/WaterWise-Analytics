import pandas as pd
import xgboost as xgb
import argparse
import json

# === Setup Argument Parser ===
parser = argparse.ArgumentParser(description='Predict water safety based on input parameters.')
parser.add_argument('--pH', type=float, required=True)
parser.add_argument('--turbidity', type=float, required=True)
parser.add_argument('--temperature', type=float, required=True)
parser.add_argument('--conductivity', type=float, required=True)
parser.add_argument('--dissolved_oxygen', type=float, required=True)
parser.add_argument('--salinity', type=float, required=True)
parser.add_argument('--total_dissolved_solids', type=float, required=True)
parser.add_argument('--hardness', type=float, required=True)
parser.add_argument('--alkalinity', type=float, required=True)
parser.add_argument('--chlorine', type=float, required=True)
parser.add_argument('--total_coliforms', type=float, required=True)
parser.add_argument('--e_coli', type=float, required=True)

args = parser.parse_args()

# === Load Trained Model ===
try:
    model = xgb.Booster()
    model.load_model("xgboost_waterwise.model")  
except Exception as e:

    print(json.dumps({"error": f"Failed to load model: {e}"}))
    exit(1)

#Correct Order
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

# === Predict ===
try:
    dmatrix_input = xgb.DMatrix(input_data, feature_names=input_data.columns)
except Exception as e:
    print(json.dumps({"error": f"Failed to create DMatrix: {e}"}))
    exit(1)
try:
    prediction = model.predict(dmatrix_input)[0]
    label = "Safe" if prediction == 1 else "Unsafe"
except Exception as e:
    print(json.dumps({"error": f"Prediction failed: {e}"}))
    exit(1)

# === Recommendations ===
def generate_recommendations(data):
    messages = []
    if data['pH'] < 6.5 or data['pH'] > 8.5:
        messages.append(f"pH ({data['pH']}) is outside safe range (6.5-8.5).")
    if data['turbidity'] > 5:
        messages.append(f"Turbidity ({data['turbidity']}) is high (> 5 NTU).")
    if data['chlorine'] > 4:
        messages.append(f"Chlorine level ({data['chlorine']}) is high (> 4 mg/L).")
    if data['total_coliforms'] > 0 or data['e_coli'] > 0:
        messages.append(f"Microbial contamination detected (Coliforms: {data['total_coliforms']}, E.coli: {data['e_coli']})!")
    return messages

recommendations = generate_recommendations(data)

# === Output ===
output = {
    "status": label,
    "recommendations": recommendations,
    "input_data": data
}
print(json.dumps(output, indent=2))

 