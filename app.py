import streamlit as st
import pandas as pd
import pdfplumber
import re
from difflib import SequenceMatcher

# --- Page Config ---
st.set_page_config(page_title="Vantix Scope Engine", layout="wide")
st.title("🏗️ The Cost of Rebuilding")
st.write("V3: Description-Only Matching. Stripping numbers to find better matches.")

# --- Helper Functions ---
def get_similarity(a, b):
    return SequenceMatcher(None, str(a).upper(), str(b).upper()).ratio()

def clean_text_for_matching(text):
    """
    Removes numbers, units, and special characters so we only compare the 'item' itself.
    Turns '1. Remove Shingles 30.00 SQ' into 'REMOVE SHINGLES'
    """
    # Remove numbers and decimals
    text = re.sub(r'\d+\.\d+|\d+', '', text)
    # Remove common units
    for unit in ['SQ', 'LF', 'EA', 'SF', 'UNIT', 'R&R', 'r&r']:
        text = text.replace(unit, '')
    # Remove extra spaces and punctuation
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip().upper()

def is_useful_line(line):
    """A more relaxed filter to ensure we don't skip Carrier items"""
    line = line.strip()
    if len(line) < 15: return False
    # Avoid header/footer common phrases
    ignore_list = ['PAGE', 'ESTIMATE', 'CLAIM', 'INSURED', 'PROPERTY', 'TOTAL', 'DEPRECIATION']
    if any(word in line.upper() for word in ignore_list): return False
    return True

def extract_data(uploaded_file):
    lines = []
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        if is_useful_line(line):
                            lines.append(line.strip())
        return lines
    except Exception as e:
        st.error(f"Error: {e}")
        return []

# --- Sidebar ---
st.sidebar.header("1. Upload Estimates")
carrier_file = st.sidebar.file_uploader("Carrier PDF", type=["pdf"])
contractor_file = st.sidebar.file_uploader("Contractor PDF", type=["pdf"])

if carrier_file and contractor_file:
    car_lines = extract_data(carrier_file)
    con_lines = extract_data(contractor_file)

    if car_lines and con_lines:
        st.success(f"Found {len(car_lines)} potential Carrier items and {len(con_lines)} Contractor items.")
        
        # --- Preview Section (Debug) ---
        with st.expander("🔍 Preview what the app is reading"):
            col1, col2 = st.columns(2)
            col1.write("**Carrier Lines (First 10):**")
            col1.write(car_lines[:10])
            col2.write("**Contractor Lines (First 10):**")
            col2.write(con_lines[:10])

        # --- Step 2: Run Analysis ---
        if st.button("🚀 Run Full Comparison"):
            results = []
            
            # Pre-clean the carrier lines for faster matching
            cleaned_car_data = [{"raw": line, "clean": clean_text_for_matching(line)} for line in car_lines]
            
            for con_raw in con_lines:
                con_clean = clean_text_for_matching(con_raw)
                
                best_match_raw = "N/A"
                top_score = 0
                
                for car_item in cleaned_car_data:
                    score = get_similarity(con_clean, car_item["clean"])
                    if score > top_score:
                        top_score = score
                        best_match_raw = car_item["raw"]
                
                # Threshold check (Lowered to 0.45 because we are matching cleaner text)
                status = "✅ Match" if top_score > 0.45 else "🚨 Potential Supplement"
                
                results.append({
                    "Contractor Line (Full)": con_raw,
                    "Status": status,
                    "Carrier Match Found": best_match_raw if top_score > 0.45 else "No similar item found",
                    "Match Confidence": f"{int(top_score*100)}%"
                })

            st.header("Comparison Results")
            res_df = pd.DataFrame(results)
            
            # Styling
            def highlight_missing(row):
                return ['background-color: #ffe6e6' if row['Status'] == "🚨 Potential Supplement" else ''] * len(row)

            st.dataframe(res_df.style.apply(highlight_missing, axis=1), use_container_width=True)
    else:
        st.error("One of the files is not yielding readable text. Check if it's a scanned image.")
    
