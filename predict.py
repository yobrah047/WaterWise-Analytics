import pandas as pd
import xgboost as xgb
import argparse
import json
import sys
import traceback

def main():
    # === 1. Setup Argument Parser === #
    # This section defines the expected input parameters (water quality features) 
    # that the user provides when running the script from the command line.
    try:
        parser = argparse.ArgumentParser(description="Predict water safety based on input parameters.")
        parser.add_argument("--pH", type=float, required=True)
        parser.add_argument("--turbidity", type=float, required=True)
        parser.add_argument("--temperature", type=float, required=True)
        parser.add_argument("--conductivity", type=float, required=True)
        parser.add_argument("--dissolved_oxygen", type=float, required=True)
        parser.add_argument("--salinity", type=float, required=True)
        parser.add_argument("--total_dissolved_solids", type=float, required=True)
        parser.add_argument("--hardness", type=float, required=True)
        parser.add_argument("--alkalinity", type=float, required=True)
        parser.add_argument("--chlorine", type=float, required=True)
        parser.add_argument("--total_coliforms", type=float, required=True)
        parser.add_argument("--e_coli", type=float, required=True)
        args = parser.parse_args()
    except Exception as e:
        # If argument parsing fails, return an error in JSON format
        print(json.dumps({"error": f"Argument parsing failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === 2. Load Trained XGBoost Model === #
    # Loads the pre-trained model from a saved file ("xgboost_waterwise.model").
    try:
        model = xgb.Booster()
        model.load_model("xgboost_waterwise.model")
    except Exception as e:
        print(json.dumps({"error": f"Failed to load model: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === 3. Prepare Input Data === #
    # Collects the input parameters into a dictionary and then converts them into a pandas DataFrame.
    try:
        data = {
            "pH": args.pH,
            "turbidity": args.turbidity,
            "temperature": args.temperature,
            "conductivity": args.conductivity,
            "dissolved_oxygen": args.dissolved_oxygen,
            "salinity": args.salinity,
            "total_dissolved_solids": args.total_dissolved_solids,
            "hardness": args.hardness,
            "alkalinity": args.alkalinity,
            "chlorine": args.chlorine,
            "total_coliforms": args.total_coliforms,
            "e_coli": args.e_coli,
        }
        input_data = pd.DataFrame([data])
    except Exception as e:
        print(json.dumps({"error": f"Input data preparation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === 4. Select Model Features & Create DMatrix === #
    # The model was trained on specific features only.
    # Here we select those features and convert them into an XGBoost DMatrix for prediction.
    try:
        model_features = ['pH', 'turbidity', 'temperature', 'conductivity',
                          'dissolved_oxygen', 'salinity', 'total_dissolved_solids',
                          'hardness', 'alkalinity', 'chlorine']
        input_data_for_model = input_data[model_features]
        dmatrix_input = xgb.DMatrix(input_data_for_model, feature_names=model_features)
    except Exception as e:
        print(json.dumps({"error": f"Failed to create DMatrix: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === 5. Model Prediction === #
    # The model outputs a prediction (1 = Safe, 0 = Unsafe).
    try:
        prediction = model.predict(dmatrix_input)[0]
        label = "Safe" if prediction == 1 else "Unsafe"
    except Exception as e:
        print(json.dumps({"error": f"Prediction failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === 6. Rule-Based Checks (WHO Guidelines) === #
    # Independent validation of safety using WHO limits.
    # If any critical parameter violates safe thresholds, the label is set to "Unsafe".
    is_unsafe_by_rules = False
    if args.pH < 6.5 or args.pH > 8.5:
        is_unsafe_by_rules = True
    if args.turbidity > 5:
        is_unsafe_by_rules = True
    if args.chlorine > 5:
        is_unsafe_by_rules = True
    if args.total_coliforms > 0:
        is_unsafe_by_rules = True
    if args.e_coli > 0:
        is_unsafe_by_rules = True

    try:
        if is_unsafe_by_rules:
            label = "Unsafe"
        else:
            label = "Safe"
    except Exception as e:
        print(json.dumps({"error": f"Rule-based checks failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === 7. Generate Treatment Recommendations === #
    # This function gives human-readable recommendations if parameters are out of safe ranges.
    def generate_recommendations(data):
        messages = []

        # pH recommendations
        if data["pH"] < 6.5:
            messages.append(
                f"pH ({data['pH']}) is too low. Acidic water can corrode pipes and leach metals. "
                "Add soda ash or lime to raise pH."
            )
        elif data["pH"] > 8.5:
            messages.append(
                f"pH ({data['pH']}) is too high. Alkaline water can cause scaling and reduce disinfection. "
                "Add citric acid or carbon dioxide to lower pH."
            )

        # Turbidity recommendations
        if data["turbidity"] > 5:
            messages.append(
                f"Turbidity ({data['turbidity']} NTU) is high. Cloudy water may contain pathogens. "
                "Use coagulation-flocculation and filtration."
            )

        # Temperature recommendations
        if data["temperature"] > 30:
            messages.append(
                f"Temperature ({data['temperature']} °C) is high. Promotes microbial growth. "
                "Consider aeration/cooling and monitor oxygen levels."
            )

        # Chlorine recommendations
        if data["chlorine"] > 4:
            messages.append(
                f"Chlorine ({data['chlorine']} mg/L) exceeds safe levels. May cause taste/health issues. "
                "Use activated carbon filters or dechlorination."
            )

        # TDS recommendations
        if data["total_dissolved_solids"] > 500:
            messages.append(
                f"TDS ({data['total_dissolved_solids']} mg/L) is high. Indicates excess minerals/pollutants. "
                "Use reverse osmosis or distillation."
            )

        # Conductivity recommendations
        if data["conductivity"] > 1000:
            messages.append(
                f"Conductivity ({data['conductivity']} µS/cm) is high. May indicate salts/contamination. "
                "Test for ions and use ion exchange or RO."
            )

        # Dissolved oxygen recommendations
        if data["dissolved_oxygen"] < 5:
            messages.append(
                f"Dissolved Oxygen ({data['dissolved_oxygen']} mg/L) is low. Stresses aquatic life. "
                "Use aeration methods."
            )

        # Salinity recommendations
        if data["salinity"] > 0.5:
            messages.append(
                f"Salinity ({data['salinity']} ppt) is high. Possible saltwater intrusion. "
                "Use desalination (RO)."
            )

        # Hardness recommendations
        if data["hardness"] > 150:
            messages.append(
                f"Hardness ({data['hardness']} mg/L) is high. Causes scaling and reduces soap effectiveness. "
                "Use water softeners (ion exchange)."
            )

        # Alkalinity recommendations
        if data["alkalinity"] < 20:
            messages.append(
                f"Alkalinity ({data['alkalinity']} mg/L) is too low. pH unstable. "
                "Add sodium bicarbonate or lime."
            )
        elif data["alkalinity"] > 200:
            messages.append(
                f"Alkalinity ({data['alkalinity']} mg/L) is too high. May interfere with disinfection. "
                "Use dilution or mild acids."
            )

        # Microbial recommendations
        if data["total_coliforms"] > 0:
            messages.append(
                f"Total Coliforms ({data['total_coliforms']}) detected. Indicates contamination. "
                "Immediate disinfection (e.g., chlorination) required."
            )

        if data["e_coli"] > 0:
            messages.append(
                f"E. coli ({data['e_coli']}) detected. Confirms fecal contamination. "
                "Boil water, disinfect strongly, and find contamination source."
            )

        return messages

    try:
        recommendations = generate_recommendations(data)
        # Add fallback recommendation if unsafe but no specific advice was generated
        if label == "Unsafe" and not recommendations:
            recommendations.append(
                "Water predicted as Unsafe. Further testing recommended before use."
            )
    except Exception as e:
        print(json.dumps({"error": f"Recommendation generation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === 8. Final Output === #
    # The script prints the result in JSON format, including:
    # - Water safety status (Safe/Unsafe)
    # - Recommendations (if any)
    # - Input data used for prediction
    try:
        output = {"status": label, "recommendations": recommendations, "input_data": data}
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(json.dumps({"error": f"Output generation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

# Entry point of the script
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)
