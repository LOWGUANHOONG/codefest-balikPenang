from jamaibase import JamAI, types as t
import os
import re
from config import PROJECT_ID, API_KEY

os.environ["JAMAI_API_KEY"] = API_KEY
os.environ["JAMAI_PROJECT_ID"] = PROJECT_ID
jamai = JamAI(project_id=PROJECT_ID, token=API_KEY)

TABLE_ID = "Contract_Generator"

def generate_corrected_contract(contract_text: str, language: str = "en") -> str:
    # Simple prompt passing data only
    target_lang = "Bahasa Melayu" if language == 'ms' else "English"
    prompt = f"Target Language: {target_lang}\n\nContract:\n{contract_text}"

    try:
        response = jamai.table.add_table_rows(
            table_type=t.TableType.ACTION,
            request=t.MultiRowAddRequest(
                table_id=TABLE_ID,
                data=[{"question": prompt}],
                stream=False
            )
        )

        if response.rows:
            row = response.rows[0]
            # Find output column
            for col in ["answer"]:
                if col in row.columns:
                    text = row.columns[col].text
                    # Clean Markdown
                    text = re.sub(r'^```(markdown)?', '', text.strip())
                    return re.sub(r'```$', '', text).strip()
            
            # Fallback
            return list(row.columns.values())[-1].text
            
        return "Error: No response."

    except Exception as e:
        return f"Generation Error: {str(e)}"