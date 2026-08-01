import streamlit as st
st.title('app.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import os
import numpy as np
import pandas as pd
from pathlib import Path
from flask import Flask, request, jsonify, render_template

from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import f_regression, mutual_info_regression, RFE, SelectKBest
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet, LassoCV
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import spearmanr

try:
    from xgboost import XGBRegressor
    _xgb_available = True
except Exception:
    _xgb_available = False

app = Flask(__name__, template_folder='templates', static_folder='static')

DATA_PATH = Path(r"D:\H\0615\california archive\housing.csv")

def load_data():
    df = pd.read_csv(DATA_PATH)
    # Clean possible missing total_bedrooms
    if 'total_bedrooms' in df.columns:
        df['total_bedrooms'] = df['total_bedrooms'].fillna(df['total_bedrooms'].mean())
    return df

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/features', methods=['GET'])
def get_features():
    df = load_data()
    
    # Categorical option values
    ocean_proximity_categories = df['ocean_proximity'].unique().tolist() if 'ocean_proximity' in df.columns else []
    
    # Numerical features
    numerical_cols = ['longitude', 'latitude', 'housing_median_age', 'total_rooms', 
                      'total_bedrooms', 'population', 'households', 'median_income']
    
    feature_info = []
    for col in numerical_cols:
        if col in df.columns:
            feature_info.append({
                'name': col,
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'mean': float(df[col].mean()),
                'step': float((df[col].max() - df[col].min()) / 100.0)
            })
            
    return jsonify({
        'numerical_features': feature_info,
        'categorical_features': {
            'name': 'ocean_proximity',
            'categories': ocean_proximity_categories
        },
        'target_info': {
            'name': 'median_house_value',
            'min': float(df['median_house_value'].min()),
            'max': float(df['median_house_value'].max()),
            'mean': float(df['median_house_value'].mean())
        }
    })

@app.route('/api/train', methods=['POST'])
def train_model():
    data = request.get_json() or {}
    algo = data.get('algorithm', 'Ridge')
    k_features = int(data.get('k_features', 10))
    test_size = float(data.get('test_size', 0.2))
    
    # Hyperparameters
    alpha = float(data.get('alpha', 1.0))
    max_depth = data.get('max_depth', None)
    if max_depth is not None:
        max_depth = int(max_depth) if max_depth != 'None' else None
    
    df = load_data()
    y = df['median_house_value'] / 1000.0  # Scale to $1000s
    X = df.drop(columns=['median_house_value'])
    
    # One-hot encode the categorical column ocean_proximity
    X_encoded = pd.get_dummies(X, columns=['ocean_proximity'], dtype=float)
    
    # Train / Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=test_size, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=X_encoded.columns, index=X_train.index)
    X_test_scaled_df = pd.DataFrame(X_test_scaled, columns=X_encoded.columns, index=X_test.index)
    
    # Select K Best using Mutual Information (for active model training)
    # California dataset has 20k rows. Mutual information calculation on 20k rows is slow (~10s).
    # Sample 3000 rows for mutual information calculation
    sample_size = min(3000, len(X_train))
    X_train_sample = X_train_scaled_df.sample(n=sample_size, random_state=42)
    y_train_sample = y_train.loc[X_train_sample.index]
    
    selector = SelectKBest(score_func=mutual_info_regression, k=min(k_features, X_encoded.shape[1]))
    selector.fit(X_train_sample.values, y_train_sample.values)
    
    selected_mask = selector.get_support()
    selected_cols = X_encoded.columns[selected_mask].tolist()
    
    # Get score values
    mi_scores = selector.scores_
    feature_scores = sorted(
        [{'name': col, 'score': float(score)} for col, score in zip(X_encoded.columns, mi_scores)],
        key=lambda x: x['score'], reverse=True
    )
    
    # Subset to selected features
    X_train_sel = X_train_scaled_df[selected_cols].values
    X_test_sel = X_test_scaled_df[selected_cols].values
    
    # Initialize chosen model
    if algo == 'LinearRegression':
        model = LinearRegression()
    elif algo == 'Ridge':
        model = Ridge(alpha=alpha, random_state=42)
    elif algo == 'Lasso':
        model = Lasso(alpha=alpha, random_state=42)
    elif algo == 'ElasticNet':
        model = ElasticNet(alpha=alpha, random_state=42)
    elif algo == 'DecisionTree':
        model = DecisionTreeRegressor(max_depth=max_depth, random_state=42)
    elif algo == 'RandomForest':
        model = RandomForestRegressor(n_estimators=100, max_depth=max_depth, random_state=42, n_jobs=-1)
    elif algo == 'GradientBoosting':
        model = GradientBoostingRegressor(n_estimators=100, max_depth=max_depth or 3, random_state=42)
    elif algo == 'AdaBoost':
        model = AdaBoostRegressor(n_estimators=100, random_state=42)
    elif algo == 'SVR':
        model = SVR(C=alpha)
    elif algo == 'XGBoost' and _xgb_available:
        model = XGBRegressor(n_estimators=100, max_depth=max_depth or 6, learning_rate=0.1, random_state=42, n_jobs=-1, objective='reg:squarederror')
    elif algo == 'KNeighbors':
        model = KNeighborsRegressor()
    else:
        model = Ridge(alpha=alpha, random_state=42)
        
    model.fit(X_train_sel, y_train)
    
    # Predictions
    pred_train_raw = model.predict(X_train_sel)
    pred_test_raw = model.predict(X_test_sel)
    
    # Convert back to raw USD (multiply by 1000)
    y_train_orig = y_train * 1000.0
    y_test_orig = y_test * 1000.0
    pred_train_orig = pred_train_raw * 1000.0
    pred_test_orig = pred_test_raw * 1000.0
    
    # Metrics
    train_rmse = float(np.sqrt(mean_squared_error(y_train_orig, pred_train_orig)))
    test_rmse = float(np.sqrt(mean_squared_error(y_test_orig, pred_test_orig)))
    train_r2 = float(r2_score(y_train_orig, pred_train_orig))
    test_r2 = float(r2_score(y_test_orig, pred_test_orig))
    
    # Calculate feature importances
    importances = {}
    if hasattr(model, 'feature_importances_'):
        for col, val in zip(selected_cols, model.feature_importances_):
            importances[col] = float(val)
    elif hasattr(model, 'coef_'):
        for col, val in zip(selected_cols, model.coef_):
            importances[col] = float(abs(val))
            
    sorted_importances = sorted(
        [{'name': k, 'importance': v} for k, v in importances.items()],
        key=lambda x: x['importance'], reverse=True
    )
    
    # -------------------------- Stepwise Feature Selector Benchmark --------------------------
    total_features = X_encoded.shape[1]
    
    # Sample down training data for fast CV calculations
    sample_cv_size = min(1500, len(X_train))
    X_train_cv = X_train_scaled_df.sample(n=sample_cv_size, random_state=42)
    y_train_cv = y_train.loc[X_train_cv.index]
    
    # Extract feature rankings
    # 1. Pearson Correlation
    pearson_scores = [np.abs(np.corrcoef(X_train_cv.values[:, i], y_train_cv.values)[0, 1]) for i in range(total_features)]
    pearson_rank = np.argsort(pearson_scores)[::-1]

    # 2. Spearman Correlation
    spearman_scores = [np.abs(spearmanr(X_train_cv.values[:, i], y_train_cv.values).correlation) for i in range(total_features)]
    spearman_rank = np.argsort(spearman_scores)[::-1]

    # 3. F-test Regression
    f_scores, _ = f_regression(X_train_cv.values, y_train_cv.values)
    f_rank = np.argsort(f_scores)[::-1]

    # 4. Mutual Information
    mi_scores_cv = mutual_info_regression(X_train_cv.values, y_train_cv.values, random_state=42)
    mi_rank = np.argsort(mi_scores_cv)[::-1]

    # 5. RFE
    rfe = RFE(estimator=LinearRegression(), n_features_to_select=1)
    rfe.fit(X_train_cv.values, y_train_cv.values)
    rfe_rank = np.argsort(rfe.ranking_)

    # 6. Lasso L1 Coefficient Magnitudes
    lasso = LassoCV(cv=3, random_state=42).fit(X_train_cv.values, y_train_cv.values)
    lasso_coefs = np.abs(lasso.coef_)
    lasso_rank = np.argsort(lasso_coefs)[::-1]

    # 7. Random Forest Feature Importances
    rf = RandomForestRegressor(n_estimators=15, random_state=42, n_jobs=-1).fit(X_train_cv.values, y_train_cv.values)
    rf_rank = np.argsort(rf.feature_importances_)[::-1]

    # 8. SFS Forward Selection
    selected_sfs = []
    remaining = list(range(total_features))
    while remaining:
        best_score = -np.inf
        best_feat = None
        for f in remaining:
            candidate = selected_sfs + [f]
            score = np.mean(cross_val_score(LinearRegression(), X_train_cv.values[:, candidate], y_train_cv.values, cv=3, scoring='r2'))
            if score > best_score:
                best_score = score
                best_feat = f
        selected_sfs.append(best_feat)
        remaining.remove(best_feat)
    sfs_rank = selected_sfs

    selectors = {
        "Pearson Corr": pearson_rank,
        "Spearman Corr": spearman_rank,
        "F-test Reg": f_rank,
        "Mutual Info": mi_rank,
        "RFE": rfe_rank,
        "Lasso (L1)": lasso_rank,
        "Random Forest": rf_rank,
        "SFS (Forward)": sfs_rank
    }

    # Evaluate all selectors on the full test set using LinearRegression evaluator
    benchmark_results = []
    for name, rank in selectors.items():
        for k_val in range(1, total_features + 1):
            selected_indices = rank[:k_val]
            model_eval = LinearRegression()
            model_eval.fit(X_train_scaled[:, selected_indices], y_train)
            
            # Predict on test
            preds = model_eval.predict(X_test_scaled[:, selected_indices])
            
            # Compute R2 and MSE on RAW scale (multiplied by 1000 for MSE to match raw $1000s unit)
            r2_val = r2_score(y_test, preds)
            mse_val = mean_squared_error(y_test, preds)
            
            benchmark_results.append({
                'Selector': name,
                'Number of Features': k_val,
                'R2': float(r2_val),
                'MSE': float(mse_val)
            })
            
    # Sample down actuals and predicted values for scatter plot
    scatter_samples = min(500, len(y_test_orig))
    indices_sample = np.random.RandomState(42).choice(len(y_test_orig), scatter_samples, replace=False)
    
    return jsonify({
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'selected_features': selected_cols,
        'feature_scores': feature_scores,
        'importances': sorted_importances,
        'test_actual': y_test_orig.iloc[indices_sample].tolist(),
        'test_predicted': pred_test_orig[indices_sample].tolist(),
        'benchmark_data': benchmark_results
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json() or {}
    user_inputs = data.get('inputs', {})
    algo = data.get('algorithm', 'Ridge')
    k_features = int(data.get('k_features', 10))
    alpha = float(data.get('alpha', 1.0))
    max_depth = data.get('max_depth', None)
    if max_depth is not None:
        max_depth = int(max_depth) if max_depth != 'None' else None
        
    df = load_data()
    y = df['median_house_value'] / 1000.0  # target in $1000s
    X = df.drop(columns=['median_house_value'])
    
    # Separate numeric and categorical
    numerical_cols = ['longitude', 'latitude', 'housing_median_age', 'total_rooms', 
                      'total_bedrooms', 'population', 'households', 'median_income']
    
    input_vector = {}
    for col in numerical_cols:
        val = user_inputs.get(col)
        if val is None:
            input_vector[col] = float(X[col].mean())
        else:
            input_vector[col] = float(val)
            
    input_vector['ocean_proximity'] = user_inputs.get('ocean_proximity', X['ocean_proximity'].mode()[0])
            
    input_df = pd.DataFrame([input_vector])
    
    # Dummy alignment
    X_encoded = pd.get_dummies(X, columns=['ocean_proximity'], dtype=float)
    input_encoded = pd.get_dummies(input_df, columns=['ocean_proximity'], dtype=float)
    
    # Re-align categories
    for col in X_encoded.columns:
        if col not in input_encoded.columns:
            input_encoded[col] = 0.0
    input_encoded = input_encoded[X_encoded.columns]
    
    # Split for scaler fitting
    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=0.2, random_state=42
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    input_scaled = scaler.transform(input_encoded)
    input_scaled_df = pd.DataFrame(input_scaled, columns=X_encoded.columns)
    X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=X_encoded.columns, index=X_train.index)
    
    # Feature select
    sample_size = min(3000, len(X_train))
    X_train_sample = X_train_scaled_df.sample(n=sample_size, random_state=42)
    y_train_sample = y_train.loc[X_train_sample.index]
    
    selector = SelectKBest(score_func=mutual_info_regression, k=min(k_features, X_encoded.shape[1]))
    selector.fit(X_train_sample.values, y_train_sample.values)
    selected_cols = X_encoded.columns[selector.get_support()].tolist()
    
    X_train_sel = X_train_scaled_df[selected_cols].values
    input_sel = input_scaled_df[selected_cols].values
    
    # Train
    if algo == 'LinearRegression':
        model = LinearRegression()
    elif algo == 'Ridge':
        model = Ridge(alpha=alpha, random_state=42)
    elif algo == 'Lasso':
        model = Lasso(alpha=alpha, random_state=42)
    elif algo == 'ElasticNet':
        model = ElasticNet(alpha=alpha, random_state=42)
    elif algo == 'DecisionTree':
        model = DecisionTreeRegressor(max_depth=max_depth, random_state=42)
    elif algo == 'RandomForest':
        model = RandomForestRegressor(n_estimators=100, max_depth=max_depth, random_state=42, n_jobs=-1)
    elif algo == 'GradientBoosting':
        model = GradientBoostingRegressor(n_estimators=100, max_depth=max_depth or 3, random_state=42)
    elif algo == 'AdaBoost':
        model = AdaBoostRegressor(n_estimators=100, random_state=42)
    elif algo == 'SVR':
        model = SVR(C=alpha)
    elif algo == 'XGBoost' and _xgb_available:
        model = XGBRegressor(n_estimators=100, max_depth=max_depth or 6, learning_rate=0.1, random_state=42, n_jobs=-1, objective='reg:squarederror')
    elif algo == 'KNeighbors':
        model = KNeighborsRegressor()
    else:
        model = Ridge(alpha=alpha, random_state=42)
        
    model.fit(X_train_sel, y_train)
    pred_raw = model.predict(input_sel)[0]
    pred_orig = float(pred_raw * 1000.0)  # Scale back to raw USD
    
    return jsonify({
        'prediction': pred_orig
    })

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000)
