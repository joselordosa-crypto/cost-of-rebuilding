import streamlit as st
import pandas as pd
import pdfplumber
from difflib import SequenceMatcher

# --- The App Header ---
st.set_page_config(page_title="Vantix Scope Engine", layout="wide")
st.title("🏗️ The Cost of Rebuilding")
st.write("Detecting discrepancies between Carrier and Contractor estimates.")

# --- Helper Functions ---
def get_similarity(a, b):
    return SequenceMatcher(None, str(a).upper(), str(b).upper()).ratio()

def clean_df(df):
    """Basic cleaning to remove empty rows and headers from PDF tables"""
    df = df.dropna(how='all') # Remove empty rows
    return df.reset_index(drop=True)

# --- File Uploader Sidebar ---
st.sidebar.header("Step 1: Upload Estimates")
carrier_file = st.sidebar.file_uploader("1. Carrier Estimate (PDF)", type=["pdf"])
contractor_file = st.sidebar.file_uploader("2. Contractor Bid (PDF)", type=["pdf"])

def extract_data(uploaded_file):
    all_rows = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                all_rows.extend(table)
    return clean_df(pd.DataFrame(all_rows))

# --- Main Interface Logic ---
if carrier_file and contractor_file:
    st.success("✅ Both files received!")
    
    # Extract data
    df_car = extract_data(carrier_file)
    df_con = extract_data(contractor_file)

    # --- Step 2: Run Comparison ---
    st.divider()
    if st.button("🚀 Run Comparison Analysis"):
        comparison_results = []
        
        # We assume the first column is the Description
        # In a production app, we would use AI to identify columns accurately
        carrier_items = df_car.iloc[:, 0].astype(str).tolist()
        
        for _, con_row in df_con.iterrows():
            con_desc = str(con_row.iloc[0])
            
            # Find the best fuzzy match in the carrier list
            best_match = None
            highest_score = 0
            
            for car_item in carrier_items:
                score = get_similarity(con_desc, car_item)
                if score > highest_score:
                    highest_score = score
                    best_match = car_item
            
            # Decide if it's a match or a missing item (Threshold 0.6)
            if highest_score > 0.6:
                status = "✅ Match Found"
                variance_note = f"Matches: {best_match}"
            else:
                status = "🚨 Missing / Supplement"
                variance_note = "No similar item in Carrier scope"

            comparison_results.append({
                "Contractor Item": con_desc,
                "Status": status,
                "Confidence": f"{int(highest_score * 100)}%",
                "Carrier Reference": variance_note
            })

        # Display results
        res_df = pd.DataFrame(comparison_results)
        
        st.header("Discrepancy Report")
        
        # Color Coding the Status
        def color_status(val):
            color = 'red' if 'Missing' in val else 'green'
            return f'background-color: {color}; color: white'

        st.table(res_df.style.applymap(color_status, subset=['Status']))

elif carrier_file or contractor_file:
    st.info("Waiting for the second file...")
