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
    y = np.log1p(df['median_house_value'])
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
    
    # Select K Best using Mutual Information
    # To keep response time low, fit SelectKBest on a sample if dataset is too large
    # California dataset has 20k rows, mutual_info_regression on 20k rows is slow (~10s).
    # Let's sample 3000 rows for mutual information calculation
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
        
    # Fit on all training data
    model.fit(X_train_sel, y_train)
    
    # Predictions
    pred_train_log = model.predict(X_train_sel)
    pred_test_log = model.predict(X_test_sel)
    
    # Convert predictions back to original Median House Value scale (expm1)
    y_train_orig = np.expm1(y_train)
    y_test_orig = np.expm1(y_test)
    pred_train_orig = np.expm1(pred_train_log)
    pred_test_orig = np.expm1(pred_test_log)
    
    # Metrics
    train_rmse = float(np.sqrt(mean_squared_error(y_train_orig, pred_train_orig)))
    test_rmse = float(np.sqrt(mean_squared_error(y_test_orig, pred_test_orig)))
    train_r2 = float(r2_score(y_train_orig, pred_train_orig))
    test_r2 = float(r2_score(y_test_orig, pred_test_orig))
    
    # Feature importances
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
    
    # Fast multi-model CV benchmark (using sampled subset for high responsiveness)
    benchmark_models = {
        'LinearRegression': LinearRegression(),
        'Ridge': Ridge(random_state=42),
        'Lasso': Lasso(alpha=0.001, random_state=42),
        'ElasticNet': ElasticNet(alpha=0.001, random_state=42),
        'DecisionTree': DecisionTreeRegressor(random_state=42),
        'RandomForest': RandomForestRegressor(n_estimators=15, random_state=42, n_jobs=-1),
        'GradientBoosting': GradientBoostingRegressor(n_estimators=15, random_state=42),
        'AdaBoost': AdaBoostRegressor(n_estimators=15, random_state=42),
        'SVR': SVR(C=1.0)
    }
    if _xgb_available:
        benchmark_models['XGBoost'] = XGBRegressor(n_estimators=15, random_state=42, n_jobs=-1, objective='reg:squarederror')
    else:
        benchmark_models['KNeighbors'] = KNeighborsRegressor()
        
    benchmark_results = []
    cv = KFold(n_splits=3, shuffle=True, random_state=42)
    
    # Run benchmark CV on sample data
    sample_cv_size = min(1500, len(X_train))
    X_train_cv = X_train_scaled_df.sample(n=sample_cv_size, random_state=42)
    y_train_cv = y_train.loc[X_train_cv.index]
    
    for k_val in range(1, 11):
        selector_k = SelectKBest(score_func=mutual_info_regression, k=min(k_val, X_train_cv.shape[1]))
        X_train_k = selector_k.fit_transform(X_train_cv.values, y_train_cv.values)
        
        for name, bench_model in benchmark_models.items():
            neg_mse = cross_val_score(bench_model, X_train_k, y_train_cv.values, scoring='neg_mean_squared_error', cv=cv, n_jobs=-1)
            benchmark_results.append({
                'Algorithm': name,
                'Number of Features': k_val,
                'MSE': float(-neg_mse.mean())
            })
            
    # Sample down actuals and predicted values for scatter plot to avoid DOM lag
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
    y = np.log1p(df['median_house_value'])
    X = df.drop(columns=['median_house_value'])
    
    # Separate numeric and categorical
    numerical_cols = ['longitude', 'latitude', 'housing_median_age', 'total_rooms', 
                      'total_bedrooms', 'population', 'households', 'median_income']
    
    # Prepare input dictionary with default fallback to column mean
    input_vector = {}
    for col in numerical_cols:
        val = user_inputs.get(col)
        if val is None:
            input_vector[col] = float(X[col].mean())
        else:
            input_vector[col] = float(val)
            
    input_vector['ocean_proximity'] = user_inputs.get('ocean_proximity', X['ocean_proximity'].mode()[0])
            
    input_df = pd.DataFrame([input_vector])
    
    # Get exact dummy column alignment
    X_encoded = pd.get_dummies(X, columns=['ocean_proximity'], dtype=float)
    input_encoded = pd.get_dummies(input_df, columns=['ocean_proximity'], dtype=float)
    
    # Re-align categories
    for col in X_encoded.columns:
        if col not in input_encoded.columns:
            input_encoded[col] = 0.0
    input_encoded = input_encoded[X_encoded.columns]
    
    # Train test split for scaling pipeline
    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=0.2, random_state=42
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    input_scaled = scaler.transform(input_encoded)
    input_scaled_df = pd.DataFrame(input_scaled, columns=X_encoded.columns, index=input_encoded.index)
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
    pred_log = model.predict(input_sel)[0]
    pred_orig = float(np.expm1(pred_log))
    
    return jsonify({
        'prediction': pred_orig
    })

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000)
