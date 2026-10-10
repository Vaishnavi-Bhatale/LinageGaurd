from gatekeeper.rules import extract_signals
from gatekeeper.llm_risk_checker import check_risk
from db.neo4j_client import get_column_history, get_table_history


def evaluate_query(parsed):
    sql = parsed["raw_sql"]
    operation = parsed["operation"]
    table = parsed["table"]
    columns = parsed["columns"]

    # Layer 1: rule-based signals
    signals = extract_signals(sql, operation, table, columns)

    # Graph history: table-level for DELETE (no columns), column-level otherwise
    all_history = []
    if operation == "DELETE":
        all_history = get_table_history(table)
    else:
        for col in columns:
            all_history.extend(get_column_history(table, col))

    # Layer 2: LLM judgment
    llm_result = check_risk(sql, all_history, signals)

    # Hard rule: DELETE without WHERE is never allowed, whatever the LLM says
    rule_block = operation == "DELETE" and not signals["has_where_clause"]

    if rule_block:
        decision = "BLOCK"
        reason = "Blocked by rule: DELETE without a WHERE clause would remove every row. " \
                 f"(LLM said: {llm_result['label']} - {llm_result['reason']})"
    elif llm_result["label"] == "risky":
        decision = "BLOCK"
        reason = llm_result["reason"]
    else:
        decision = "APPROVE"
        reason = llm_result["reason"]

    return {
        "decision": decision,
        "label": llm_result["label"],
        "reason": reason,
        "signals": signals,
        "rule_override": rule_block,
    }