import pandas as pd
import xgboost as xgb
import argparse
import json
import sys
import traceback

def main():
    # === Setup Argument Parser === #
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
        print(json.dumps({"error": f"Argument parsing failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Load Trained Model === #
    try:
        model = xgb.Booster()
        model.load_model("xgboost_waterwise.model")
    except Exception as e:
        print(json.dumps({"error": f"Failed to load model: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Prepare Input Data === #
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

    # === Predict === #
    try:
        # Select only the columns that the model was trained on
        model_features = ['pH', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen', 'salinity', 'total_dissolved_solids', 'hardness', 'alkalinity', 'chlorine']
        input_data_for_model = input_data[model_features]

        # Create DMatrix for prediction using the selected features
        dmatrix_input = xgb.DMatrix(input_data_for_model, feature_names=model_features)

    except Exception as e:
        print(json.dumps({"error": f"Failed to create DMatrix: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    try:
        prediction = model.predict(dmatrix_input)[0]
        label = "Safe" if prediction == 1 else "Unsafe"
    except Exception as e:
        print(json.dumps({"error": f"Prediction failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Rule-Based Checks (WHO Guidelines) === #
    # Check if any of the critical parameters violate the safe limits based on rules
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
        # If any of the rules indicate unsafe water, set the label to Unsafe.
        # Otherwise, the label is determined by the model prediction.
        if is_unsafe_by_rules:
             label = "Unsafe"

    except Exception as e:
        print(json.dumps({"error": f"Rule-based checks failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Recommendations === #
    def generate_recommendations(data):
        messages = []

        if data["pH"] < 6.5:
            messages.append(
                f"pH ({data['pH']}) is too low. Acidic water can corrode pipes and leach metals. "
                "Add alkaline substances such as soda ash (sodium carbonate) or lime to raise pH."
            )
        elif data["pH"] > 8.5:
            messages.append(
                f"pH ({data['pH']}) is too high. Alkaline water can cause scale buildup and reduce disinfection efficiency. "
                "Add acidic agents like citric acid or carbon dioxide to lower pH."
            )

        if data["turbidity"] > 5:
            messages.append(
                f"Turbidity ({data['turbidity']} NTU) is high. Cloudy water may contain pathogens or sediments. "
                "Use coagulation-flocculation followed by sand filtration or membrane filtration."
            )

        if data["temperature"] > 30: # Added recommendation for high temperature
             messages.append(
                 f"Temperature ({data['temperature']} °C) is high. Elevated temperature can decrease dissolved oxygen levels and promote microbial growth. "
                 "Consider aeration or cooling methods, and monitor dissolved oxygen and microbial parameters."
             )

        if data["chlorine"] > 4:
            messages.append(
                f"Chlorine ({data['chlorine']} mg/L) exceeds safe levels. Can cause taste issues and health risks. "
                "Consider activated carbon filters or dechlorination with ascorbic acid or sodium thiosulfate."
            )

        if data["total_dissolved_solids"] > 500:
            messages.append(
                f"TDS ({data['total_dissolved_solids']} mg/L) is high. Indicates excess minerals or pollutants. "
                "Reverse osmosis, distillation, or deionization systems are effective treatment methods."
            )

        if data["conductivity"] > 1000:
            messages.append(
                f"Conductivity ({data['conductivity']} µS/cm) is high. May indicate excessive salts or contamination. "
                "Test for specific ions (e.g., nitrates, sulfates) and consider ion exchange or reverse osmosis."
            )

        if data["dissolved_oxygen"] < 5:
            messages.append(
                f"Dissolved Oxygen ({data['dissolved_oxygen']} mg/L) is low. This can stress aquatic life. "
                "Introduce aeration methods like fountains, diffused aerators, or surface agitators."
            )

        if data["salinity"] > 0.5:
            messages.append(
                f"Salinity ({data['salinity']} ppt) is high. May indicate saltwater intrusion or industrial discharge. "
                "Monitor sources and use desalination techniques such as reverse osmosis."
            )

        if data["hardness"] > 150:
            messages.append(
                f"Hardness ({data['hardness']} mg/L) is high. May cause scale in pipes and reduce soap effectiveness. "
                "Water softeners using ion-exchange resins are recommended."
            )

        if data["alkalinity"] < 20:
            messages.append(
                f"Alkalinity ({data['alkalinity']} mg/L) is too low. Poor buffering makes pH unstable. "
                "Add sodium bicarbonate or lime to increase alkalinity and stabilize pH."
            )
        elif data["alkalinity"] > 200:
            messages.append(
                f"Alkalinity ({data['alkalinity']} mg/L) is high. May interfere with disinfection. "
                "Dilution or acidic dosing (like sulfuric acid) can help reduce alkalinity."
            )

        if data["total_coliforms"] > 0:
             messages.append(
                 f"Total Coliforms ({data['total_coliforms']} MPN/100mL) detected. Indicates potential fecal contamination. "
                 "Requires immediate disinfection (e.g., chlorination) and investigation of the source."
             )

        if data["e_coli"] > 0:
             messages.append(
                 f"E. coli ({data['e_coli']} MPN/100mL) detected. Confirms fecal contamination and serious health risk. "
                 "Water is unsafe to drink without treatment. Boil water or use strong disinfection and identify/eliminate contamination source."
             )

        return messages

    try:
        recommendations = generate_recommendations(data)
        # Add a general recommendation if the label is "Unsafe" and no specific recommendations were added.
        # This general recommendation might be redundant now with more specific rules, but keeping it as a fallback.
        if label == "Unsafe" and not recommendations:
            recommendations.append(
                "Overall prediction is Unsafe. While individual parameters appear within typical ranges, the model indicates potential issues. Consider further testing or professional assessment before use."
            )
    except Exception as e:
        print(json.dumps({"error": f"Recommendation generation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Output === #
    try:
        output = {"status": label, "recommendations": recommendations, "input_data": data}
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(json.dumps({"error": f"Output generation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)