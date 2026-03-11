import streamlit as st
import pandas as pd
import pdfplumber

# --- The App Header ---
st.set_page_config(page_title="Vantix Scope Engine", layout="wide")
st.title("🏗️ The Cost of Rebuilding")
st.write("Upload both estimates to identify discrepancies.")

# --- File Uploader Sidebar ---
st.sidebar.header("Step 1: Upload Estimates")

# Uploader 1: Carrier
carrier_file = st.sidebar.file_uploader("1. Carrier Estimate (PDF)", type=["pdf"])

# Uploader 2: Contractor
contractor_file = st.sidebar.file_uploader("2. Contractor Bid (PDF)", type=["pdf"])

# --- The Extraction Engine ---
def extract_data(uploaded_file):
    all_rows = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                all_rows.extend(table)
    return pd.DataFrame(all_rows)

# --- Main Interface Logic ---
if carrier_file and contractor_file:
    st.success("✅ Both files received!")
    
    # Create two columns to show the files side-by-side
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Carrier Data")
        df_carrier = extract_data(carrier_file)
        st.dataframe(df_carrier, height=300)
        
    with col2:
        st.subheader("Contractor Data")
        df_contractor = extract_data(contractor_file)
        st.dataframe(df_contractor, height=300)

    # --- Step 2: Run Comparison ---
    st.divider()
    if st.button("🚀 Run Comparison Analysis"):
        st.balloons()
        st.header("Comparison Report")
        st.info("The app is now looking for matching line items between the two files...")
        # (This is where the Fuzzy Matching logic from earlier will live)

elif carrier_file or contractor_file:
    st.info("Waiting for the second file... Please upload both to begin the analysis.")
else:
    st.warning("Please upload the Carrier PDF and the Contractor PDF in the sidebar.")
