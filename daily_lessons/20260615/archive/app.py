import os
import numpy as np
import pandas as pd
from pathlib import Path
from flask import Flask, request, jsonify, render_template

from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, mutual_info_regression
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, r2_score

try:
    from xgboost import XGBRegressor
    _xgb_available = True
except Exception:
    _xgb_available = False

app = Flask(__name__, template_folder='templates', static_folder='static')

DATA_PATH = Path(r"D:\H\0615\archive\HousingData.csv")

def load_data():
    df = pd.read_csv(DATA_PATH)
    # Clean standard NA representations
    df = df.replace("NA", np.nan).astype(float)
    # Impute missing values with column mean to keep data size stable for interactive sliders
    for col in df.columns:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].mean())
    return df

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/features', methods=['GET'])
def get_features():
    df = load_data()
    X = df.drop(columns=['MEDV'])
    
    # Calculate stats for building frontend input sliders dynamically
    feature_info = []
    for col in X.columns:
        feature_info.append({
            'name': col,
            'min': float(X[col].min()),
            'max': float(X[col].max()),
            'mean': float(X[col].mean()),
            'step': float((X[col].max() - X[col].min()) / 100.0)
        })
    return jsonify({
        'features': feature_info,
        'target_info': {
            'name': 'MEDV',
            'min': float(df['MEDV'].min()),
            'max': float(df['MEDV'].max()),
            'mean': float(df['MEDV'].mean())
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
    y = np.log1p(df['MEDV'])
    X = df.drop(columns=['MEDV'])
    
    # Train / Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=X.columns)
    X_test_scaled_df = pd.DataFrame(X_test_scaled, columns=X.columns)
    
    # Select K Best using Mutual Information
    selector = SelectKBest(score_func=mutual_info_regression, k=k_features)
    selector.fit(X_train_scaled, y_train)
    
    selected_mask = selector.get_support()
    selected_cols = X.columns[selected_mask].tolist()
    
    # Get score values
    mi_scores = selector.scores_
    feature_scores = sorted(
        [{'name': col, 'score': float(score)} for col, score in zip(X.columns, mi_scores)],
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
    pred_train_log = model.predict(X_train_sel)
    pred_test_log = model.predict(X_test_sel)
    
    # Convert predictions back to original MEDV scale (expm1)
    y_train_orig = np.expm1(y_train)
    y_test_orig = np.expm1(y_test)
    pred_train_orig = np.expm1(pred_train_log)
    pred_test_orig = np.expm1(pred_test_log)
    
    # Metrics
    train_rmse = float(np.sqrt(mean_squared_error(y_train_orig, pred_train_orig)))
    test_rmse = float(np.sqrt(mean_squared_error(y_test_orig, pred_test_orig)))
    train_r2 = float(r2_score(y_train_orig, pred_train_orig))
    test_r2 = float(r2_score(y_test_orig, pred_test_orig))
    
    # Calculate feature importances if the model supports it
    importances = {}
    if hasattr(model, 'feature_importances_'):
        for col, val in zip(selected_cols, model.feature_importances_):
            importances[col] = float(val)
    elif hasattr(model, 'coef_'):
        for col, val in zip(selected_cols, model.coef_):
            importances[col] = float(abs(val))
            
    # Sort importances
    sorted_importances = sorted(
        [{'name': k, 'importance': v} for k, v in importances.items()],
        key=lambda x: x['importance'], reverse=True
    )
    
    # Benchmark loop for multi-model performance tracking (MSE line chart)
    # We benchmark K from 1 to 10 using exactly 10 models
    benchmark_models = {
        'LinearRegression': LinearRegression(),
        'Ridge': Ridge(random_state=42),
        'Lasso': Lasso(alpha=0.001, random_state=42),
        'ElasticNet': ElasticNet(alpha=0.001, random_state=42),
        'DecisionTree': DecisionTreeRegressor(random_state=42),
        'RandomForest': RandomForestRegressor(n_estimators=30, random_state=42, n_jobs=-1),
        'GradientBoosting': GradientBoostingRegressor(n_estimators=30, random_state=42),
        'AdaBoost': AdaBoostRegressor(n_estimators=30, random_state=42),
        'SVR': SVR(C=1.0)
    }
    if _xgb_available:
        benchmark_models['XGBoost'] = XGBRegressor(n_estimators=30, random_state=42, n_jobs=-1, objective='reg:squarederror')
    else:
        benchmark_models['KNeighbors'] = KNeighborsRegressor()
        
    benchmark_results = []
    cv = KFold(n_splits=3, shuffle=True, random_state=42) # Fast CV for UX responsiveness
    
    for k_val in range(1, 11):
        selector_k = SelectKBest(score_func=mutual_info_regression, k=k_val)
        X_train_k = selector_k.fit_transform(X_train_scaled, y_train)
        
        for name, bench_model in benchmark_models.items():
            neg_mse = cross_val_score(bench_model, X_train_k, y_train, scoring='neg_mean_squared_error', cv=cv, n_jobs=-1)
            benchmark_results.append({
                'Algorithm': name,
                'Number of Features': k_val,
                'MSE': float(-neg_mse.mean())
            })
            
    return jsonify({
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'selected_features': selected_cols,
        'feature_scores': feature_scores,
        'importances': sorted_importances,
        'test_actual': y_test_orig.tolist(),
        'test_predicted': pred_test_orig.tolist(),
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
    y = np.log1p(df['MEDV'])
    X = df.drop(columns=['MEDV'])
    
    # Prepare input vector
    input_vector = {}
    for col in X.columns:
        val = user_inputs.get(col)
        if val is None:
            input_vector[col] = float(X[col].mean())
        else:
            input_vector[col] = float(val)
            
    input_df = pd.DataFrame([input_vector])
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    input_scaled = scaler.transform(input_df)
    input_scaled_df = pd.DataFrame(input_scaled, columns=X.columns)
    X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=X.columns)
    
    # Select K
    selector = SelectKBest(score_func=mutual_info_regression, k=k_features)
    selector.fit(X_train_scaled, y_train)
    selected_cols = X.columns[selector.get_support()].tolist()
    
    X_train_sel = X_train_scaled_df[selected_cols].values
    input_sel = input_scaled_df[selected_cols].values
    
    # Train chosen
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
    pred_log = model.predict(input_sel)[0]
    pred_orig = float(np.expm1(pred_log))
    
    return jsonify({
        'prediction': pred_orig
    })

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000)
