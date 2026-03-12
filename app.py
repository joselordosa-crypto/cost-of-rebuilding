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
        with st.spinner("Calculating the net discrepancy..."):
            carrier_text = extract_text(carrier_file)
            contractor_text = extract_text(contractor_file)

            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""
            Act as an Insurance Appraiser. Your goal is to find the net financial gap between these two estimates.

            SECTION 1: DISCREPANCY TABLE
            Find items present in BOTH estimates where the Contractor is higher, OR items in the Contractor bid that are standard labor/materials missing from the Carrier.
            Calculate the exact difference for each line.
            Columns: Item | Contractor $ | Carrier $ | Difference ($)

            SECTION 2: SUPPLEMENT & CODE UPGRADES
            List items that are entirely new supplements or code-required upgrades found in the Contractor's scope but absent in the Carrier's.
            Columns: Supplement Item | Estimated Cost ($) | Reason

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

            # --- Calculation Logic for Discrepancy Only ---
            # We split the report to only calculate math from Section 1
            report_sections = full_report.split("SECTION 2")
            discrepancy_section = report_sections[0]
            
            # Find all numbers in the 'Difference' column of Section 1
            diff_amounts = re.findall(r'\|\s*[\d,]+\.?\d*\s*\|\s*[\d,]+\.?\d*\s*\|\s*([\d,]+\.?\d*)\s*\|', discrepancy_section)
            
            total_discrepancy = 0
            for amt in diff_amounts:
                try:
                    total_discrepancy += float(amt.replace(',', ''))
                except:
                    continue

            # --- Results Display ---
            st.divider()
            
            st.metric(label="Total Discrepancy Amount", value=f"${total_discrepancy:,.2f}", 
                      help="The sum of all line-item price and quantity differences.")
            
            st.header("Discrepancy Analysis (Carrier vs. Contractor)")
            st.markdown(discrepancy_section.replace("SECTION 1:", ""))
            
            if len(report_sections) > 1:
                st.divider()
                st.header("✨ Potential Supplement & Code Upgrades")
                st.markdown(report_sections[1].replace("SUPPLEMENT & CODE UPGRADES:", ""))

elif not api_key:
    st.warning("Please enter your OpenAI API Key.")
