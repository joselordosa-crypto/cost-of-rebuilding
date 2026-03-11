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
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    all_rows.extend(table)
        df = pd.DataFrame(all_rows)
        df = df.dropna(how='all').reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return pd.DataFrame()

# --- Sidebar: File Uploads ---
st.sidebar.header("1. Upload Estimates")
carrier_file = st.sidebar.file_uploader("Carrier PDF", type=["pdf"])
contractor_file = st.sidebar.file_uploader("Contractor PDF", type=["pdf"])

# --- Main Logic ---
if carrier_file and contractor_file:
    df_car = extract_data(carrier_file)
    df_con = extract_data(contractor_file)

    if not df_car.empty and not df_con.empty:
        st.success("✅ Files Uploaded Successfully")

        # --- Step 2: Column Selection ---
        st.header("2. Map Your Columns")
        st.info("Select which columns contain the Item Descriptions and the Total Prices.")
        
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Carrier Column Mapping")
            car_desc_col = st.selectbox("Carrier: Description", options=df_car.columns, key="car_desc")
            car_price_col = st.selectbox("Carrier: Total Price", options=df_car.columns, index=min(len(df_car.columns)-1, 1), key="car_price")
            st.write("Preview:", df_car[[car_desc_col, car_price_col]].head(3))

        with col2:
            st.subheader("Contractor Column Mapping")
            con_desc_col = st.selectbox("Contractor: Description", options=df_con.columns, key="con_desc")
            con_price_col = st.selectbox("Contractor: Total Price", options=df_con.columns, index=min(len(df_con.columns)-1, 1), key="con_price")
            st.write("Preview:", df_con[[con_desc_col, con_price_col]].head(3))

        # --- Step 3: Run Analysis ---
        st.divider()
        if st.button("🚀 Run Comparison Analysis"):
            comparison_results = []
            
            carrier_items = df_car[car_desc_col].astype(str).tolist()
            
            for _, con_row in df_con.iterrows():
                con_desc = str(con_row[con_desc_col])
                con_price = str(con_row[con_price_col])
                
                best_match = None
                highest_score = 0
                for car_item in carrier_items:
                    score = get_similarity(con_desc, car_item)
                    if score > highest_score:
                        highest_score = score
                        best_match = car_item
                
                if highest_score > 0.65:
                    status = "✅ Match"
                    ref = best_match
                else:
                    status = "🚨 Missing"
                    ref = "Potential Supplement"

                comparison_results.append({
                    "Contractor Item": con_desc,
                    "Price": con_price,
                    "Status": status,
                    "Carrier Reference": ref,
                    "Confidence": f"{int(highest_score * 100)}%"
                })

            res_df = pd.DataFrame(comparison_results)
            st.header("Discrepancy Report")
            
            def highlight_missing(s):
                return ['background-color: #ffcccc' if v == "🚨 Missing" else '' for v in s]

            st.table(res_df.style.apply(highlight_missing, subset=['Status']))
    else:
        st.error("Could not find readable tables in one or both PDFs. Please check the file format.")

elif carrier_file or contractor_file:
    st.info("Please upload both files to enable column mapping.")
