import streamlit as st
import pandas as pd
import pdfplumber
import re
from difflib import SequenceMatcher

# --- Page Config ---
st.set_page_config(page_title="Vantix Scope Engine", layout="wide")
st.title("🏗️ The Cost of Rebuilding")
st.write("Smart Filtering: Only comparing actual line items and ignoring headers/addresses.")

# --- Helper Functions ---
def get_similarity(a, b):
    return SequenceMatcher(None, str(a).upper(), str(b).upper()).ratio()

def is_valid_line_item(line):
    """
    Returns True if the line looks like an actual estimate line item.
    Checks for: Starting with a number, containing units (SQ, LF, EA), or action words.
    """
    line = line.strip()
    # 1. Check if it starts with a number (e.g., '1. ' or '10. ')
    starts_with_num = re.match(r'^\d+\.', line)
    
    # 2. Check for common insurance units
    has_units = any(unit in line for unit in [' SQ ', ' LF ', ' EA ', ' SF ', ' UNIT '])
    
    # 3. Check for action keywords
    has_keywords = any(word in line.upper() for word in ['REMOVE', 'REPLACE', 'R&R', 'DETACH', 'RESET', 'PRIME', 'PAINT'])
    
    # If it meets at least two of these criteria, it's likely a real line item
    score = sum([bool(starts_with_num), has_units, has_keywords])
    return score >= 2

def extract_clean_data(uploaded_file):
    all_lines = []
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        # APPLY THE SMART FILTER HERE
                        if is_valid_line_item(line):
                            all_lines.append(line.strip())
        
        return pd.DataFrame(all_lines, columns=["Estimate Line"])
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return pd.DataFrame()

# --- Sidebar ---
st.sidebar.header("1. Upload Estimates")
carrier_file = st.sidebar.file_uploader("Carrier Estimate (PDF)", type=["pdf"])
contractor_file = st.sidebar.file_uploader("Contractor Bid (PDF)", type=["pdf"])

if carrier_file and contractor_file:
    df_car = extract_clean_data(carrier_file)
    df_con = extract_clean_data(contractor_file)

    if not df_car.empty and not df_con.empty:
        st.success(f"Cleaned Data: Found {len(df_car)} Carrier items and {len(df_con)} Contractor items.")

        # --- Step 2: Run Analysis ---
        st.divider()
        if st.button("🚀 Run Smart Comparison"):
            results = []
            carrier_text_list = df_car["Estimate Line"].tolist()
            
            for _, con_row in df_con.iterrows():
                con_line = str(con_row["Estimate Line"])
                
                best_match = "No Match Found"
                top_score = 0
                
                for car_line in carrier_text_list:
                    score = get_similarity(con_line, car_line)
                    if score > top_score:
                        top_score = score
                        best_match = car_line
                
                status = "✅ Match" if top_score > 0.55 else "🚨 Potential Supplement"
                
                results.append({
                    "Contractor Scope Line": con_line,
                    "Status": status,
                    "Carrier Match": best_match if top_score > 0.55 else "N/A",
                    "Similarity": f"{int(top_score*100)}%"
                })

            res_df = pd.DataFrame(results)
            
            # Use a more readable table display
            st.header("Discrepancy Report")
            
            def highlight_rows(row):
                if row['Status'] == "🚨 Potential Supplement":
                    return ['background-color: #ffe6e6'] * len(row)
                return [''] * len(row)

            st.dataframe(res_df.style.apply(highlight_rows, axis=1), use_container_width=True)
    else:
        st.error("No valid line items found. Ensure the PDF is a digital estimate and not a scan.")

elif carrier_file or contractor_file:
    st.info("Upload both files to start the smart scan.")
    
