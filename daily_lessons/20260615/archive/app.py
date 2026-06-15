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

DATA_PATH = Path(r"D:\H\0615\archive\HousingData.csv")

def load_data():
    df = pd.read_csv(DATA_PATH)
    # Clean standard NA representations
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
    y = df['MEDV']  # Raw target scale (no log)
    X = df.drop(columns=['MEDV'])
    
    # Train / Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=X.columns, index=X_train.index)
    X_test_scaled_df = pd.DataFrame(X_test_scaled, columns=X.columns, index=X_test.index)
    
    # Select K Best using Mutual Information (for active model training)
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
    pred_train_raw = model.predict(X_train_sel)
    pred_test_raw = model.predict(X_test_sel)
    
    # Metrics
    train_rmse = float(np.sqrt(mean_squared_error(y_train, pred_train_raw)))
    test_rmse = float(np.sqrt(mean_squared_error(y_test, pred_test_raw)))
    train_r2 = float(r2_score(y_train, pred_train_raw))
    test_r2 = float(r2_score(y_test, pred_test_raw))
    
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
    total_features = X.shape[1]
    
    # 1. Pearson Correlation
    pearson_scores = [np.abs(np.corrcoef(X_train_scaled[:, i], y_train)[0, 1]) for i in range(total_features)]
    pearson_rank = np.argsort(pearson_scores)[::-1]

    # 2. Spearman Correlation
    spearman_scores = [np.abs(spearmanr(X_train_scaled[:, i], y_train).correlation) for i in range(total_features)]
    spearman_rank = np.argsort(spearman_scores)[::-1]

    # 3. F-test Regression
    f_scores, _ = f_regression(X_train_scaled, y_train)
    f_rank = np.argsort(f_scores)[::-1]

    # 4. Mutual Information
    mi_scores_cv = mutual_info_regression(X_train_scaled, y_train, random_state=42)
    mi_rank = np.argsort(mi_scores_cv)[::-1]

    # 5. RFE
    rfe = RFE(estimator=LinearRegression(), n_features_to_select=1)
    rfe.fit(X_train_scaled, y_train)
    rfe_rank = np.argsort(rfe.ranking_)

    # 6. Lasso L1 Coefficient Magnitudes
    lasso = LassoCV(cv=3, random_state=42).fit(X_train_scaled, y_train)
    lasso_coefs = np.abs(lasso.coef_)
    lasso_rank = np.argsort(lasso_coefs)[::-1]

    # 7. Random Forest Feature Importances
    rf = RandomForestRegressor(n_estimators=30, random_state=42, n_jobs=-1).fit(X_train_scaled, y_train)
    rf_rank = np.argsort(rf.feature_importances_)[::-1]

    # 8. SFS Forward Selection
    selected_sfs = []
    remaining = list(range(total_features))
    while remaining:
        best_score = -np.inf
        best_feat = None
        for f in remaining:
            candidate = selected_sfs + [f]
            score = np.mean(cross_val_score(LinearRegression(), X_train_scaled[:, candidate], y_train, cv=3, scoring='r2'))
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

    benchmark_results = []
    for name, rank in selectors.items():
        for k_val in range(1, total_features + 1):
            selected_indices = rank[:k_val]
            model_eval = LinearRegression()
            model_eval.fit(X_train_scaled[:, selected_indices], y_train)
            
            # Predict on test
            preds = model_eval.predict(X_test_scaled[:, selected_indices])
            r2_val = r2_score(y_test, preds)
            mse_val = mean_squared_error(y_test, preds)
            
            benchmark_results.append({
                'Selector': name,
                'Number of Features': k_val,
                'R2': float(r2_val),
                'MSE': float(mse_val)
            })
            
    return jsonify({
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'selected_features': selected_cols,
        'feature_scores': feature_scores,
        'importances': sorted_importances,
        'test_actual': y_test.tolist(),
        'test_predicted': pred_test_raw.tolist(),
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
    y = df['MEDV']
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
    X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=X.columns, index=X_train.index)
    
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
    pred_raw = model.predict(input_sel)[0]
    pred_orig = float(pred_raw)
    
    return jsonify({
        'prediction': pred_orig
    })

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000)
