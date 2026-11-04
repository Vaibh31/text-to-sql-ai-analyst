# Step 1: Extract Schema
# Step 1: Extract Schema
import sqlite3
import json

db_path = "northwind.db"

def extract_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    schema = {}
    for table_name in tables:
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        schema[table_name] = [col[1] for col in cursor.fetchall()]

    conn.close()
    return json.dumps(schema)


# for field_info in inspector.get_columns('customers'):
#     print(field_info)


# Step 2: Text to SQL (DeepSeek with groq)

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import re

load_dotenv()
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

def text_to_sql(schema, prompt):
    SYSTEM_PROMPT = """You are an expert SQL generator. Given a database schema and a user question, write a valid SQLite query that answers it.
Wrap table or column names that contain spaces in double quotes, e.g. "Order Details".
Return ONLY the SQL query. No explanation, no markdown, no code fences."""

    USER_PROMPT = """Schema:
{schema}

Question: {user_prompt}

SQL Query:"""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT),
    ])
    chain = prompt_template | llm
    response = chain.invoke({"schema": schema, "user_prompt": prompt}).content

    # Clean up the output so only the SQL is left
    cleaned = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
    cleaned = cleaned.replace("```sql", "").replace("```", "").strip()
    return cleaned

# Step 3: Run SQL on Database (read-only)
def run_sql(db_path, query):
    # Guardrail: only allow SELECT queries
    if not query.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)  # opens the DB in read-only mode
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return columns, rows

# Quick test
if __name__ == "__main__":
    schema = extract_schema(db_path)
    sql = text_to_sql(schema, "Who are the top 5 customers by total order value?")
    print("SQL:", sql)
    columns, rows = run_sql(db_path, sql)
    print(columns, rows)