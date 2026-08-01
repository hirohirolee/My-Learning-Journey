import streamlit as st

import sys
import joblib
import pandas as pd
import numpy as np

def predict_profit(rd_spend, admin_spend, market_spend, state):
    # Load model and scaler
    scaler = joblib.load('scaler.pkl')
    lr_model = joblib.load('lr_model.pkl')
    rf_model = joblib.load('rf_model.pkl')
    features = joblib.load('features.pkl')
    
    # Preprocess inputs
    state = state.strip().lower()
    state_florida = 1 if 'florida' in state or 'fl' in state or '佛' in state else 0
    state_newyork = 1 if 'new york' in state or 'ny' in state or '紐' in state else 0
    
    # Create input DataFrame
    input_data = pd.DataFrame([{
        'R&D Spend': float(rd_spend),
        'Administration': float(admin_spend),
        'Marketing Spend': float(market_spend),
        'State_Florida': state_florida,
        'State_New York': state_newyork
    }])
    
    # Reorder columns to match features
    input_data = input_data[features]
    
    # Scale numerical features
    num_cols = ['R&D Spend', 'Administration', 'Marketing Spend']
    input_scaled = input_data.copy()
    input_scaled[num_cols] = scaler.transform(input_data[num_cols])
    
    # Predict
    pred_lr = lr_model.predict(input_scaled)[0]
    pred_rf = rf_model.predict(input_scaled)[0]
    
    return pred_lr, pred_rf

if __name__ == '__main__':
    if len(sys.argv) < 5:
        st.write("Usage: python predict.py <RD> <Admin> <Marketing> <State>")
        sys.exit(1)
        
    rd = sys.argv[1]
    admin = sys.argv[2]
    mkt = sys.argv[3]
    st = sys.argv[4]
    
    try:
        lr_p, rf_p = predict_profit(rd, admin, mkt, st)
        st.write(f"LR_PRED:{lr_p:.2f}")
        st.write(f"RF_PRED:{rf_p:.2f}")
    except Exception as e:
        st.write(f"ERROR:{str(e)}")
