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

    return result