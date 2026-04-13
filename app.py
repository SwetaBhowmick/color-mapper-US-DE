import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

st.set_page_config(page_title="US-DE Color Mapper", layout="wide")

st.title("🎨 US → DE Color Mapping Tool")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

def fuzzy_match(us_color, de_list):
    match, score, _ = process.extractOne(us_color, de_list, scorer=fuzz.token_sort_ratio)
    return match if score > 70 else None

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Preview Data")
    st.dataframe(df.head())

    columns = df.columns.tolist()

    us_col = st.selectbox("Select US Color Column", columns)
    de_col = st.selectbox("Select DE Color Column", columns)

    if st.button("🔍 Run Mapping"):

        us_colors = df[us_col].dropna().unique()
        de_colors = df[de_col].dropna().unique()

        mapping = {}

        for us in us_colors:
            if us in de_colors:
                mapping[us] = us
            else:
                mapping[us] = fuzzy_match(us, de_colors)

        df["Mapped_DE_Color"] = df[us_col].map(mapping)

        st.success("✅ Mapping Completed!")

        st.dataframe(df)

        output_file = "mapped_colors.xlsx"
        df.to_excel(output_file, index=False)

        with open(output_file, "rb") as f:
            st.download_button(
                label="📥 Download Mapped Excel",
                data=f,
                file_name="mapped_colors.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
