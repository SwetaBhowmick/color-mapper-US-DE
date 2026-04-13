import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import deepl

st.set_page_config(page_title="US-DE Color Mapper", layout="wide")

st.title("🎨 US → DE Color Mapping Tool")

# 🔑 DeepL API Key input
auth_key = st.text_input("Enter DeepL API Key", type="password")

# 📂 Upload file
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])


if uploaded_file and auth_key:

    translator = deepl.Translator(auth_key)

    df = pd.read_excel(uploaded_file)

    st.subheader("Preview Data")
    st.dataframe(df.head())

    columns = df.columns.tolist()

    us_col = st.selectbox("Select US Color Column", columns)
    de_col = st.selectbox("Select DE Color Column", columns)

    if st.button("🔍 Run Mapping"):

        st.info("Translating German colors to English...")

        # ✅ Translate ONLY unique values (saves API usage)
        unique_de = df[de_col].dropna().unique()

        translation_map = {}
        for de in unique_de:
            try:
                translated = translator.translate_text(str(de), target_lang="EN-US").text
                translation_map[de] = translated
            except:
                translation_map[de] = None

        df["DE_Translated"] = df[de_col].map(translation_map)

        # 🔍 Fuzzy match US with translated DE
        mapping = {}

        us_colors = df[us_col].astype(str).unique()
        de_translated = df["DE_Translated"].dropna().astype(str).unique()

        for us in us_colors:
            try:
                match, score, _ = process.extractOne(
                    us,
                    de_translated,
                    scorer=fuzz.token_sort_ratio
                )
                mapping[us] = match if score > 70 else None
            except:
                mapping[us] = None

        df["Mapped_DE"] = df[us_col].map(mapping)

        st.success("✅ Mapping Completed with DeepL!")

        st.dataframe(df)

        # 📥 Download file
        output_file = "mapped_colors.xlsx"
        df.to_excel(output_file, index=False)

        with open(output_file, "rb") as f:
            st.download_button(
                label="📥 Download Mapped Excel",
                data=f,
                file_name="mapped_colors.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
