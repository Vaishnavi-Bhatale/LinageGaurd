from parser import parse_query
from db.neo4j_client import add_query_to_graph
from gatekeeper.gatekeeper import evaluate_query


def process_query(sql):
    try:
        parsed = parse_query(sql)
    except Exception as e:
        print(f"Could not parse this SQL. Error: {e}\n")
        return

    try:
        result = evaluate_query(parsed)
    except Exception as e:
        print(f"Gatekeeper error: {e}\n")
        return

    print("\n" + "=" * 60)
    print("RULE-BASED SIGNALS (Layer 1)")
    print("=" * 60)
    for key, value in result["signals"].items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("LLM-BASED RISK ANALYSIS (Layer 2)")
    print("=" * 60)
    print(f"  Risk Label : {result['label'].upper()}")
    print(f"  Reasoning  : {result['reason']}")

    print("\n" + "=" * 60)
    print("FINAL DECISION")
    print("=" * 60)
    print(f"  >> {result['decision']}")
    print(f"  Rule override: {result['rule_override']}")
    print("=" * 60 + "\n")

    if result["decision"] == "APPROVE":
        add_query_to_graph(
            raw_sql=parsed["raw_sql"],
            operation=parsed["operation"],
            table=parsed["table"],
            columns=parsed["columns"],
        )
        print("Written to lineage graph.\n")
    else:
        print("BLOCKED - not written to the graph.\n")


print("LineageGuard Gatekeeper - type a SQL query, or 'exit' to quit.\n")

while True:
    sql = input("Enter a SQL query: ").strip()

    if sql.lower() in ("exit", "quit", "q"):
        print("Goodbye.")
        break

    if not sql:
        continue  # ignore empty Enter presses

    process_query(sql)