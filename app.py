import streamlit as st
import pandas as pd
import pdfplumber
from difflib import SequenceMatcher

# --- Page Config & Branding ---
st.set_page_config(page_title="Vantix Scope Engine", layout="wide")
st.title("🏗️ The Cost of Rebuilding")
st.write("Match estimates and identify missing supplement items.")

# --- Helper Functions ---
def get_similarity(a, b):
    return SequenceMatcher(None, str(a).upper(), str(b).upper()).ratio()

def extract_data(uploaded_file):
    all_rows = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                all_rows.extend(table)
    df = pd.DataFrame(all_rows)
    # Clean up: Remove rows that are entirely empty
    df = df.dropna(how='all').reset_index(drop=True)
    return df

# --- Sidebar: File Uploads ---
st.sidebar.header("1. Upload Estimates")
carrier_file = st.sidebar.file_uploader("Carrier PDF", type=["pdf"])
contractor_file = st.sidebar.file_uploader("Contractor PDF", type=["pdf"])

# --- Main Logic ---
if carrier_file and contractor_file:
    df_car = extract_data(carrier_file)
    df_con = extract_data(contractor_file)

    st.success("✅ Files Uploaded Successfully")

    # --- Step 2: Column Selection ---
    st.header("2. Map Your Columns")
    st.info("Select which columns contain the Item Descriptions and the Total Prices.")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Carrier Column Mapping")
        car_desc_col = st.selectbox("Carrier: Description Column", options=df_car.columns, index=0)
        car_price_col = st.selectbox("Carrier: Total Price Column", options=df_car.columns, index=min(len(df_car.columns)-1, 1))

    with col2:
        st.subheader("Contractor Column Mapping")
        con_desc_col = st.selectbox("Contractor: Description Column", options=df_con.columns, index=0)
        con_price_col = st.selectbox("Contractor: Total Price Column", options=df_con.columns, index=min(len(df_con.columns)-1, 1))

    # --- Step 3: Run Analysis ---
    st.divider()
    if st.button("🚀 Run Comparison Analysis"):
        comparison_results = []
        
        # Get list of carrier items for matching
        carrier_items = df_car[car_desc_col].astype(str).tolist()
        
        for _, con_row in df_con.iterrows():
            con_desc = str(con_row[con_desc_col])
            con_price = str(con_row[con_price_col])
            
            # Find best fuzzy match
            best_match = None
            highest_score = 0
            for car_item in carrier_items:
                score = get_similarity(con_desc, car_item)
                if score > highest_score:
                    highest_score = score
                    best_match = car_item
            
            # Identify Status
            if highest_score > 0.65:
                status = "✅ Match"
                ref = best_match
            else:
                status = "🚨 Missing"
                ref = "Potential Supplement"

            comparison_results.append({
                "Contractor Item
