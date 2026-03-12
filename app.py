import streamlit as st
import pandas as pd
import pdfplumber
import openai
import re

# --- Page Config ---
st.set_page_config(page_title="Vantix AI Scope Engine", layout="wide")
st.title("🏗️ Vantix Appraisal & Supplement Engine")

# --- 1. THE TRANSLATION DICTIONARY ---
# You can add new shorthand codes here as you encounter them!
TRANSLATION_DICT = {
    "RFG 3ARSH": "Roofing 3-Tab Shingles",
    "RFG DRIP": "Roofing Drip Edge",
    "RFG 30LB": "Roofing Felt - 30 lb",
    "RFG VAL": "Roofing Valley Metal",
    "DRY 1/2": "Drywall - 1/2 inch",
    "DRY 5/8": "Drywall - 5/8 inch",
    "FCO WD": "Floor Covering - Wood",
    "FNC TRIM": "Finish Carpentry - Trim",
    "DMO GEN": "General Demolition",
    "WTR DRY": "Water Mitigation - Drying",
    "PNTP": "Paint - Prime & Paint",
    # Add as many as you need...
}

def translate_codes(text):
    """Replaces shorthand codes with full descriptions from the dictionary."""
    for code, full_name in TRANSLATION_DICT.items():
        # Using regex to ensure we only replace the exact code word
        text = re.sub(rf'\b{code}\b', full_name, text, flags=re.IGNORECASE)
    return text

# --- API Setup ---
api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")

def extract_text(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                # APPLY TRANSLATION DURING EXTRACTION
                text += translate_codes(content) + "\n"
    return text

# --- Sidebar ---
st.sidebar.header("1. Upload Estimates")
carrier_file = st.sidebar.file_uploader("Carrier Estimate (PDF)", type=["pdf"])
contractor_file = st.sidebar.file_uploader("Contractor Bid (PDF)", type=["pdf"])

if carrier_file and contractor_file and api_key:
    if st.button("🚀 Run AI Comparison"):
        with st.spinner("Translating codes and analyzing..."):
            carrier_text = extract_text(carrier_file)
            contractor_text = extract_text(contractor_file)

            client = openai.OpenAI(api_key=api_key)
            
            # THE PROMPT: Telling the AI we've already helped it with translations
            prompt = f"""
            You are an expert Insurance Appraiser. 
            Compare these two estimates. I have already pre-processed some shorthand codes into full text.
            
            TASK: 
            1. Match items based on the SCOPE of work, even if the wording is slightly different.
            2. Identify items in the CONTRACTOR estimate that are missing or under-calculated in the CARRIER estimate.
            3. If an item is a 'Match', do not list it in the table. ONLY list discrepancies.

            Format as a Markdown table:
            Item | Contractor Value | Carrier Value | Difference ($) | Reason
            
            CARRIER ESTIMATE:
            {carrier_text[:6000]}
            
            CONTRACTOR ESTIMATE:
            {contractor_text[:6000]}
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.choices[0].message.content

            # --- Calculation Logic ---
            all_amounts = re.findall(r'\|\s*([\d,]+\.?\d*)\s*\|', result_text)
            total_gap = 0
            for amt in all_amounts:
                try:
                    total_gap += float(amt.replace(',', ''))
                except:
                    continue

            # --- Results Display ---
            st.divider()
            st.metric(label="Total Potential Appraisal Amount", value=f"${total_gap:,.2f}")
            st.header("Discrepancy Report")
            st.markdown(result_text)

elif not api_key:
    st.warning("Please enter your OpenAI API Key in the sidebar.")
