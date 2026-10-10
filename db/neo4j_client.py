from neo4j import GraphDatabase
import os
import uuid
from datetime import datetime
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


def add_query_to_graph(raw_sql, operation, table, columns):
    query_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    # Fixed constants (never user input), because Cypher can't parameterize relationship types
    edge = "READS" if operation == "SELECT" else "MODIFIES"

    with driver.session() as session:
        # Query node (always new)
        session.run(
            "CREATE (q:Query {id: $id, raw_sql: $sql, operation: $op, timestamp: $ts})",
            id=query_id, sql=raw_sql, op=operation, ts=timestamp
        )

        # Table node (reuse if it exists) + Query -> Table
        session.run("MERGE (t:Table {name: $table})", table=table)
        session.run(
            """
            MATCH (q:Query {id: $id}), (t:Table {name: $table})
            CREATE (q)-[:TOUCHES]->(t)
            """,
            id=query_id, table=table
        )

        # Column nodes + Table -> Column + Query -> Column
        for col in columns:
            session.run(
                """
                MATCH (t:Table {name: $table})
                MERGE (c:Column {name: $col, table_name: $table})
                MERGE (t)-[:HAS_COLUMN]->(c)
                """,
                col=col, table=table
            )
            session.run(
                f"""
                MATCH (q:Query {{id: $id}}), (c:Column {{name: $col, table_name: $table}})
                CREATE (q)-[:{edge}]->(c)
                """,
                id=query_id, col=col, table=table
            )

        # A DELETE removes whole rows, so it modifies every known column of the table
        if operation == "DELETE":
            session.run(
                """
                MATCH (q:Query {id: $id}), (c:Column {table_name: $table})
                CREATE (q)-[:MODIFIES]->(c)
                """,
                id=query_id, table=table
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
        return [dict(r) for r in result]


def get_table_history(table, limit=10):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (q:Query)-[:TOUCHES]->(t:Table {name: $table})
            RETURN q.raw_sql AS raw_sql, q.operation AS operation, q.timestamp AS timestamp
            ORDER BY q.timestamp DESC
            LIMIT $limit
            """,
            table=table, limit=limit
        )
        return [dict(r) for r in result]


def ensure_has_column_edges():
    with driver.session() as session:
        session.run(
            """
            MATCH (t:Table), (c:Column {table_name: t.name})
            MERGE (t)-[:HAS_COLUMN]->(c)
            """
        )