import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import deepl
import unicodedata
import re

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="SE-NL Color Mapper", layout="wide")

st.title("🎨 SE → NL Color Mapping Tool (Accurate + Accent Safe + Clean Output)")

# -------------------------------
# Helper Functions
# -------------------------------

# Clean ONLY for matching (not for output)
def clean_text(text):
    if pd.isna(text):
        return None
    return " ".join(str(text).strip().split()).lower()

# Remove accents for matching only
def remove_accents(text):
    if text is None:
        return None
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )

# Normalize (used ONLY for comparison)
def normalize(text):
    cleaned = clean_text(text)
    if cleaned is None:
        return None
    return remove_accents(cleaned)

# Extract numbers (important for accuracy like "Blue 2")
def extract_numbers(text):
    if text is None:
        return ""
    return " ".join(re.findall(r'\d+', str(text)))

# -------------------------------
# Inputs
# -------------------------------
auth_key = st.text_input("Enter DeepL API Key", type="password")
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

# -------------------------------
# Main Logic
# -------------------------------
if uploaded_file and auth_key:

    translator = deepl.Translator(auth_key)

    df = pd.read_excel(uploaded_file)

    st.subheader("Preview Data")
    st.dataframe(df.head())

    columns = df.columns.tolist()

    se_col = st.selectbox("Select SE Column (Swedish)", columns)
    nl_col = st.selectbox("Select NL Column (Dutch)", columns)

    if st.button("🔍 Run Mapping"):

        st.info("Translating Swedish → Dutch using DeepL...")

        # -------------------------------
        # Step 1: Preserve Original NL
        # -------------------------------
        df["NL_Original"] = df[nl_col]

        # -------------------------------
        # Step 2: Translate SE → NL
        # -------------------------------
        unique_se = df[se_col].dropna().unique()

        translation_map = {}
        for se in unique_se:
            try:
                translated = translator.translate_text(
                    str(se),
                    target_lang="NL"
                ).text
                translation_map[se] = translated
            except:
                translation_map[se] = None

        df["SE_Translated_NL"] = df[se_col].map(translation_map)

        # -------------------------------
        # Step 3: Normalize for matching
        # -------------------------------
        df["SE_Norm"] = df["SE_Translated_NL"].apply(normalize)
        df["NL_Norm"] = df[nl_col].apply(normalize)

        df["SE_Num"] = df["SE_Translated_NL"].apply(extract_numbers)
        df["NL_Num"] = df[nl_col].apply(extract_numbers)

        # -------------------------------
        # Step 4: Smart Matching (text + number)
        # -------------------------------
        mapping = {}

        se_values = df["SE_Norm"].dropna().unique()
        nl_values = df["NL_Norm"].dropna().unique()

        for se in se_values:
            best_match = None
            best_score = 0

            for nl in nl_values:
                score = fuzz.token_sort_ratio(se, nl)

                # Boost score if numbers match
                se_num = extract_numbers(se)
                nl_num = extract_numbers(nl)

                if se_num and nl_num and se_num == nl_num:
                    score += 10

                if score > best_score:
                    best_score = score
                    best_match = nl

            mapping[se] = best_match if best_score > 75 else None

        # -------------------------------
        # Step 5: Apply Mapping
        # -------------------------------
        df["Mapped_NL_Norm"] = df["SE_Norm"].map(mapping)

        # -------------------------------
        # Step 6: Map back to ORIGINAL NL
        # -------------------------------
        reverse_map = {}

        for orig in df[nl_col].dropna().unique():
            norm = normalize(orig)
            if norm not in reverse_map:
                reverse_map[norm] = orig  # keep ORIGINAL formatting

        df["Mapped_NL_Original"] = df["Mapped_NL_Norm"].map(reverse_map)

        # -------------------------------
        # Output
        # -------------------------------
        st.success("✅ Mapping Completed Successfully!")

        st.subheader("Final Output")
        st.dataframe(df)

        # -------------------------------
        # Download
        # -------------------------------
        output_file = "SE_NL_mapped.xlsx"
        df.to_excel(output_file, index=False)

        with open(output_file, "rb") as f:
            st.download_button(
                label="📥 Download Mapped Excel",
                data=f,
                file_name="SE_NL_mapped.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
