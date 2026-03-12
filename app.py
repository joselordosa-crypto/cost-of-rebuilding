import streamlit as st
import pandas as pd
import pdfplumber
from difflib import SequenceMatcher

# --- Page Config ---
st.set_page_config(page_title="Vantix Scope Engine", layout="wide")
st.title("🏗️ The Cost of Rebuilding")
st.write("Deep Scan Mode: Reading all text layers from the estimate.")

# --- Helper Functions ---
def get_similarity(a, b):
    return SequenceMatcher(None, str(a).upper(), str(b).upper()).ratio()

def extract_all_text_lines(uploaded_file):
    """Reads every line of text from the PDF, even if not in a table"""
    all_lines = []
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                # Extract words and group them into lines by their vertical position
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        # Only keep lines that look like they have data (longer than 10 chars)
                        if len(line.strip()) > 10:
                            all_lines.append([line.strip()])
        
        df = pd.DataFrame(all_lines, columns=["Full Line Text"])
        return df
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return pd.DataFrame()

# --- Sidebar ---
st.sidebar.header("1. Upload Estimates")
carrier_file = st.sidebar.file_uploader("Carrier Estimate (PDF)", type=["pdf"])
contractor_file = st.sidebar.file_uploader("Contractor Bid (PDF)", type=["pdf"])

if carrier_file and contractor_file:
    df_car = extract_all_text_lines(carrier_file)
    df_con = extract_all_text_lines(contractor_file)

    if not df_car.empty and not df_con.empty:
        st.success(f"Successfully read {len(df_car)} lines from Carrier and {len(df_con)} lines from Contractor.")

        # --- Step 2: Run Analysis ---
        st.header("2. Discrepancy Analysis")
        if st.button("🚀 Compare All Lines"):
            results = []
            carrier_text_list = df_car["Full Line Text"].tolist()
            
            for _, con_row in df_con.iterrows():
                con_line = str(con_row["Full Line Text"])
                
                best_match = "No Match Found"
                top_score = 0
                
                for car_line in carrier_text_list:
                    score = get_similarity(con_line, car_line)
                    if score > top_score:
                        top_score = score
                        best_match = car_line
                
                # Logic: If similarity is low, it's likely a missing supplement
                status = "✅ Match" if top_score > 0.5 else "🚨 Potential Supplement"
                
                results.append({
                    "Contractor Scope Line": con_line,
                    "Status": status,
                    "Carrier Match": best_match if top_score > 0.5 else "N/A",
                    "Similarity": f"{int(top_score*100)}%"
                })

            res_df = pd.DataFrame(results)
            
            # Displaying the results with coloring
            def color_status(val):
                color = 'red' if val == "🚨 Potential Supplement" else 'green'
                return f'color: {color}'

            st.dataframe(res_df.style.applymap(color_status, subset=['Status']), use_container_width=True)
    else:
        st.error("The app could not find any text in one of these PDFs. Ensure they are not scanned 'images' of documents.")

elif carrier_file or contractor_file:
    st.info("Waiting for both files...")
