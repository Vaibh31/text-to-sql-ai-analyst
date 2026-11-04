from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

response = llm.invoke("Write a SQL query to count all rows in a table called orders. Return only the SQL.")
print(response.content)