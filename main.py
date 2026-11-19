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
BLOCKED_WORDS = ["insert", "update", "delete", "drop", "alter", "create",
                 "truncate", "attach", "detach", "pragma", "vacuum", "reindex"]


def check_query(query):
    """Guardrail: allow only a single read-only query (SELECT, or WITH ... SELECT)."""
    # Remove comments and a trailing semicolon before checking
    sql = re.sub(r"--.*?$", " ", query, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL).strip().rstrip(";").strip()
    # Ignore text inside quotes, so a value like 'Drop Shipping' doesn't trigger a block
    no_strings = re.sub(r"'[^']*'", "''", sql)
    words = re.findall(r"[a-z_]+", no_strings.lower())

    if not words or words[0] not in ("select", "with"):
        raise ValueError("Only SELECT queries are allowed.")
    if ";" in no_strings:
        raise ValueError("Only one query at a time is allowed.")
    blocked = [w for w in BLOCKED_WORDS if w in words]
    if blocked:
        raise ValueError(f"Blocked keyword in query: {blocked[0].upper()}")
    return sql


def run_sql(db_path, query):
    query = check_query(query)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)  # second safety net: the DB is opened read-only
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