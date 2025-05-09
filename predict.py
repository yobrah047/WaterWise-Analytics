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
        }
        input_data = pd.DataFrame([data])
    except Exception as e:
        print(json.dumps({"error": f"Input data preparation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Predict === #
    try:
        dmatrix_input = xgb.DMatrix(input_data, feature_names=list(input_data.columns))
    except Exception as e:
        print(json.dumps({"error": f"Failed to create DMatrix: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    try:
        prediction = model.predict(dmatrix_input)[0]
        label = "Safe" if prediction == 1 else "Unsafe"
    except Exception as e:
        print(json.dumps({"error": f"Prediction failed: {e}", "traceback": traceback.format_exc()}))
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

        return messages

    try:
        recommendations = generate_recommendations(data)
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
