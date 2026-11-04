import streamlit as st
import pandas as pd
from main import extract_schema, text_to_sql, run_sql, db_path

st.title("Text-to-SQL Assistant")
st.caption("Ask a question about the Amazon database in plain English.")

question = st.text_input("Your question")

if st.button("Run") and question:
    schema = extract_schema(db_path)
    sql = text_to_sql(schema, question)
    st.subheader("Generated SQL")
    st.code(sql, language="sql")

    try:
        columns, rows = run_sql(db_path, sql)
        st.subheader("Result")
        df = pd.DataFrame(rows, columns=columns)
        st.markdown(df.to_html(index=False), unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")