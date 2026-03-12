import streamlit as st
import pandas as pd
import pdfplumber
import openai

# --- Page Config ---
st.set_page_config(page_title="Vantix AI Scope Engine", layout="wide")
st.title("🤖 AI-Powered Scope Comparison")

# --- API Setup ---
# You will enter your key in the sidebar of the running app
api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")

def extract_text(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# --- Sidebar ---
st.sidebar.header("1. Upload Estimates")
carrier_file = st.sidebar.file_uploader("Carrier PDF", type=["pdf"])
contractor_file = st.sidebar.file_uploader("Contractor PDF", type=["pdf"])

if carrier_file and contractor_file and api_key:
    if st.button("🚀 Run AI Analysis"):
        with st.spinner("AI is analyzing scopes..."):
            carrier_text = extract_text(carrier_file)
            contractor_text = extract_text(contractor_file)

            # --- The AI Prompt ---
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""
            You are an expert Insurance Adjuster and Appraiser. 
            I will provide you with two estimates. 
            Identify every line item in the CONTRACTOR estimate that is MISSING or UNDER-SCOPED in the CARRIER estimate.
            
            Format your answer as a table with columns: 
            Item Description | Contractor Qty | Carrier Qty | Reason for Discrepancy (e.g. Missing, Lower Quantity, Code Upgrade)
            
            CARRIER ESTIMATE:
            {carrier_text[:4000]} # Limit text to fit AI window
            
            CONTRACTOR ESTIMATE:
            {contractor_text[:4000]}
            """

            response = client.chat.completions.create(
                model="gpt-4o", # Or gpt-3.5-turbo for cheaper/faster
                messages=[{"role": "user", "content": prompt}]
            )

            st.header("AI Discrepancy Report")
            st.markdown(response.choices[0].message.content)

elif not api_key:
    st.warning("Please enter your OpenAI API Key in the sidebar to use the AI logic.")
