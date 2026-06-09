import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

# Load and clean data
df = pd.read_csv('50_Startups.csv')
df_clean = df.drop(index=49).reset_index(drop=True)

# Encode categorical variable State
df_encoded = pd.get_dummies(df_clean, columns=['State'], drop_first=True, dtype=int)

X = df_encoded.drop('Profit', axis=1)
y = df_encoded['Profit']

# We train on the FULL cleaned dataset for the simulator to utilize all available data
num_cols = ['R&D Spend', 'Administration', 'Marketing Spend']
scaler = StandardScaler()

X_scaled = X.copy()
X_scaled[num_cols] = scaler.fit_transform(X[num_cols])

# Train models
lr_model = LinearRegression()
lr_model.fit(X_scaled, y)

rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_scaled, y)

# Save models, scaler, and features list
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(lr_model, 'lr_model.pkl')
joblib.dump(rf_model, 'rf_model.pkl')
joblib.dump(list(X.columns), 'features.pkl')

print("Models and scaler saved successfully!")
