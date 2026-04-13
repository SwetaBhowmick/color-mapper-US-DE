import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import deepl

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="US-DE Color Mapper", layout="wide")

st.title("🎨 US → DE Color Mapping Tool (Clean + Accurate)")

# -------------------------------
# Helper Function (CLEAN TEXT)
# -------------------------------
def clean_text(text):
    if pd.isna(text):
        return None
    return " ".join(str(text).strip().split()).lower()

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

    us_col = st.selectbox("Select US Color Column", columns)
    de_col = st.selectbox("Select DE Color Column", columns)

    if st.button("🔍 Run Mapping"):

        st.info("Translating German → English using DeepL...")

        # -------------------------------
        # Step 1: Preserve Original DE
        # -------------------------------
        df["DE_Original"] = df[de_col]

        # -------------------------------
        # Step 2: Translate ONLY unique values
        # -------------------------------
        unique_de = df[de_col].dropna().unique()

        translation_map = {}
        for de in unique_de:
            try:
                translated = translator.translate_text(
                    str(de),
                    target_lang="EN-US"
                ).text
                translation_map[de] = translated
            except:
                translation_map[de] = None

        df["DE_Translated"] = df[de_col].map(translation_map)

        # -------------------------------
        # Step 3: Clean text for matching
        # -------------------------------
        df["US_Clean"] = df[us_col].apply(clean_text)
        df["DE_Translated_Clean"] = df["DE_Translated"].apply(clean_text)

        # -------------------------------
        # Step 4: Fuzzy Matching
        # -------------------------------
        mapping = {}

        us_values = df["US_Clean"].dropna().unique()
        de_values = df["DE_Translated_Clean"].dropna().unique()

        for us in us_values:
            try:
                match, score, _ = process.extractOne(
                    us,
                    de_values,
                    scorer=fuzz.token_sort_ratio
                )
                mapping[us] = match if score > 70 else None
            except:
                mapping[us] = None

        # -------------------------------
        # Step 5: Apply Mapping
        # -------------------------------
        df["Mapped_DE_Clean"] = df["US_Clean"].map(mapping)

        # -------------------------------
        # Step 6: Map back to ORIGINAL DE
        # -------------------------------
        reverse_map = {
            clean_text(v): k for k, v in translation_map.items() if v is not None
        }

        df["Mapped_DE_Original"] = df["Mapped_DE_Clean"].map(reverse_map)

        # -------------------------------
        # Output
        # -------------------------------
        st.success("✅ Mapping Completed Successfully!")

        st.subheader("Final Output")
        st.dataframe(df)

        # -------------------------------
        # Download File
        # -------------------------------
        output_file = "mapped_colors.xlsx"
        df.to_excel(output_file, index=False)

        with open(output_file, "rb") as f:
            st.download_button(
                label="📥 Download Mapped Excel",
                data=f,
                file_name="mapped_colors.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
