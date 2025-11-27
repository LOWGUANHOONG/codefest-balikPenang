import sys
import os
import re
from io import BytesIO
import streamlit as st

# Ensure Python can find your subfolder
sys.path.append(os.path.join(os.path.dirname(__file__), "contractChecker"))

from contractChecker.pdf_parser import extract_text_from_pdf
from contractChecker.law_checker import check_full_contract
from contractChecker.generate_new_contract import generate_corrected_contract
from contractChecker.financial_calculator import calculate_liability

# --- PDF Generation Imports ---
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib import colors

# --- Page Configuration ---
st.set_page_config(
    page_title="Malaysian Labour Law Assistant",
    initial_sidebar_state="expanded", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: inherit;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    
    [data-testid="stSidebarNav"]::before {
        content: "Malaysian Labour Law Assistant";
        font-size: 1.5em; /* Matches h1 size */
        text-align: center;
        display: block;
        padding: 15px 0 10px 0;
        font-weight: bold;
    }
    
    [data-testid="stSidebarNav"]::after {
        content: "";
        display: block;
        border-bottom: 1px solid #34495e; 
        margin-bottom: 10px;
    }
    
    [data-testid="stSidebarNav"] > div:first-child > div:first-child {
        display: none;
    }


    [data-testid="stSidebar"] > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) {
        visibility: hidden;
        height: 0px; /* Still collapse height just in case, but rely on visibility */
    }

    .disclaimer {
        background-color: #FFEE8C;
        padding: 15px;
        border-radius: 8px;
        font-size: 0.9em;
        color: #2c3e50;
        border-left: 5px solid #2c3e50;
        margin-top: 20px;
    }
    .disclaimer p, .disclaimer strong {
        font-weight: normal;
        color: #003747;
    }
