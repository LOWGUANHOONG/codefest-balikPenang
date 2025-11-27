import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
import config
from termination_checker import check_termination  # <-- use your new helper

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
    # 1. We must place SOMETHING here, but we hide it with CSS to clear the space.
    # The actual title is injected using the CSS ::before pseudo-element above.
    st.empty() 
    
    # NOTE: The navigation links are AUTO-GENERATED and now appear immediately
    # after the empty space, but the CSS places the title above them.

    
    # 3. Place the Legal Disclaimer at the bottom
    st.markdown("""
    <div class="disclaimer">
        ⚠️ DISCLAIMER: This tool is for informational purposes only and does not constitute legal advice. 
        Always consult with a qualified legal professional for advice regarding specific legal issues.
    </div>
    """, unsafe_allow_html=True)

st.title("📝 Employee Termination & Compensation Generator")

# --- 1️⃣ Upload Employee Data CSV/Excel ---
uploaded_file = st.file_uploader("Upload Employee CSV/Excel", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        employee_df = pd.read_csv(uploaded_file)
    else:
        employee_df = pd.read_excel(uploaded_file)

    st.subheader("Preview Employee Data")
    st.dataframe(employee_df)

    # --- 2️⃣ Select Employee(s) to Terminate ---
    selected_employees = st.multiselect("Select Employee(s) to Terminate", employee_df['name'])

    if selected_employees:
        # --- 3️⃣ Select Termination Reason ---
        reason = st.selectbox("Termination Reason", [
            "Poor Performance", "Misconduct", "Redundancy", "Resignation", "Other"
        ])

        # --- 4️⃣ Check Termination & Generate Letter(s) ---
        if st.button("✅ Check Termination & Generate Letter(s)"):
            for emp_name in selected_employees:
                employee_row = employee_df[employee_df['name'] == emp_name].iloc[0]
                employee_data = employee_row.to_dict()

                # --- Call termination_checker helper ---
                result = check_termination(employee_data, reason)

                legal_to_terminate = result.get("legal_to_terminate", False)

                if legal_to_terminate:
                    st.success(f"✅ Termination allowed for {emp_name}")

                    # --- Calculate Compensation ---
                    notice_pay = round(employee_data.get("salary", 0) * result.get("required_notice_period", 1), 2)
                    severance = round(result.get("severance_pay", 0), 2)
                    unused_leave_pay = round(result.get("unused_leave_pay", 0), 2)
                    total_comp = round(notice_pay + severance + unused_leave_pay, 2)

                    st.subheader(f"💰 Compensation for {emp_name}")
                    st.write(f"Notice Pay: RM {notice_pay}")
                    st.write(f"Severance: RM {severance}")
                    st.write(f"Unused Leave: RM {unused_leave_pay}")
                    st.write(f"**Total Compensation: RM {total_comp}**")

                    # --- Generate PDF Termination Letter ---
                    buffer = BytesIO()
                    c = canvas.Canvas(buffer, pagesize=A4)
                    width, height = A4

                    c.setFont("Helvetica-Bold", 14)
                    c.drawString(50, height - 50, "Termination Letter")
                    c.setFont("Helvetica", 12)
                    c.drawString(50, height - 100, f"Date: {datetime.today().strftime('%d/%m/%Y')}")
                    c.drawString(50, height - 120, f"To: {employee_data['name']}")
                    c.drawString(50, height - 140, f"Role: {employee_data['role']}")
                    c.drawString(50, height - 180, f"Dear {employee_data['name']},")
                    c.drawString(50, height - 200, "We regret to inform you that your employment is terminated effective immediately.")
                    c.drawString(50, height - 220, f"Reason: {reason}")
                    c.drawString(50, height - 240, f"Compensation to be paid: RM {total_comp}")
                    c.drawString(50, height - 260, f"(Notice Pay: RM {notice_pay}, Severance: RM {severance}, Unused Leave: RM {unused_leave_pay})")
                    c.drawString(50, height - 300, "Sincerely,")
                    c.drawString(50, height - 320, "HR Department")

                    c.showPage()
                    c.save()
                    buffer.seek(0)

                    st.download_button(
                        label=f"📄 Download Termination Letter - {emp_name}",
                        data=buffer,
                        file_name=f"termination_{employee_data['name']}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error(f"⚠️ Termination not allowed for {emp_name}: {result.get('legal_reasons_if_cannot', 'Check contract/law')}")

