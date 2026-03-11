import streamlit as st
import pandas as pd
from difflib import SequenceMatcher

# --- Helper Functions ---
def get_similarity(a, b):
    return SequenceMatcher(None, str(a).upper(), str(b).upper()).ratio()

def find_best_match(item, choices, threshold=0.6):
    best_match = None
    highest_score = 0
    for choice in choices:
        score = get_similarity(item, choice)
        if score > highest_score:
            highest_score = score
            best_match = choice
    return best_match if highest_score >= threshold else None

# --- Mock Data Loader (Simulating Parsed PDFs) ---
def load_mock_data():
    carrier_data = [
        {"Description": "RFG 3ARSH", "Qty": 20, "Unit": "SQ", "Price": 350.00},
        {"Description": "RFG DRIP", "Qty": 100, "Unit": "LF", "Price": 1.50},
    ]
    contractor_data = [
        {"Description": "3-Tab Shingles (AR)", "Qty": 22, "Unit": "SQ", "Price": 425.00},
        {"Description": "Drip Edge - Aluminum", "Qty": 110, "Unit": "LF", "Price": 3.00},
        {"Description": "Ice & Water Shield", "Qty": 3, "Unit": "SQ", "Price": 120.00}, # Supplement Opportunity
    ]
    return pd.DataFrame(carrier_data), pd.DataFrame(contractor_data)

# --- UI Layout ---
st.set_page_config(page_title="The Cost of Rebuilding", layout="wide")
st.title("🏗️ The Cost of Rebuilding: Estimate Comparison")

carrier_df, contractor_df = load_mock_data()

# Summary Metrics
col1, col2, col3 = st.columns(3)
carrier_total = (carrier_df['Qty'] * carrier_df['Price']).sum()
contractor_total = (contractor_df['Qty'] * contractor_df['Price']).sum()
diff = contractor_total - carrier_total

col1.metric("Carrier Estimate", f"${carrier_total:,.2f}")
col2.metric("Contractor Bid", f"${contractor_total:,.2f}", f"-${diff:,.2f}", delta_color="inverse")
col3.metric("Potential Supplement Value", "$450.00", help="Items found in contractor bid missing from carrier scope.")

# Comparison Logic
st.subheader("Line-Item Variance Analysis")
comparison_results = []

for _, con_row in contractor_df.iterrows():
    match_desc = find_best_match(con_row['Description'], carrier_df['Description'].tolist())
    
    if match_desc:
        car_row = carrier_df[carrier_df['Description'] == match_desc].iloc[0]
        variance = (con_row['Qty'] * con_row['Price']) - (car_row['Qty'] * car_row['Price'])
        status = "⚠️ Variance" if variance != 0 else "✅ Match"
    else:
        variance = con_row['Qty'] * con_row['Price']
        status = "🚨 Missing from Carrier"

    comparison_results.append({
        "Contractor Item": con_row['Description'],
        "Carrier Item": match_desc if match_desc else "NOT FOUND",
        "Contractor Total": con_row['Qty'] * con_row['Price'],
        "Variance": variance,
        "Status": status
    })

# Display Table
res_df = pd.DataFrame(comparison_results)

def color_variance(val):
    color = 'red' if val > 0 else 'green'
    return f'color: {color}'

st.dataframe(res_df.style.applymap(color_variance, subset=['Variance']))

# Supplement Engine Suggestions
st.sidebar.header("Supplement Engine")
st.sidebar.info("Suggested items based on roofing code requirements:")
st.sidebar.checkbox("Step Flashing (Omitted)", value=True)
st.sidebar.checkbox("High Profile Ridge Cap", value=False)