</style>
""", unsafe_allow_html=True)


# --- Sidebar Setup ---
with st.sidebar:
    st.empty() 
    st.markdown("""
    <div class="disclaimer">
        ⚠️ DISCLAIMER: This tool is for informational purposes only and does not constitute legal advice. 
        Always consult with a qualified legal professional for advice regarding specific legal issues.
    </div>
    """, unsafe_allow_html=True)



def local_detect_language(text):
    """
    Simple detection to switch UI language immediately.
    """
    malay_keywords = ['gaji', 'pekerja', 'majikan', 'cuti', 'kerja', 'bulan', 
                      'hari', 'kontrak', 'penamatan', 'wang', 'bayaran', 'tahun']
    text_lower = text.lower()
    # Check first 1000 chars is enough for UI switching
    malay_count = sum(1 for word in malay_keywords if word in text_lower[:1000])
    return 'ms' if malay_count >= 3 else 'en'

def create_pdf_from_markdown(markdown_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=72, leftMargin=72, 
        topMargin=72, bottomMargin=18
    )
    styles = getSampleStyleSheet()
    
    # Custom Styles
    header_style = ParagraphStyle(
        'CustomHeader', parent=styles['Heading2'],
        fontSize=14, spaceAfter=12, textColor=colors.black, fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        'CustomNormal', parent=styles['Normal'],
        fontSize=11, leading=14, spaceAfter=6, alignment=TA_JUSTIFY
    )

    story = []
    lines = markdown_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
        
        # Detect Markdown Headers (##)
        if line.startswith('##'):
            clean_line = line.replace('#', '').strip()
            story.append(Paragraph(clean_line, header_style))
        
        # Detect Bullets
        elif line.startswith('- ') or line.startswith('* '):
            clean_line = line[2:].strip()
            # Convert bold syntax **text** to HTML <b>text</b>
            formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean_line)
            story.append(Paragraph(f"•  {formatted_line}", normal_style))
        
        # Standard Text
        else:
            formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            story.append(Paragraph(formatted_line, normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Helper: Financial Dashboard Renderer (Optimized Visuals) ---
def render_financial_dashboard(contract_risk, employee_data):
    if not contract_risk and not employee_data:
        return

    st.markdown("---")
    st.subheader("💰 Financial Liability Analysis")

    # 1. Employee Profile (Compact View)
    if employee_data:
        with st.container():
            st.markdown("##### 👤 Extracted Employee Profile")
            # Use columns with captions for a tighter look
            c1, c2, c3, c4 = st.columns(4)
            
            # Extract Data
            name = employee_data.get("employee_name", "Unknown")
            pos = employee_data.get("position_title", "-")
            start = employee_data.get("start_date") or "-"
            
            salary = employee_data.get("basic_salary_monthly")
            try:
                sal_str = f"RM {float(salary):,.2f}" if salary else "RM 0.00"
            except:
                sal_str = str(salary)

            # Render Small Cells
            with c1:
                st.caption("Name")
                st.markdown(f"**{name}**")
            with c2:
                st.caption("Position")
                st.markdown(f"**{pos}**")
            with c3:
                st.caption("Base Salary")
                st.markdown(f"**{sal_str}**")
            with c4:
                st.caption("Start Date")
                st.markdown(f"**{start}**")

    # 2. Top Level Liability Metrics
    if contract_risk:
        st.markdown("") # Spacer
        try:
            likely_total = float(contract_risk.get("total_likely_liability", 0.0))
            worst_total = float(contract_risk.get("total_worst_case_liability", 0.0))
        except:
            likely_total, worst_total = 0.0, 0.0

        k1, k2 = st.columns(2)
        k1.metric("📉 Likely Liability (Compound)", f"RM {likely_total:,.2f}", "Settlement Risk", delta_color="inverse")
        k2.metric("💥 Worst Case (Court Max)", f"RM {worst_total:,.2f}", "Max Penalty", delta_color="inverse")

        # 3. Detailed Breakdown List
        breakdown_list = contract_risk.get("breakdown", [])
        if breakdown_list:
            with st.expander("💸 View Liability Breakdown", expanded=True):
                for item in breakdown_list:
                    # Parse Item format: "⚠️ Type: RM X... | ⛓️ Jail: Z"
                    parts = item.split("|")
                    main_text = parts[0].strip()
                    jail_text = parts[1].strip() if len(parts) > 1 else ""

                    col_text, col_jail = st.columns([0.8, 0.2])
                    col_text.markdown(f"**{main_text}**")
                    
                    if jail_text and "None" not in jail_text:
                        col_jail.error(jail_text.replace("⛓️", "").strip())
                    elif jail_text:
                        col_jail.caption(jail_text)


# --- UI Translations ---
TRANSLATIONS = {
    'en': {
        'title': '🏢 Malaysian Labour Law Assistant',
        'subtitle': '*Validate employment contracts against Employment Act 1955 & Industrial Relations Act 1967*',
        'upload_label': '📎 Upload Employment Contract (PDF)',
        'file_uploaded': '✅ File uploaded:',
        'detected': 'Detected Language: 🇬🇧 English',
        'validate_btn': '🔬 Validate Contract',
        'generate_btn': '📝 Generate Corrected Contract',
        'download_btn': '📥 Download Corrected Contract (PDF)',
        'processing_val': '⏳ Analyzing contract clauses...',
        'processing_gen': '⏳ AI Drafter is rewriting the contract...',
        'processing_pdf': '⏳ Creating formatted PDF...',
        'report_title': '📊 Validation Report',
        'no_violations': '✅ No violations detected! This contract complies with Malaysian labour law.',
        'violations_found': '⚠️ Violations Found',
        'total_clauses': 'Total Clauses',
        'issues_found': 'Clauses with Issues',
        'total_violations': 'Specific Violations',
        'preview_title': '📄 Corrected Contract Preview',
        'confirm_pdf': '✅ Confirm and Generate PDF',
        'success_pdf': '✅ Corrected Contract PDF Generated Successfully!',
        'original_clause': 'Original Clause:',
        'violation_details': 'Violations:',
        'status_label': 'Status',
        'reason_label': 'Reason',
        'corrected_label': 'Correction',
        'status_legal': '✅ Legal',
        'status_illegal': '❌ Illegal',
        'status_missing': '⚪ Not Specified'
    },
    'ms': {
        'title': '🏢 Pembantu Undang-Undang Buruh Malaysia',
        'subtitle': '*Sahkan kontrak pekerjaan berdasarkan Akta Kerja 1955 & Akta Perhubungan Perusahaan 1967*',
        'upload_label': '📎 Muat Naik Kontrak Pekerjaan (PDF)',
        'file_uploaded': '✅ Fail dimuat naik:',
        'detected': 'Bahasa Dikesan: 🇲🇾 Bahasa Melayu',
        'validate_btn': '🔬 Sahkan Kontrak',
        'generate_btn': '📝 Jana Kontrak Baru',
        'download_btn': '📥 Muat Turun Kontrak (PDF)',
        'processing_val': '⏳ Sedang menganalisis klausa kontrak...',
        'processing_gen': '⏳ AI sedang menulis semula kontrak...',
        'processing_pdf': '⏳ Sedang menjana PDF...',
        'report_title': '📊 Laporan Pengesahan',
        'no_violations': '✅ Tiada pelanggaran dikesan! Kontrak ini mematuhi undang-undang.',
        'violations_found': '⚠️ Pelanggaran Ditemui',
        'total_clauses': 'Jumlah Klausa',
        'issues_found': 'Klausa Bermasalah',
        'total_violations': 'Jumlah Isu',
        'preview_title': '📄 Pratonton Kontrak Baru',
        'confirm_pdf': '✅ Sahkan dan Jana PDF',
        'success_pdf': '✅ PDF Kontrak Berjaya Dijana!',
        'original_clause': 'Klausa Asal:',
        'violation_details': 'Butiran Pelanggaran:',
        'status_label': 'Status',
        'reason_label': 'Sebab',
        'corrected_label': 'Pembetulan',
        'status_legal': '✅ Sah',
        'status_illegal': '❌ Tidak Sah',
        'status_missing': '⚪ Tidak Dinyatakan'
    }
}

# --- Session State Management ---
if "checker_output" not in st.session_state: st.session_state.checker_output = None
if "full_corrected_text" not in st.session_state: st.session_state.full_corrected_text = None
if "detected_language" not in st.session_state: st.session_state.detected_language = 'en'
if "current_contract_text" not in st.session_state: st.session_state.current_contract_text = ""
if "file_key" not in st.session_state: st.session_state.file_key = ""

def get_text(key):
    """Retrieve translation for the current language."""
    return TRANSLATIONS[st.session_state.detected_language].get(key, key)

st.title(get_text('title'))
st.markdown(get_text('subtitle'))

uploaded_file = st.file_uploader(get_text('upload_label'), type=['pdf'])

if uploaded_file is not None:
    # --- 1. AUTO-PROCESSING ON UPLOAD ---
    if uploaded_file.file_id != st.session_state.file_key:
        st.session_state.file_key = uploaded_file.file_id
        st.session_state.checker_output = None
        st.session_state.full_corrected_text = None
        
        # Extract Text
        raw_text = extract_text_from_pdf(uploaded_file)
        raw_text = re.sub(r'[\u200b\u200c\u200d\uFEFF]', '', raw_text)
        st.session_state.current_contract_text = raw_text
        
        # Detect Language & Update State
        st.session_state.detected_language = local_detect_language(raw_text)
        
        # Rerun immediately to switch the UI language
        st.rerun()

    # Display Info
    st.success(f"{get_text('file_uploaded')} **{uploaded_file.name}**")
    st.info(get_text('detected'))
    
    col1, col2 = st.columns([1, 1])
    
    # --- 2. VALIDATE BUTTON ---
    with col1:
        if st.button(get_text('validate_btn'), type="primary", use_container_width=True):
            with st.spinner(get_text('processing_val')):
                # Call JamAI (Uses text from session state - No re-extraction needed)
                st.session_state.checker_output = check_full_contract(
                    st.session_state.current_contract_text
                )

    # --- 3. REPORT DISPLAY ---
    if st.session_state.checker_output:
        st.markdown("---")
        st.subheader(get_text('report_title'))
        report_data = st.session_state.checker_output
        
        if isinstance(report_data, dict):
            summary = report_data.get("summary", {})
            total_clauses = summary.get("total_clauses_found", 0)
            illegal_clauses = report_data.get("violations", [])
        else:
            total_clauses = len(report_data)
            illegal_clauses = report_data
            
        # Count specific violation points
        total_violations = sum(len(c.get("illegal", {})) for c in illegal_clauses)
        
        # Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric(get_text('total_clauses'), total_clauses)
        m2.metric(get_text('issues_found'), len(illegal_clauses))
        m3.metric(get_text('total_violations'), total_violations)
        
        # --- Financial Impact Dashboard ---
        contract_risk_data = report_data.get("contract_risk") or {}
        employee_facts = report_data.get("employee_data") or {}
        liability_summary = {}
        if contract_risk_data:
            liability_summary = calculate_liability(contract_risk_data, employee_facts)
        if liability_summary or employee_facts:
            render_financial_dashboard(liability_summary, employee_facts)

        if not illegal_clauses:
            st.success(get_text('no_violations'))
        else:
            st.warning(f"{get_text('violations_found')}: {total_violations}")
            
            # Render Violations
            for i, clause in enumerate(illegal_clauses, 1):
                with st.expander(f"🚩 Clause {i}", expanded=True):
                    st.markdown(f"**{get_text('original_clause')}**")
                    st.info(clause.get("text", ""))
                    
                    st.markdown(f"**{get_text('violation_details')}**")
                    
                    illegal_details = clause.get("illegal", {})
                    for category, details in illegal_details.items():
                        cat_label = TRANSLATIONS[st.session_state.detected_language].get(category, category.title())
                        st.markdown(f"### {cat_label}")
                        
                        # Status
                        status_key = f"status_{details.get('status', 'missing')}"
                        st.markdown(f"**{get_text('status_label')}:** {get_text(status_key)}")
                        
                        # Reason
                        if details.get('reason'):
                            st.markdown(f"**{get_text('reason_label')}:** {details['reason']}")
                            
                        # Correction
                        if details.get('corrected'):
                            st.success(f"**{get_text('corrected_label')}:** {details['corrected']}")

        # --- 4. GENERATE BUTTON ---
        st.markdown("---")
        with col2:
            # Only enable if violations exist
            if st.button(get_text('generate_btn'), type="secondary", use_container_width=True, disabled=not illegal_clauses):
                with st.spinner(get_text('processing_gen')):
                    # Call Generator
                    st.session_state.full_corrected_text = generate_corrected_contract(
                        st.session_state.current_contract_text,
                        st.session_state.detected_language
                    )

    # --- 5. DOWNLOAD SECTION ---
    if st.session_state.full_corrected_text:
        st.markdown("---")
        st.subheader(get_text('preview_title'))
        
        st.text_area("", st.session_state.full_corrected_text, height=300)
        
        # PDF Download Button
        if st.button(get_text('confirm_pdf'), type="primary"):
            with st.spinner(get_text('processing_pdf')):
                pdf_data = create_pdf_from_markdown(st.session_state.full_corrected_text)
                st.success(get_text('success_pdf'))
                
                st.download_button(
                    label=get_text('download_btn'),
                    data=pdf_data.getvalue(),
                    file_name="Compliant_Contract.pdf",
                    mime="application/pdf"
                )

else:
    # Default Empty State
    st.info("👆 " + get_text('upload_label'))
    
    # Info Expander
    with st.expander("ℹ️ What does this tool validate?"):
        st.markdown("""
        **Checks compliance with:**
        - Employment Act 1955
        - Industrial Relations Act 1967
        
        **Key Areas:**
        - ✅ Minimum wage (RM1,500)
        - ✅ Working hours (Max 48h/week)
        - ✅ Overtime rates
        - ✅ Maternity/Paternity leave
        - ✅ Notice periods

        """)
