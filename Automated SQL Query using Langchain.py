
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.vectorstores import FAISS

from langchain_core.example_selectors import (
    SemanticSimilarityExampleSelector
)
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    MessagesPlaceholder
)


# ==========================================
# 1. ENVIRONMENT CONFIGURATION
# ==========================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not configured.")

# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

required_db_config = [
    DB_HOST,
    DB_USER,
    DB_PASSWORD,
    DB_NAME
]

if not all(required_db_config):
    raise ValueError("Database configuration is incomplete.")


# ==========================================
# 2. LLM INITIALIZATION
# ==========================================

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=OPENAI_API_KEY
)

embeddings = OpenAIEmbeddings(
    api_key=OPENAI_API_KEY
)


# ==========================================
# 3. DATABASE CONNECTION
# ==========================================

database_url = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=3600
)

db = SQLDatabase(
    engine,
    sample_rows_in_table_info=2
)


# ==========================================
# 4. DATABASE SCHEMA EXTRACTION
# ==========================================

def extract_schema(engine):
    """
    Extract database schema, including:
    - Table names
    - Column names and data types
    - Primary keys
    - Foreign keys
    """

    inspector = inspect(engine)
    schema_info = []

    for table_name in inspector.get_table_names():

        schema_info.append(f"Table: {table_name}")

        # Extract columns
        columns = inspector.get_columns(table_name)

        for column in columns:
            schema_info.append(
                f"  - {column['name']} ({column['type']})"
            )

        # Extract primary keys
        pk = inspector.get_pk_constraint(table_name)

        if pk and pk.get("constrained_columns"):
            pk_columns = ", ".join(
                pk["constrained_columns"]
            )

            schema_info.append(
                f"  - Primary Key: {pk_columns}"
            )

        # Extract foreign keys
        foreign_keys = inspector.get_foreign_keys(
            table_name
        )

        for fk in foreign_keys:
            fk_columns = ", ".join(
                fk["constrained_columns"]
            )

            referenced_table = fk["referred_table"]

            referenced_columns = ", ".join(
                fk["referred_columns"]
            )

            schema_info.append(
                f"  - Foreign Key: {fk_columns} "
                f"references {referenced_table}"
                f"({referenced_columns})"
            )

    return "\n".join(schema_info)


schema = extract_schema(engine)

print("Database schema successfully extracted.")


# ==========================================
# 5. FEW-SHOT EXAMPLES
# ==========================================

examples = [
    {
        "input": "How many products are available?",
        "query": """
            SELECT COUNT(product_id)
            FROM product_inventory
        """
    },
    {
        "input": "Which product has the highest stock?",
        "query": """
            SELECT product_name, stock_quantity
            FROM product_inventory
            ORDER BY stock_quantity DESC
            LIMIT 1
        """
    },
    {
        "input": "What are the total sales in October 2024?",
        "query": """
            SELECT SUM(total_amount)
            FROM sales_transactions
            WHERE transaction_date >= '2024-10-01'
            AND transaction_date < '2024-11-01'
        """
    },
    {
        "input": "Compare sales between September and October 2024",
        "query": """
            SELECT
                MONTH(transaction_date) AS month,
                SUM(total_amount) AS total_sales
            FROM sales_transactions
            WHERE transaction_date >= '2024-09-01'
            AND transaction_date < '2024-11-01'
            GROUP BY MONTH(transaction_date)
            ORDER BY month
        """
    },
    {
        "input": "Which category has the highest revenue?",
        "query": """
            SELECT
                p.category,
                SUM(s.total_amount) AS revenue
            FROM sales_transactions s
            JOIN product_inventory p
                ON s.product_id = p.product_id
            GROUP BY p.category
            ORDER BY revenue DESC
            LIMIT 1
        """
    }
]


# ==========================================
# 6. SEMANTIC SIMILARITY EXAMPLE SELECTOR
# ==========================================

example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    embeddings,
    FAISS,
    k=3,
    input_keys=["input"]
)


# ==========================================
# 7. FEW-SHOT PROMPT TEMPLATE
# ==========================================

example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{query}")
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_selector=example_selector,
    example_prompt=example_prompt,
    input_variables=["input"]
)


# ==========================================
# 8. SQL AGENT PROMPT
# ==========================================

system_message = """
You are an AI assistant designed to retrieve information
from a relational SQL database.

Your responsibilities:

1. Understand the user's natural language question.
2. Identify relevant database tables and columns.
3. Generate accurate SQL queries.
4. Use JOIN operations when necessary.
5. Validate query logic before execution.
6. Return clear and relevant answers.

IMPORTANT RULES:

- Only execute SELECT queries.
- Never INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.
- Never modify database structures or records.
- Use only tables and columns available in the database.
- Do not invent database values.
- Handle dates and filtering conditions carefully.
- If the question is ambiguous, ask for clarification.
- Provide answers based on actual query results.
- Respond in the same language as the user.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_message),
    few_shot_prompt,
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")
])


# ==========================================
# 9. CREATE SQL AGENT
# ==========================================

agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    prompt=prompt,
    agent_type="openai-tools",
    verbose=True,
    max_iterations=8,
    handle_parsing_errors=True
)


# ==========================================
# 10. QUERY EXECUTION
# ==========================================

def ask_database(question: str):
    """
    Process natural language questions
    through the SQL Agent.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    response = agent_executor.invoke({
        "input": question
    })

    return response["output"]


# ==========================================
# 11. APPLICATION ENTRY POINT
# ==========================================

if __name__ == "__main__":

    print("\nAI-Powered SQL Agent")
    print("Type 'exit' to stop.\n")

    try:
        while True:

            question = input("You: ").strip()

            if question.lower() == "exit":
                print("Session ended.")
                break

            try:
                answer = ask_database(question)

                print("\nAI:", answer)
                print("-" * 50)

            except Exception as error:
                print(f"\nError: {error}")

    finally:
        engine.dispose()
