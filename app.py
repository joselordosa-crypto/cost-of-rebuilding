import streamlit as st
import pandas as pd
import pdfplumber
import openai
import re

# --- Page Config ---
st.set_page_config(page_title="Vantix AI Scope Engine", layout="wide")
st.title("🏗️ Vantix Appraisal & Supplement Engine")

# --- 1. EXPANDED TRANSLATION DICTIONARY ---
# These are the standard Xactimate/Symbility category codes.
TRANSLATION_DICT = {
    # Cleaning & Labor Synonyms
    "Final cleaning -construction": "Final Clean",
    "Final Clean, Per SF": "Final Clean",
    "Construction Clean": "Final Clean",
    "CLNR": "Cleaning",
    "CLN": "Cleaning",
    
    # Roofing Synonyms
    "RFG": "Roofing", 
    "3ARSH": "3-Tab Shingles", 
    "LAMSH": "Laminated Shingles",
    "COMP": "Composition Shingles",
    "DRIP": "Drip Edge",
    
    # General Logic
    "R&R": "Remove and Replace",
    "D&R": "Detach and Reset",
    "PER SF": "", # Remove 'Per SF' so it doesn't confuse the matcher
    "CONSTRUCTION": "" # Remove 'Construction' to get to the core word 'Clean'
}
    
    # General Logic
    "Final cleaning -construction": "Final Clean"
    "PER SF": "", # Remove 'Per SF' so it doesn't confuse the matcher
}

# --- 2. COMMON SUPPLEMENT CHECKLIST ---
# The AI will now specifically look for these commonly missed items.
SUPPLEMENT_CHECKLIST = [
    "High-Profile Ridge Caps", "Drip Edge (Code Required)", "Ice & Water Shield",
    "Step Flashing", "Furnace Vent/Rain Caps", "Valley Metal", "Pipe Jacks",
    "OSB Sheathing", "Steep Charges", "High Roof Charges"
]

def translate_codes(text):
    for code, full_name in TRANSLATION_DICT.items():
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
                text += translate_codes(content) + "\n"
    return text

# --- Sidebar ---
st.sidebar.header("1. Upload Estimates")
carrier_file = st.sidebar.file_uploader("Carrier Estimate (PDF)", type=["pdf"])
contractor_file = st.sidebar.file_uploader("Contractor Bid (PDF)", type=["pdf"])

if carrier_file and contractor_file and api_key:
    if st.button("🚀 Run AI Comparison"):
        with st.spinner("Analyzing scopes and hunting for supplements..."):
            carrier_text = extract_text(carrier_file)
            contractor_text = extract_text(contractor_file)

            client = openai.OpenAI(api_key=api_key)
            
            # THE PROMPT: Explicitly mentioning the supplement list
            prompt = f"""
            As an expert Insurance Appraiser, reconcile these estimates. 
            
            CRITICAL: 
            1. Use 'Semantic Matching': Match items by intent/scope even if words differ (e.g. 'Drip' vs 'Drip Edge').
            2. Supplement Hunter: Specifically check if these items are in the Contractor bid but MISSING from the Carrier: {', '.join(SUPPLEMENT_CHECKLIST)}.
            3. Accuracy: If the Carrier quantity is lower than the Contractor, list the dollar difference.

            Output ONLY a Markdown table with these columns:
            Item | Contractor $ | Carrier $ | Difference ($) | Status (Match/Underpaid/Missing) | Reason
            
            CARRIER ESTIMATE:
            {carrier_text[:6000]}
            
            CONTRACTOR ESTIMATE:
            {contractor_text[:6000]}
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are a professional insurance appraiser. Your math must be exact."},
                          {"role": "user", "content": prompt}]
            )

            result_text = response.choices[0].message.content

            # --- Calculation Logic ---
            all_amounts = re.findall(r'\|\s*([\d,]+\.?\d*)\s*\|\s*[\w\s/]+Match', result_text) # Only grab non-matches
            # For simplicity, we extract the 'Difference' column values
            diff_amounts = re.findall(r'\|\s*[^|]*\|\s*[^|]*\|\s*([\d,]+\.?\d*)\s*\|', result_text)
            
            total_gap = 0
            for amt in diff_amounts:
                try:
                    total_gap += float(amt.replace(',', ''))
                except:
                    continue

            # --- Results Display ---
            st.divider()
            st.metric(label="Total Potential Appraisal Amount", value=f"${total_gap:,.2f}")
            st.header("Discrepancy & Supplement Report")
            st.markdown(result_text)

elif not api_key:
    st.warning("Please enter your OpenAI API Key.")
