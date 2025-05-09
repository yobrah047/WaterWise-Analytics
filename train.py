import pandas as pd
import numpy as np
import xgboost as xgb
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve, auc, recall_score, make_scorer
import joblib
import argparse
import sys


def load_and_prepare(path):
    # Load Excel or CSV
    if path.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    # Standardize column names
    df.columns = (
        df.columns.str.strip()
                 .str.lower()
                 .str.replace(' ', '_')
                 .str.replace('-', '_')
    )
    # Rename 'ph' to 'pH' to match prediction script
    if 'ph' in df.columns:
        df = df.rename(columns={'ph': 'pH'})

    # Drop incomplete microbial data
    df = df.dropna(subset=['total_coliforms', 'e_coli'])

    # Label: unsafe if any microbial contamination
    df['label'] = np.where((df['total_coliforms'] > 0) | (df['e_coli'] > 0), 1, 0)

    # Select features
    features = [
        'pH', 'turbidity', 'temperature', 'conductivity',
        'dissolved_oxygen', 'salinity', 'total_dissolved_solids',
        'hardness', 'alkalinity', 'chlorine'
    ]
    X = df[features]
    y = df['label']
    return X, y


def oversample_train_df(train_df, label_col='label', random_state=42):
    # Identify majority/minority classes
    counts = train_df[label_col].value_counts()
    maj = counts.idxmax()
    min_ = counts.idxmin()
    n = counts.max()

    df_maj = train_df[train_df[label_col] == maj]
    df_min = train_df[train_df[label_col] == min_]

    # Upsample minority
    df_min_up = df_min.sample(n=n, replace=True, random_state=random_state)

    # Combine and shuffle
    df_res = pd.concat([df_maj, df_min_up], axis=0)
    df_res = df_res.sample(frac=1, random_state=random_state).reset_index(drop=True)
    return df_res


def main():
    parser = argparse.ArgumentParser(description='Retrain WaterWise XGBoost model with oversampling and threshold tuning')
    parser.add_argument('--data', type=str, required=True, help='Path to labeled dataset (CSV or Excel)')
    parser.add_argument('--output', type=str, default='xgboost_waterwise.model', help='Output model filename')
    args = parser.parse_args()

    # Load and prepare data
    try:
        X, y = load_and_prepare(args.data)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    # Combine for splitting
    df_all = pd.concat([X, y.rename('label')], axis=1)
    train_df, test_df = train_test_split(df_all, test_size=0.2, random_state=42, stratify=df_all['label'])

    # Oversample training data
    res_df = oversample_train_df(train_df)
    print(f"Resampled training distribution: {res_df['label'].value_counts().to_dict()}")

    X_res = res_df.drop(columns='label')
    y_res = res_df['label']
    X_test = test_df.drop(columns='label')
    y_test = test_df['label']

    # Initialize classifier
    clf = XGBClassifier(
        objective='binary:logistic',
        eval_metric='logloss',
        use_label_encoder=False,
        random_state=42
    )

    # Hyperparameter grid
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'subsample': [0.7, 0.9],
        'colsample_bytree': [0.7, 0.9]
    }

    # Scoring metrics
    scoring = {
        'safe_recall': make_scorer(recall_score, pos_label=0),
        'unsafe_recall': make_scorer(recall_score, pos_label=1),
        'f1_macro': 'f1_macro'
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    grid = GridSearchCV(
        clf,
        param_grid,
        scoring=scoring,
        refit='safe_recall',
        cv=cv,
        verbose=1,
        n_jobs=-1
    )

    # Train
    grid.fit(X_res, y_res)
    best = grid.best_estimator_
    print("Best parameters based on safe recall:", grid.best_params_)

    # Evaluate on test set
    y_pred = best.predict(X_test)
    y_prob = best.predict_proba(X_test)[:, 1]

    print("\n--- Test Evaluation ---")
    print(classification_report(y_test, y_pred, digits=4))
    print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
    print(f"ROC AUC: {roc_auc_score(y_test, y_prob):.4f}")
    precision, recall, _ = precision_recall_curve(y_test, y_prob)
    print(f"PR AUC: {auc(recall, precision):.4f}")

    # Threshold tuning
    best_t, best_sum = 0.5, 0
    print("\n--- Threshold Tuning ---")
    for t in np.linspace(0.1, 0.9, 9):
        preds = (y_prob > t).astype(int)
        s = recall_score(y_test, preds, pos_label=0) + recall_score(y_test, preds, pos_label=1)
        print(f"Threshold {t:.2f} -> Safe recall: {recall_score(y_test, preds, pos_label=0):.3f}, Unsafe recall: {recall_score(y_test, preds, pos_label=1):.3f}")
        if s > best_sum:
            best_sum, best_t = s, t
    print(f"Selected threshold: {best_t:.2f} (sum recall: {best_sum:.3f})")

    # Save model and threshold
    best.get_booster().save_model(args.output)
    joblib.dump({'model': best, 'threshold': best_t}, args.output + '.joblib')
    print(f"Model and threshold saved to {args.output} and {args.output}.joblib")

if __name__ == '__main__':
    main()
