# termination_checker.py
import json
import ast
import os
import re
from config import PROJECT_ID, API_KEY
from jamaibase import JamAI, types as t

# ------------------ JamAI Setup ------------------
# Ensure credentials are loaded from your config file
os.environ["JAMAI_API_KEY"] = API_KEY
os.environ["JAMAI_PROJECT_ID"] = PROJECT_ID

jamai = JamAI(project_id=PROJECT_ID, token=API_KEY)

# --- CONFIGURATION ---
TABLE_ID = "Termination&Compensation_Generator"

# ------------------ TERMINATION CHECKER ------------------
def check_termination(employee_data: dict, reason: str) -> dict:
    """
    Sends employee data and termination reason to JamAI and returns a DICT with:
    - legal_to_terminate (bool)
    - required_notice_period (float)
    - severance_pay (float)
    - unused_leave_pay (float)
    - legal_reasons_if_cannot (str)
    """

    print(f"🚀 Sending termination check to JamAI for {employee_data.get('name')}...")

    # --- Prepare input text for AI ---
    input_text = f"""
Employee data: {employee_data}
Termination reason: {reason}
Refer to knowledge tables: epf&socso_law, employment_act_1955, industrial_relations_act_1967
Return as JSON object with:
legal_to_terminate, required_notice_period, severance_pay, unused_leave_pay, legal_reasons_if_cannot
"""

    try:
        # --- Send to JamAI Action Table ---
        response = jamai.table.add_table_rows(
            table_type=t.TableType.ACTION,
            request=t.MultiRowAddRequest(
                table_id=TABLE_ID,
                data=[{"input": input_text}],
                stream=False
            )
        )

        if not response.rows:
            print("⚠️ No rows returned from JamAI")
            return {}

        # 1. Extract output text
        row = response.rows[0]
        answer_text = ""
        for col in ["output", "AI", "answer", "final_answer"]:
            if col in row.columns:
                answer_text = row.columns[col].text
                break
        if not answer_text:
            answer_text = list(row.columns.values())[-1].text

        # 2. Clean JSON formatting
        clean_text = re.sub(r'```json|```', '', answer_text).strip()
        clean_text = re.sub(r'\[@[^\]]*\]', '', clean_text)  # remove citations

        # 3. Parse JSON
        start = clean_text.find('{')
        end = clean_text.rfind('}')
        if start != -1 and end != -1:
            clean_text = clean_text[start : end + 1]
            try:
                data = json.loads(clean_text)
            except:
                try:
                    data = ast.literal_eval(clean_text)
                except:
                    print("❌ JSON Parse Failed")
                    return {}

            # Ensure all keys exist
            defaults = {
                "legal_to_terminate": False,
                "required_notice_period": 0,
                "severance_pay": 0,
                "unused_leave_pay": 0,
                "legal_reasons_if_cannot": ""
            }
            for key, val in defaults.items():
                if key not in data:
                    data[key] = val

            return data

        return {}

    except Exception as e:
        print(f"🔥 Critical API Error: {e}")
        return {}
