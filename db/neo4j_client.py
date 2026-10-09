from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()  

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([URI, USERNAME, PASSWORD]):
    raise RuntimeError("Missing Neo4j credentials in .env")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def test_connection():
    with driver.session() as session:
        result = session.run("RETURN 'Connection successful!' AS message")
        for record in result:
            print(record["message"])


def create_query_node(query_id, raw_sql, operation):
    with driver.session() as session:
        session.run(
            "CREATE (q:Query {id: $id, raw_sql: $sql, operation: $op})",
            id=query_id, sql=raw_sql, op=operation
        )
        print(f"Created Query node: {query_id}")


import uuid
from datetime import datetime

def add_query_to_graph(raw_sql, operation, table, columns):
    query_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    with driver.session() as session:
        # Step A: create the Query node (always new)
        session.run(
            "CREATE (q:Query {id: $id, raw_sql: $sql, operation: $op, timestamp: $ts})",
            id=query_id, sql=raw_sql, op=operation, ts=timestamp
        )

        # Step B: ensure the Table node exists (reuse if already there)
        session.run(
            "MERGE (t:Table {name: $table})",
            table=table
        )

        # Step C: connect Query -> Table
        session.run(
            """
            MATCH (q:Query {id: $id}), (t:Table {name: $table})
            CREATE (q)-[:TOUCHES]->(t)
            """,
            id=query_id, table=table
        )

        # Step D: for each column, ensure it exists, then connect Query -> Column
        for col in columns:
            session.run(
                "MERGE (c:Column {name: $col, table_name: $table})",
                col=col, table=table
            )
            session.run(
                """
                MATCH (q:Query {id: $id}), (c:Column {name: $col, table_name: $table})
                CREATE (q)-[:MODIFIES]->(c)
                """,
                id=query_id, col=col, table=table
            )

        print(f"Added query {query_id} to graph: {operation} on {table}, columns: {columns}")


def get_column_history(table, column, limit=10):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (q:Query)-[:MODIFIES]->(c:Column {name: $column, table_name: $table})
            RETURN q.raw_sql AS raw_sql, q.operation AS operation, q.timestamp AS timestamp
            ORDER BY q.timestamp DESC
            LIMIT $limit
            """,
            table=table, column=column, limit=limit
        )
        history = []
        for record in result:
            history.append({
                "raw_sql": record["raw_sql"],
                "operation": record["operation"],
                "timestamp": record["timestamp"]
            })
        return history


def ensure_has_column_edges():
    with driver.session() as session:
        session.run(
            """
            MATCH (t:Table), (c:Column {table_name: t.name})
            MERGE (t)-[:HAS_COLUMN]->(c)
            """
        )