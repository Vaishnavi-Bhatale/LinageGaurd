import sqlglot
from sqlglot import exp

def parse_query(sql):
    parsed = sqlglot.parse_one(sql)
    operation = type(parsed).__name__.upper()

    result = {
        "raw_sql": sql,
        "operation": operation,
        "table": None,
        "columns": []
    }

    if operation == "UPDATE":
        table = parsed.find(exp.Table)
        result["table"] = table.name

        set_expressions = parsed.args.get("expressions")
        result["columns"] = [e.this.name for e in set_expressions]

    elif operation == "INSERT":
        schema = parsed.args.get("this")
        result["table"] = schema.this.name
        result["columns"] = [col.name for col in schema.expressions]
        
    elif operation == "DELETE":
        result["table"] = parsed.find(exp.Table).name
        # a DELETE removes whole rows, so no specific columns are "modified"
        result["columns"] = []

    elif operation == "SELECT":
        tables = [t.name for t in parsed.find_all(exp.Table)]
        result["table"] = tables[0] if tables else None
        result["columns"] = sorted({c.name for c in parsed.find_all(exp.Column)})

    else:
        raise ValueError(f"Unsupported operation: {operation}")
    return result