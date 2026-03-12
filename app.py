import streamlit as st
import pandas as pd
import pdfplumber
import openai
import re

# --- Page Config ---
st.set_page_config(page_title="Vantix AI Scope Engine", layout="wide")
st.title("🏗️ Vantix Appraisal & Supplement Engine")

# --- 1. THE TRANSLATION DICTIONARY ---
TRANSLATION_DICT = {
    "Final cleaning -construction": "Final Clean",
    "Final Clean, Per SF": "Final Clean",
    "Construction Clean": "Final Clean",
    "CLNR": "Cleaning",
    "CLN": "Cleaning",
    "RFG": "Roofing", 
    "3ARSH": "3-Tab Shingles", 
    "LAMSH": "Laminated Shingles",
    "COMP": "Composition Shingles",
    "DRIP": "Drip Edge",
    "R&R": "Remove and Replace",
    "D&R": "Detach and Reset",
    "PER SF": "",
    "CONSTRUCTION": ""
}

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
    if st.button("🚀 Run AI Analysis"):
        with st.spinner("Analyzing and separating code upgrades..."):
            carrier_text = extract_text(carrier_file)
            contractor_text = extract_text(contractor_file)

            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""
            Act as an Insurance Appraiser. Compare these estimates and provide TWO separate tables.

            TABLE 1: GENERAL DISCREPANCIES
            Include items that exist in both but have price/qty differences, or standard labor items missing from the carrier.
            Columns: Item | Contractor $ | Carrier $ | Difference ($) | Reason

            TABLE 2: CODE UPGRADES & SUPPLEMENTS
            Include items required by building code or manufacturer specs that the carrier OMITTED (e.g., Drip Edge, Ice & Water, Shingle Starter, Ridge Vents, Flashings).
            Columns: Supplement Item | Estimated Cost ($) | Code/Requirement Note

            CARRIER ESTIMATE:
            {carrier_text[:6000]}

            CONTRACTOR ESTIMATE:
            {contractor_text[:6000]}
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            full_report = response.choices[0].message.content

            # --- Logic to extract the dollar gap for the header ---
            diff_amounts = re.findall(r'\|\s*[^|]*\|\s*[^|]*\|\s*[^|]*\|\s*([\d,]+\.?\d*)\s*\|', full_report)
            total_gap = 0
            for amt in diff_amounts:
                try:
                    total_gap += float(amt.replace(',', ''))
                except:
                    continue

            # --- Results Display ---
            st.divider()
            st.metric(label="Total Potential Appraisal Amount", value=f"${total_gap:,.2f}")
            
            # Split the report by the table headers defined in the prompt
            if "TABLE 2" in full_report:
                parts = full_report.split("TABLE 2")
                st.header("General Discrepancy Report")
                st.markdown(parts[0].replace("TABLE 1:", ""))
                
                st.divider()
                st.header("✨ Potential Supplement & Code Upgrade Chart")
                st.markdown(parts[1].replace("CODE UPGRADES & SUPPLEMENTS:", ""))
            else:
                st.markdown(full_report)

elif not api_key:
    st.warning("Please enter your OpenAI API Key.")
