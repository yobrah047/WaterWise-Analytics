import pandas as pd
from sklearn.model_selection import train_test_split
import xgboost as xgb
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

# === 1. Load dataset ===
# Load the dataset from an Excel file
df = pd.read_excel("updated_waterwise_dataset_2000.xlsx")

# ===============================================================
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
# ===============================================================
# === 2. Drop unused columns ===
# Drop columns that are not needed for the model
df = df.drop(columns=["location", "water_source", "date", "notes"], errors="ignore")

# ===============================================================
# === 3. Handle missing values ===
# Calculate the number of rows before removing missing values
original_rows = len(df)
# Remove rows with any missing values
df = df.dropna()
# Calculate the number of rows dropped
dropped_rows = original_rows - len(df)

# ===============================================================
# === 4. Add 'label' column: 1 = Safe, 0 = Unsafe ===
# Check if 'e_coli' and 'total_coliforms' columns exist
if 'e_coli' in df.columns and 'total_coliforms' in df.columns:
    # Create the 'label' column based on 'e_coli' and 'total_coliforms'
    df["label"] = df.apply(lambda row: 1 if row["e_coli"] == 0 and row["total_coliforms"] == 0 else 0, axis=1)
    # Check if only one class is present in the 'label' column
    if df["label"].nunique() < 2:
        print("Error: The dataset contains only one class after processing. Cannot train model.")
        print(df['label'].value_counts())
        exit()
else:
    # Print an error message if 'e_coli' or 'total_coliforms' is missing
    print("Error: 'e_coli' or 'total_coliforms' column not found after cleaning/dropping NAs.")
    exit()
# ===============================================================
# === 5. Split features and target ===
# Separate the features (X) and target (y) variables
X = df.drop(columns=["label", "e_coli", "total_coliforms"], errors='ignore')
y = df["label"]
# ===============================================================
# === 6. Train/test split ===
if len(X) < 2 or len(y) < 2:
    print(f"Error: Not enough data to perform train/test split after processing. Data points: {len(X)}")
    exit()

try:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if y.nunique() > 1 else None
    )
except ValueError as e:
    print(f"Error during train/test split: {e}")
    print(f"Dataset size: {len(X)}")
    print("Label distribution:")
    print(y.value_counts())
    exit()   
# ===============================================================
# === 7. Train model ===
# Initialize and train the XGBoost model
model = xgb.XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='logloss')
model.fit(X_train, y_train)

# ===============================================================
# === 8. Evaluate model ===
# Predict on the test set and calculate evaluation metrics
# === Evaluate model ===
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)

# Print model evaluation results
print("\n--- Model Evaluation ---")
print(f"Rows before dropna: {original_rows}")
print(f"Rows after dropna:  {len(df)} (Dropped: {dropped_rows})")
print(f"Training set size:  {len(X_train)}")
print(f"Test set size:      {len(X_test)}")
print(f"Accuracy:           {accuracy:.4f}")
print(f"Precision:          {precision:.4f}")
print(f"Recall:             {recall:.4f}")
print(f"F1-Score:           {f1:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, zero_division=0))
print("------------------------\n")
 
# ===============================================================
# === 9. Confution matrix ===
# Import necessary libraries for confusion matrix visualization
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# Create the confusion matrix
cm = confusion_matrix(y_test, y_pred)

# Display the confusion matrix
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1])
disp.plot(cmap='Blues')

# Show the plot with a title
plt.title("Confusion Matrix for Water Quality Classifier")
plt.show()
# ===============================================================
# === 10. Save model ===
# Save the trained model to a file
model.save_model("xgboost_waterwise.model")
joblib.dump(model, "xgboost_waterwise.joblib")
# Confirmation message
print("✅ Model trained, evaluated, and saved successfully with clean column names!")
