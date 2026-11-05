import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from main import extract_schema, text_to_sql, run_sql, db_path

st.set_page_config(page_title="Text-to-SQL AI Analyst", page_icon="🧠")

st.markdown("""
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"] {
    background: transparent;
}
#bg-video {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    object-fit: cover;
    z-index: -2;
}
#bg-overlay {
    position: fixed;
    inset: 0;
    background: rgba(10, 15, 30, 0.65);
    z-index: -1;
}
</style>
<video id="bg-video" autoplay muted loop playsinline>
    <source src="app/static/bg.mp4" type="video/mp4">
</video>
<div id="bg-overlay"></div>
""", unsafe_allow_html=True)

st.title("Text-to-SQL Assistant")
st.caption("Ask questions about the Northwind business database (customers, orders, products, employees) in plain English.")
EXAMPLES = [
    "Top 5 customers by total order value",
    "Which employee generated the most sales revenue?",
    "How many orders were placed each year?",
    "Which product categories sell the most units?",
]

st.write("**Try an example:**")
cols = st.columns(2)
for i, example in enumerate(EXAMPLES):
    if cols[i % 2].button(example, width="stretch"):
        st.session_state.question = example
        st.session_state.auto_run = True

question = st.text_input(
    "Or ask your own question",
    key="question",
    placeholder="e.g. Which country has the most customers?",
)

run_clicked = st.button("Run", type="primary")

if (run_clicked or st.session_state.pop("auto_run", False)) and question:
    schema = extract_schema(db_path)
    sql = text_to_sql(schema, question)
    st.subheader("Generated SQL")
    st.code(sql, language="sql")

    try:
        columns, rows = run_sql(db_path, sql)
        df = pd.DataFrame(rows, columns=columns)

        st.subheader("Result")
        st.markdown(df.to_html(index=False), unsafe_allow_html=True)

        # Auto chart: one text column + one number column
        if len(df.columns) >= 2 and len(df) > 1:
            label_col = df.columns[0]
            number_cols = df.select_dtypes(include="number").columns
            value_col = number_cols[-1] if len(number_cols) else None

            if value_col is not None and value_col != label_col:
                st.subheader("Chart")
                fig, ax = plt.subplots(figsize=(8, 4))
                fig.patch.set_alpha(0)
                ax.set_facecolor("none")
                ax.bar(df[label_col].astype(str), df[value_col], color="#60a5fa")
                ax.set_xlabel(label_col, color="white")
                ax.set_ylabel(value_col, color="white")
                ax.tick_params(colors="white")
                plt.xticks(rotation=45, ha="right")
                for spine in ax.spines.values():
                    spine.set_color("#475569")
                fig.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

    except Exception as e:
        st.error(f"Error: {e}")

st.markdown("""
<style>
.custom-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    padding: 10px 0;
    text-align: center;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.6);
    background: rgba(10, 15, 30, 0.85);
    z-index: 100;
}
.custom-footer a {
    color: #60a5fa;
    text-decoration: none;
}
[data-testid="stMainBlockContainer"] {
    padding-bottom: 70px;
}
</style>
<div class="custom-footer">
    Built with LangChain · Groq (GPT-OSS 120B) · SQLite · Streamlit &nbsp;|&nbsp;
    <a href="https://github.com/Vaibh31/text-to-sql-ai-analyst" target="_blank">View code on GitHub</a>
</div>
""", unsafe_allow_html=True)