import fitz  # PyMuPDF
import re
import tempfile
import os
from typing import Union
from io import BytesIO

def extract_text_from_pdf(file_source: Union[str, BytesIO]) -> str:
    """
    Extracts text and fixes common PDF spacing/newline issues.
    """
    text = ""
    temp_file_path = None

    try:
        # --- 1. Handle File Input ---
        if isinstance(file_source, str):
            pdf_path = file_source
        elif isinstance(file_source, BytesIO):
            file_source.seek(0)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file_source.read())
                pdf_path = tmp.name
                temp_file_path = tmp.name
        else:
            return ""

        # --- 2. Extract Text Page by Page ---
        with fitz.open(pdf_path) as doc:
            for page in doc:
                # Add a newline after each page to prevent joining words across pages
                text += page.get_text("text") + "\n"

        # --- 3. Smart Cleaning Logic ---
        
        # A. Normalize newlines (handle Windows/Linux differences)
        # Replace \r\n or \r with standard \n
        cleaned_text = text.replace('\r\n', '\n').replace('\r', '\n')

        # B. Fix Hyphenation (Optional but recommended)
        # Example: "Respon- \n sibility" -> "Responsibility"
        cleaned_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', cleaned_text)

        # C. The "Mask & Restore" Strategy
        # 1. Protect real paragraphs (double newlines) by turning them into a special marker
        cleaned_text = re.sub(r'\n\s*\n', '||PARAGRAPH||', cleaned_text)
        
        # 2. Convert remaining single newlines (which are usually line-wraps) into spaces
        # This fixes "Employee\nat" -> "Employee at"
        cleaned_text = cleaned_text.replace('\n', ' ')
        
        # 3. Restore the real paragraphs
        cleaned_text = cleaned_text.replace('||PARAGRAPH||', '\n\n')

        # D. Final Cleanup
        # Remove multiple spaces (e.g., "Employee   at" -> "Employee at")
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
        
        return cleaned_text.strip()

    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)