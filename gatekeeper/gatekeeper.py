from gatekeeper.rules import extract_signals
from gatekeeper.llm_risk_checker import check_risk
from db.neo4j_client import get_column_history

def evaluate_query(parsed):
    sql = parsed["raw_sql"]
    operation = parsed["operation"]
    table = parsed["table"]
    columns = parsed["columns"]

    signals = extract_signals(sql, operation, table, columns)

    all_history = []
    for col in columns:
        all_history.extend(get_column_history(table, col))

    llm_result = check_risk(sql, all_history, signals)

    decision = "BLOCK" if llm_result["label"] == "risky" else "APPROVE"

    return {
        "decision": decision,
        "label": llm_result["label"],
        "reason": llm_result["reason"],
        "signals": signals
    }