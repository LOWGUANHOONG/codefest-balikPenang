import json
import ast
import os
import re
from typing import Dict, Any
from config import PROJECT_ID, API_KEY
from jamaibase import JamAI, types as t

# ------------------ JamAI Setup ------------------
os.environ["JAMAI_API_KEY"] = API_KEY
os.environ["JAMAI_PROJECT_ID"] = PROJECT_ID

jamai = JamAI(project_id=PROJECT_ID, token=API_KEY)

# This must match your Table ID in JamAI Base
TABLE_ID = "Contract_Auditor_Full"

def parse_json_safely(text: str) -> Dict[str, Any]:
    """Helper to clean and parse JSON from AI responses."""
    if not text: 
        return {}
    
    # Remove markdown code blocks (```json ... ```)
    clean_text = re.sub(r'```json|```', '', text).strip()
    # Remove citations like [@1]
    clean_text = re.sub(r'\[@[^\]]*\]', '', clean_text)
    
    # Find the JSON object { ... }
    start = clean_text.find('{')
    end = clean_text.rfind('}')
    
    if start != -1 and end != -1:
        json_str = clean_text[start : end + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(json_str)
            except:
                return {}
    return {}

def check_full_contract(contract_text: str) -> Dict[str, Any]:
    """
    Sends text to JamAI and returns a combined dictionary of:
    1. Legal Violations (final_json_report)
    2. Financial Risk Tags (contract_risk)
    3. Employee Facts (employee_data)
    """
    print("🚀 Sending contract to JamAI Auditor...")

    try:
        # 1. Send Request to JamAI Action Table
        response = jamai.table.add_table_rows(
            table_type=t.TableType.ACTION,
            request=t.MultiRowAddRequest(
                table_id=TABLE_ID,
                data=[{"full_contract_text": contract_text}],
                stream=False
            )
        )

        if not response.rows: 
            return {}

        row = response.rows[0]
        
        # 2. Extract Columns (Safe Fetching)
        
        # A. Legal Violations (Try exact name first, then fallbacks)
        raw_report = ""
        if "final_json_report" in row.columns:
            raw_report = row.columns["final_json_report"].text
        
            
        # B. Financial Risk Tags (The simplified prompt output)
        raw_risk = ""
        if "contract_risk" in row.columns:
            raw_risk = row.columns["contract_risk"].text
            
        # C. Employee Data (Salary, Name, etc.)
        raw_facts = ""
        if "employee_data" in row.columns:
            raw_facts = row.columns["employee_data"].text

        # 3. Parse and Combine
        final_data = parse_json_safely(raw_report)
        risk_data = parse_json_safely(raw_risk)
        facts_data = parse_json_safely(raw_facts)

        # Merge them into the structure expected by main.py/core.py
        if not final_data:
            final_data = {"summary": {}, "violations": []}

        # Store with keys that match core.py expectations
        final_data["contract_risk"] = risk_data
        final_data["employee_data"] = facts_data

        print("✅ Data received from JamAI")
        return final_data

    except Exception as e:
        print(f"🔥 Critical API Error: {e}")
        return {}