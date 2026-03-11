import streamlit as st
import pandas as pd
import pdfplumber

# --- The App Header ---
st.set_page_config(page_title="Vantix Scope Engine", layout="wide")
st.title("🏗️ The Cost of Rebuilding")
st.subheader("Compare Carrier Estimates vs. Contractor Bids")

# --- File Uploader Section ---
st.sidebar.header("Upload Files")
carrier_file = st.sidebar.file_uploader("Upload Carrier PDF (Xactimate/Symbility)", type=["pdf"])

# --- The "Brain": Extracting Data from the PDF ---
def extract_pdf_data(uploaded_file):
    all_data = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                # This turns the PDF table into a list we can work with
                all_data.extend(table)
    return pd.DataFrame(all_data)

# --- App Logic ---
if carrier_file is not None:
    st.success(f"Loaded: {carrier_file.name}")
    
    # Run the extraction
    raw_data = extract_pdf_data(carrier_file)
    
    # Show the raw data so you can see it working
    st.write("### Data Extracted from PDF:")
    st.dataframe(raw_data)
    
    # Placeholder for the Comparison Logic (from previous steps)
    st.info("Next Step: The app will now match these lines against your contractor bid.")
else:
    st.warning("Please upload a Carrier Estimate PDF in the sidebar to begin.")
    
    # Show how it looks with demo data if no file is uploaded
    st.write("---")
    st.write("### How it works:")
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)
    st.write("1. Upload your Carrier PDF.\n2. Upload your Contractor Estimate.\n3. See the red/green variance report instantly.")
