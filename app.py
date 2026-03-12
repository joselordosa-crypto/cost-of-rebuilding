import streamlit as st
import pandas as pd
import pdfplumber
from difflib import SequenceMatcher

# --- Page Config ---
st.set_page_config(page_title="Vantix Scope Engine", layout="wide")
st.title("🏗️ The Cost of Rebuilding")
st.write("Aggressive extraction mode enabled: Reading all tables from all pages.")

# --- Helper Functions ---
def get_similarity(a, b):
    return SequenceMatcher(None, str(a).upper(), str(b).upper()).ratio()

def extract_data(uploaded_file):
    """Robust extraction for PDFs and CSVs"""
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    
    all_rows = []
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                # 'extract_tables' (plural) gets EVERYTHING on the page
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        all_rows.extend(table)
        
        df = pd.DataFrame(all_rows)
        # Drop rows that are completely empty
        df = df.dropna(how='all').reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return pd.DataFrame()

# --- Sidebar ---
st.sidebar.header("1. Upload Files")
carrier_file = st.sidebar.file_uploader("Carrier Estimate (PDF or CSV)", type=["pdf", "csv"])
contractor_file = st.sidebar.file_uploader("Contractor Bid (PDF or CSV)", type=["pdf", "csv"])

if carrier_file and contractor_file:
    df_car = extract_data(carrier_file)
    df_con = extract_data(contractor_file)

    if not df_car.empty and not df_con.empty:
        st.success(f"Extracted {len(df_car)} rows from Carrier and {len(df_con)} rows from Contractor.")

        # --- Step 2: Column Selection ---
        st.header("2. Map Your Columns")
        st.info("Since PDFs have many columns, pick the one that contains the item descriptions.")
        
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Carrier Column Mapping")
            car_desc_col = st.selectbox("Carrier: Description", options=df_car.columns, key="car_desc")
            car_price_col = st.selectbox("Carrier: Price", options=df_car.columns, index=min(len(df_car.columns)-1, 1), key="car_price")
            st.write("First 5 rows:", df_car[[car_desc_col]].head(5))

        with col2:
            st.subheader("Contractor Column Mapping")
            con_desc_col = st.selectbox("Contractor: Description", options=df_con.columns, key="con_desc")
            con_price_col = st.selectbox("Contractor: Price", options=df_con.columns, index=min(len(df_con.columns)-1, 1), key="con_price")
            st.write("First 5 rows:", df_con[[con_desc_col]].head(5))

        # --- Step 3: Run Analysis ---
        if st.button("🚀 Run Full Comparison"):
            results = []
            # Fuzzy match every contractor line against the carrier list
            car_list = df_car[car_desc_col].astype(str).tolist()
            
            for _, con_row in df_con.iterrows():
                c_text = str(con_row[con_desc_col])
                c_price = str(con_row[con_price_col])
                
                # Basic filter: Skip very short rows (likely page headers/junk)
                if len(c_text) < 5: continue 

                best_match = "No Match Found"
                top_score = 0
                for item in car_list:
                    score = get_similarity(c_text, item)
                    if score > top_score:
                        top_score = score
                        best_match = item
                
                status = "✅ Match" if top_score > 0.6 else "🚨 Missing / Supplement"
                
                results.append({
                    "Contractor Item": c_text,
                    "Price": c_price,
                    "Match Status": status,
                    "Closest Carrier Match": best_match,
                    "Match Score": f"{int(top_score*100)}%"
                })

            st.header("Comparison Results")
            res_df = pd.DataFrame(results)
            st.dataframe(res_df, use_container_width=True)
    else:
        st.error("One of the files appears to be empty or unreadable.")

elif carrier_file or contractor_file:
    st.info("Waiting for both files to begin.")
