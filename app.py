import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import deepl
import unicodedata

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="SE-FR Color Mapper", layout="wide")

st.title("🎨 SE → FR Color Mapping Tool (Accurate + Accent Safe)")

# -------------------------------
# Helper Functions
# -------------------------------

# Clean spaces + lowercase
def clean_text(text):
    if pd.isna(text):
        return None
    return " ".join(str(text).strip().split()).lower()

# Remove accents (é → e, ü → u)
def remove_accents(text):
    if text is None:
        return None
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )

# Full normalization (spaces + lowercase + accents)
def normalize(text):
    cleaned = clean_text(text)
    if cleaned is None:
        return None
    return remove_accents(cleaned)

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
    fr_col = st.selectbox("Select FR Column (French)", columns)

    if st.button("🔍 Run Mapping"):

        st.info("Translating Swedish → French using DeepL...")

        # -------------------------------
        # Step 1: Preserve Original FR
        # -------------------------------
        df["FR_Original"] = df[fr_col]

        # -------------------------------
        # Step 2: Translate SE → FR (unique values)
        # -------------------------------
        unique_se = df[se_col].dropna().unique()

        translation_map = {}
        for se in unique_se:
            try:
                translated = translator.translate_text(
                    str(se),
                    target_lang="FR"
                ).text
                translation_map[se] = translated
            except:
                translation_map[se] = None

        df["SE_Translated_FR"] = df[se_col].map(translation_map)

        # -------------------------------
        # Step 3: Normalize text
        # -------------------------------
        df["SE_Norm"] = df["SE_Translated_FR"].apply(normalize)
        df["FR_Norm"] = df[fr_col].apply(normalize)

        # -------------------------------
        # Step 4: Fuzzy Matching
        # -------------------------------
        mapping = {}

        se_values = df["SE_Norm"].dropna().unique()
        fr_values = df["FR_Norm"].dropna().unique()

        for se in se_values:
            try:
                match, score, _ = process.extractOne(
                    se,
                    fr_values,
                    scorer=fuzz.token_sort_ratio
                )
                mapping[se] = match if score > 75 else None
            except:
                mapping[se] = None

        # -------------------------------
        # Step 5: Apply Mapping
        # -------------------------------
        df["Mapped_FR_Norm"] = df["SE_Norm"].map(mapping)

        # -------------------------------
        # Step 6: Map back to ORIGINAL FR
        # -------------------------------
        reverse_map = {
            normalize(v): k for k, v in zip(df[fr_col], df[fr_col])
        }

        df["Mapped_FR_Original"] = df["Mapped_FR_Norm"].map(reverse_map)

        # -------------------------------
        # Output
        # -------------------------------
        st.success("✅ Mapping Completed Successfully!")

        st.subheader("Final Output")
        st.dataframe(df)

        # -------------------------------
        # Download File
        # -------------------------------
        output_file = "SE_FR_mapped.xlsx"
        df.to_excel(output_file, index=False)

        with open(output_file, "rb") as f:
            st.download_button(
                label="📥 Download Mapped Excel",
                data=f,
                file_name="SE_FR_mapped.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
