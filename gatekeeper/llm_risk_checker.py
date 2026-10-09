import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def check_risk(new_query, history, signals):
    history_text = "\n".join(
        f"- [{h['operation']}] {h['raw_sql']} (at {h['timestamp']})"
        for h in history
    ) or "No prior history for this column."

    prompt = f"""
You are a database security assistant protecting against risky or accidental SQL changes.

Rule-based signals detected for the new query:
- Has WHERE clause: {signals['has_where_clause']}
- Touches a sensitive column: {signals['touches_sensitive_column']}
- Operation type: {signals['operation']} (base risk weight: {signals['operation_risk_weight']}/3)

Past history for this column (most recent first):
{history_text}

New incoming query:
{new_query}

Judge whether this new query is risky, considering both the signals above and
whether it's consistent with past patterns. A missing WHERE clause or touching a
sensitive column is not automatically risky — judge it in context.

Respond in EXACTLY this format, nothing else:
LABEL: <safe|risky>
REASON: <one or two sentence explanation>
"""

    response = model.generate_content(prompt)
    return _parse_response(response.text)


def _parse_response(text):
    label_match = re.search(r"LABEL:\s*(safe|risky)", text, re.IGNORECASE)
    reason_match = re.search(r"REASON:\s*(.+)", text, re.IGNORECASE | re.DOTALL)

    return {
        "label": label_match.group(1).lower() if label_match else "unknown",
        "reason": reason_match.group(1).strip() if reason_match else text.strip()
    }