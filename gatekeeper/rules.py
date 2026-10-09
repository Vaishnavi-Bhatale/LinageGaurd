import sqlglot
from sqlglot import exp

SENSITIVE_COLUMNS = ["marks", "salary", "credit_limit"]

def extract_signals(sql, operation, table, columns):
    parsed = sqlglot.parse_one(sql)

    signals = {
        "operation": operation,
        "table": table,
        "columns": columns,
        "has_where_clause": False,
        "touches_sensitive_column": False,
        "operation_risk_weight": 0,
    }

    where_clause = parsed.args.get("where")
    signals["has_where_clause"] = where_clause is not None

    signals["touches_sensitive_column"] = any(
        col in SENSITIVE_COLUMNS for col in columns
    )

    weight_map = {"DELETE": 3, "UPDATE": 2, "INSERT": 1, "SELECT": 0}
    signals["operation_risk_weight"] = weight_map.get(operation, 1)

    return signals