import streamlit as st
import pandas as pd
import pdfplumber
import openai
import re

# --- Page Config ---
st.set_page_config(page_title="Vantix AI Scope Engine", layout="wide")
st.title("🏗️ Vantix Appraisal & Supplement Engine")

# --- API Setup ---
api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")

def extract_text(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# --- Sidebar ---
st.sidebar.header("1. Upload Estimates")
carrier_file = st.sidebar.file_uploader("Carrier Estimate (PDF)", type=["pdf"])
contractor_file = st.sidebar.file_uploader("Contractor Bid (PDF)", type=["pdf"])

if carrier_file and contractor_file and api_key:
    if st.button("🚀 Run AI Comparison"):
        with st.spinner("AI is calculating the appraisal gap..."):
            carrier_text = extract_text(carrier_file)
            contractor_text = extract_text(contractor_file)

            client = openai.OpenAI(api_key=api_key)
            
            # THE PROMPT: We ask for a specific format so we can extract the numbers later
            prompt = f"""
            Compare these two insurance estimates. 
            Identify every item in the CONTRACTOR estimate that is MISSING or UNDERPAID in the CARRIER estimate.
            
            Format your response EXACTLY as a Markdown table with these columns:
            Item | Status | Difference ($) | Reason
            
            For the 'Difference ($)' column, provide ONLY the number (e.g., 1250.50).
            
            CARRIER ESTIMATE:
            {carrier_text[:5000]}
            
            CONTRACTOR ESTIMATE:
            {contractor_text[:5000]}
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini", # Cost-saving model
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.choices[0].message.content

            # --- Calculation Logic ---
            # We look for dollar amounts in the AI's table to create a total
            all_amounts = re.findall(r'\|\s*([\d,]+\.?\d*)\s*\|', result_text)
            total_gap = 0
            for amt in all_amounts:
                try:
                    total_gap += float(amt.replace(',', ''))
                except:
                    continue

            # --- Results Display ---
            st.divider()
            
            # Big Metric Card
            st.metric(label="Total Potential Appraisal Amount", value=f"${total_gap:,.2f}")
            
            st.header("Detailed Line-Item Discrepancies")
            st.markdown(result_text)

elif not api_key:
    st.warning("Please enter your OpenAI API Key in the sidebar.")
