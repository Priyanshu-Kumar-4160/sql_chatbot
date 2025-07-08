import os
import sqlite3
from dotenv import load_dotenv
from pydantic import BaseModel


from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_community.chat_models import ChatOpenAI
from langgraph.graph import StateGraph

load_dotenv()

# -----------------------------
# 📌 1. LLM setup
# -----------------------------
llm = ChatOpenAI(model="gpt-4", temperature=0)

# -----------------------------
# 📌 2. Prompt for SQL generation
# -----------------------------
PROMPT = PromptTemplate.from_template(
    """Given an input question and a table schema, write an SQL query that answers the question.
    
    Only use the given tables. Do not hallucinate.

    Question: {question}

    Schema:
    {schema}

    SQL Query:"""
)

sql_chain = PROMPT | llm | StrOutputParser()

# -----------------------------
# 📌 3. Load DB schema from sqlite
# -----------------------------
def load_schema_from_sqlite() -> str:
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    schema = ""
    for table in ["chatbot_customer", "chatbot_order"]:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        schema += f"Table: {table}\n"
        for col in columns:
            schema += f"  {col[1]} ({col[2]})\n"
        schema += "\n"
    conn.close()
    return schema.strip()

# -----------------------------
# 📌 4. Nodes for LangGraph
# -----------------------------
def format_input(state):
    user_input = state["user_input"]
    return {"user_input": user_input}


def get_schema(state):
    return {
        **state,
        "schema": load_schema_from_sqlite()
    }

def run_sql_query(state):
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    try:
        cursor.execute(state["sql"])
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
    except Exception as e:
        rows = []
        columns = ["error"]
        print(f"[SQL ERROR] {e}")
    conn.close()
    return {
        **state,
        "rows": rows,
        "columns": columns
    }

def extract_sql_from_response(state):
    # assumes SQL comes after final line break
    sql = state["llm_raw"].strip().split("\n")[-1]
    return {
        **state,
        "sql": sql
    }

def format_output(state):
    return {
        "question": state["user_input"],
        "sql": state["sql"],
        "rows": state["rows"],
        "columns": state["columns"],
        "explanation": state["llm_raw"]
    }

# -----------------------------
# ✅ 5. Define state keys
# -----------------------------
class GraphState(BaseModel):
    user_input: str = ""
    schema: str = ""
    llm_raw: str = ""
    sql: str = ""
    columns: list = []
    rows: list = []


# -----------------------------
# 📦 6. LangGraph flow
# -----------------------------
builder = StateGraph(GraphState)

builder.add_node("input",       RunnableLambda(format_input))
builder.add_node("schema",      RunnableLambda(get_schema))
builder.add_node("generate_sql", sql_chain)
builder.add_node("extract_sql", RunnableLambda(extract_sql_from_response))
builder.add_node("run_sql",     RunnableLambda(run_sql_query))
builder.add_node("format",      RunnableLambda(format_output))

builder.set_entry_point("input")
builder.add_edge("input",        "schema")
builder.add_edge("schema",       "generate_sql")
builder.add_edge("generate_sql", "extract_sql")
builder.add_edge("extract_sql",  "run_sql")
builder.add_edge("run_sql",      "format")
builder.set_finish_point("format")

# 🔁 Final runnable graph
graph = builder.compile()
