# Import required Python libraries
import pandas as pd  # For data manipulation and DataFrame creation
import xgboost as xgb  # For loading and using the XGBoost model
import argparse  # For parsing command-line arguments
import json  # For JSON output formatting
import sys  # For system exit handling
import traceback  # For capturing error stack traces

def main():
    # === Setup Argument Parser === #
    # Define command-line arguments for water quality parameters
    try:
        parser = argparse.ArgumentParser(description="Predict water safety based on input parameters.")
        # Add required arguments for water quality metrics
        parser.add_argument("--pH", type=float, required=True, help="pH level of the water")
        parser.add_argument("--turbidity", type=float, required=True, help="Turbidity in NTU")
        parser.add_argument("--temperature", type=float, required=True, help="Temperature in °C")
        parser.add_argument("--conductivity", type=float, required=True, help="Electrical conductivity in µS/cm")
        parser.add_argument("--dissolved_oxygen", type=float, required=True, help="Dissolved oxygen in mg/L")
        parser.add_argument("--salinity", type=float, required=True, help="Salinity in ppt")
        parser.add_argument("--total_dissolved_solids", type=float, required=True, help="Total dissolved solids in mg/L")
        parser.add_argument("--hardness", type=float, required=True, help="Hardness in mg/L")
        parser.add_argument("--alkalinity", type=float, required=True, help="Alkalinity in mg/L")
        parser.add_argument("--chlorine", type=float, required=True, help="Chlorine concentration in mg/L")
        parser.add_argument("--total_coliforms", type=float, required=True, help="Total coliforms in MPN/100mL")
        parser.add_argument("--e_coli", type=float, required=True, help="E. coli in MPN/100mL")
        args = parser.parse_args()  # Parse command-line arguments
    except Exception as e:
        # Handle argument parsing errors and output JSON error message
        print(json.dumps({"error": f"Argument parsing failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)  # Exit with error code

    # === Load Trained Model === #
    # Load the pre-trained XGBoost model for water safety prediction
    try:
        model = xgb.Booster()  # Initialize XGBoost Booster object
        model.load_model("xgboost_waterwise.model")  # Load model from file
    except Exception as e:
        # Handle model loading errors
        print(json.dumps({"error": f"Failed to load model: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Prepare Input Data === #
    # Create a DataFrame from input arguments for model prediction
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
        input_data = pd.DataFrame([data])  # Convert dictionary to single-row DataFrame
    except Exception as e:
        # Handle errors in preparing input data
        print(json.dumps({"error": f"Input data preparation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Predict === #
    # Prepare data for XGBoost prediction and make prediction
    try:
        # Select only the features used during model training
        model_features = ['pH', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen', 
                         'salinity', 'total_dissolved_solids', 'hardness', 'alkalinity', 'chlorine']
        input_data_for_model = input_data[model_features]  # Filter DataFrame to model features

        # Create DMatrix for XGBoost prediction
        dmatrix_input = xgb.DMatrix(input_data_for_model, feature_names=model_features)

    except Exception as e:
        # Handle errors in creating DMatrix
        print(json.dumps({"error": f"Failed to create DMatrix: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    try:
        # Make prediction using the loaded model
        prediction = model.predict(dmatrix_input)[0]
        label = "Safe" if prediction == 1 else "Unsafe"  # Convert prediction to human-readable label
    except Exception as e:
        # Handle prediction errors
        print(json.dumps({"error": f"Prediction failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Rule-Based Checks (WHO Guidelines) === #
    # Apply WHO-based rules to override model prediction if critical parameters are unsafe
    is_unsafe_by_rules = False
    if args.pH < 6.5 or args.pH > 8.5:  # pH outside WHO safe range
        is_unsafe_by_rules = True
    if args.turbidity > 5:  # Turbidity above WHO limit
        is_unsafe_by_rules = True
    if args.chlorine > 5:  # Chlorine above WHO limit
        is_unsafe_by_rules = True
    if args.total_coliforms > 0:  # Any coliforms indicate contamination
        is_unsafe_by_rules = True
    if args.e_coli > 0:  # Any E. coli indicates serious contamination
        is_unsafe_by_rules = True

    try:
        # Override model prediction to "Unsafe" if any rule indicates unsafe water
        if is_unsafe_by_rules:
            label = "Unsafe"
    except Exception as e:
        # Handle errors in rule-based checks
        print(json.dumps({"error": f"Rule-based checks failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Recommendations === #
    # Define function to generate recommendations based on input parameters
    def generate_recommendations(data):
        messages = []  # List to store recommendation messages

        # pH recommendations
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

        # Turbidity recommendation
        if data["turbidity"] > 5:
            messages.append(
                f"Turbidity ({data['turbidity']} NTU) is high. Cloudy water may contain pathogens or sediments. "
                "Use coagulation-flocculation followed by sand filtration or membrane filtration."
            )

        # Temperature recommendation
        if data["temperature"] > 30:
            messages.append(
                f"Temperature ({data['temperature']} °C) is high. Elevated temperature can decrease dissolved oxygen levels and promote microbial growth. "
                "Consider aeration or cooling methods, and monitor dissolved oxygen and microbial parameters."
            )

        # Chlorine recommendation
        if data["chlorine"] > 4:
            messages.append(
                f"Chlorine ({data['chlorine']} mg/L) exceeds safe levels. Can cause taste issues and health risks. "
                "Consider activated carbon filters or dechlorination with ascorbic acid or sodium thiosulfate."
            )

        # Total Dissolved Solids (TDS) recommendation
        if data["total_dissolved_solids"] > 500:
            messages.append(
                f"TDS ({data['total_dissolved_solids']} mg/L) is high. Indicates excess minerals or pollutants. "
                "Reverse osmosis, distillation, or deionization systems are effective treatment methods."
            )

        # Conductivity recommendation
        if data["conductivity"] > 1000:
            messages.append(
                f"Conductivity ({data['conductivity']} µS/cm) is high. May indicate excessive salts or contamination. "
                "Test for specific ions (e.g., nitrates, sulfates) and consider ion exchange or reverse osmosis."
            )

        # Dissolved Oxygen recommendation
        if data["dissolved_oxygen"] < 5:
            messages.append(
                f"Dissolved Oxygen ({data['dissolved_oxygen']} mg/L) is low. This can stress aquatic life. "
                "Introduce aeration methods like fountains, diffused aerators, or surface agitators."
            )

        # Salinity recommendation
        if data["salinity"] > 0.5:
            messages.append(
                f"Salinity ({data['salinity']} ppt) is high. May indicate saltwater intrusion or industrial discharge. "
                "Monitor sources and use desalination techniques such as reverse osmosis."
            )

        # Hardness recommendation
        if data["hardness"] > 150:
            messages.append(
                f"Hardness ({data['hardness']} mg/L) is high. May cause scale in pipes and reduce soap effectiveness. "
                "Water softeners using ion-exchange resins are recommended."
            )

        # Alkalinity recommendations
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

        # Total Coliforms recommendation
        if data["total_coliforms"] > 0:
            messages.append(
                f"Total Coliforms ({data['total_coliforms']} MPN/100mL) detected. Indicates potential fecal contamination. "
                "Requires immediate disinfection (e.g., chlorination) and investigation of the source."
            )

        # E. coli recommendation
        if data["e_coli"] > 0:
            messages.append(
                f"E. coli ({data['e_coli']} MPN/100mL) detected. Confirms fecal contamination and serious health risk. "
                "Water is unsafe to drink without treatment. Boil water or use strong disinfection and identify/eliminate contamination source."
            )

        return messages

    try:
        # Generate recommendations based on input data
        recommendations = generate_recommendations(data)
        # Fallback recommendation if water is predicted unsafe but no specific issues are flagged
        if label == "Unsafe" and not recommendations:
            recommendations.append(
                "Overall prediction is Unsafe. While individual parameters appear within typical ranges, "
                "the model indicates potential issues. Consider further testing or professional assessment before use."
            )
    except Exception as e:
        # Handle errors in recommendation generation
        print(json.dumps({"error": f"Recommendation generation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Output === #
    # Prepare and output final JSON response
    try:
        output = {
            "status": label,  # Safe or Unsafe label
            "recommendations": recommendations,  # List of recommendation messages
            "input_data": data  # Input parameters for reference
        }
        print(json.dumps(output, indent=2))  # Output formatted JSON
    except Exception as e:
        # Handle errors in output generation
        print(json.dumps({"error": f"Output generation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

# Entry point for the script
if __name__ == "__main__":
    try:
        main()  # Execute main function
    except Exception as e:
        # Catch any unexpected errors in main execution
        print(json.dumps({"error": f"Unexpected error: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)