
import pandas as pd
import xgboost as xgb
import argparse
import json  # Import the json module for JSON handling
import sys
import traceback

def main():
    # === Setup Argument Parser === #
    try:
        parser = argparse.ArgumentParser(
            description="Predict water safety based on input parameters."
        )
        parser.add_argument("--pH", type=float, required=True, help="pH level of the water")
        parser.add_argument("--turbidity", type=float, required=True, help="Turbidity level of the water (NTU)")
        parser.add_argument("--temperature", type=float, required=True, help="Temperature of the water in Celsius")
        parser.add_argument("--conductivity", type=float, required=True, help="Electrical conductivity of the water (µS/cm)")
        parser.add_argument(
            "--dissolved_oxygen", type=float, required=True, help="Dissolved oxygen level in the water (mg/L)"
        )
        parser.add_argument("--salinity", type=float, required=True, help="Salinity of the water (ppt)")
        parser.add_argument("--total_dissolved_solids", type=float, required=True, help="Total dissolved solids in the water (mg/L)")
        parser.add_argument("--hardness", type=float, required=True, help="Hardness of the water (mg/L as CaCO₃)")
        parser.add_argument("--alkalinity", type=float, required=True, help="Alkalinity of the water (mg/L as CaCO₃)")
        parser.add_argument("--chlorine", type=float, required=True, help="Chlorine level in the water (mg/L)")
        parser.add_argument("--total_coliforms", type=float, required=True, help="Total coliforms count in the water (CFU/100 mL)")
        parser.add_argument("--e_coli", type=float, required=True, help="E. coli count in the water (CFU/100 mL)")

        args = parser.parse_args()  # Parse the arguments provided by the user
    except Exception as e:
        print(json.dumps({"error": f"Argument parsing failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Load Trained Model === #
    try:
        model = xgb.Booster()  # Initialize an XGBoost booster model
        model.load_model(
            "xgboost_waterwise.model"
        )  # Load the trained model from file
    except Exception as e:
        # If model loading fails, print an error in JSON format and exit
        print(json.dumps({"error": f"Failed to load model: {e}", "traceback": traceback.format_exc()}))  
        sys.exit(1)  # Exit the script with a non-zero code to indicate failure

    # === Prepare Input Data === #
    try:
        data = {  # Create a dictionary with the input parameters
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
        # Create a DataFrame from the input data
        input_data = pd.DataFrame([data])  
    except Exception as e:
        print(json.dumps({"error": f"Input data preparation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Predict === #
    try:  # Try block to handle potential exceptions during prediction
        # Create a DMatrix for the input data. DMatrix is the internal data structure that the model uses
        dmatrix_input = xgb.DMatrix(input_data, feature_names=list(input_data.columns))
    except Exception as e:  # Handle any exceptions that occur during DMatrix creation
        # Print the error message as JSON and exit the script if an error occurs
        print(json.dumps({"error": f"Failed to create DMatrix: {e}", "traceback": traceback.format_exc()}))  
        sys.exit(1)  # Exit the script with a non-zero exit code to indicate failure

    try:  # Try block to handle potential exceptions during prediction
        # Make a prediction using the loaded model and the DMatrix
        prediction = model.predict(dmatrix_input)[0]  
        # Convert the prediction to a human-readable label
        label = "Safe" if prediction == 1 else "Unsafe"  
    except Exception as e:  # Handle any exceptions that occur during prediction
        # Print the error message as JSON and exit the script if an error occurs
        print(json.dumps({"error": f"Prediction failed: {e}", "traceback": traceback.format_exc()}))  
        sys.exit(1)  # Exit the script with a non-zero exit code to indicate failure

    # === Recommendations === #
    def generate_recommendations(data):
        """
        Generates recommendations for water quality based on the provided data.

        Args:
            data (dict): A dictionary containing the water quality parameters.

        Returns:
            list: A list of recommendation messages.
        """
        messages = []
        # Check if pH is outside the safe range
        if data["pH"] < 6.5 or data["pH"] > 8.5:
            messages.append(f"pH ({data['pH']}) is outside safe range (6.5-8.5).")  
        # Check if turbidity is high
        if data["turbidity"] > 5:
            messages.append(f"Turbidity ({data['turbidity']}) is high (> 5 NTU).")  
        # Check if chlorine level is high
        if data["chlorine"] > 4:
            messages.append(f"Chlorine level ({data['chlorine']}) is high (> 4 mg/L).")  
        # Microbial contamination check removed because these features are no longer available in input
        return messages

    try:
        recommendations = generate_recommendations(data)  # Generate recommendations based on the input data
    except Exception as e:
        print(json.dumps({"error": f"Recommendation generation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

    # === Output === #
    try:
        # Create a dictionary containing the prediction output
        output = {"status": label, "recommendations": recommendations, "input_data": data}  
        print(json.dumps(output, indent=2))  # Output the results in JSON format with indentation for readability
    except Exception as e:
        print(json.dumps({"error": f"Output generation failed: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {e}", "traceback": traceback.format_exc()}))
        sys.exit(1)

 