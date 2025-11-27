import re

def calculate_liability(risk_json, employee_data):
    """
    Takes raw risk tags from AI (contract_risk) + extracted employee facts (employee_data).
    Returns the final calculated breakdown and totals for the Dashboard.
    """
    
    # --- 1. SETUP & PARSING ---
    # Parse Salary safely (Handle numbers or strings like "RM 1,500.00")
    raw_salary = employee_data.get("basic_salary_monthly", 1500)
    try:
        # Remove currency symbols and commas, then convert to float
        clean_salary = str(raw_salary).upper().replace("RM", "").replace(",", "").strip()
        salary = float(clean_salary)
    except:
        salary = 1500.00 # Fallback to Min Wage
    
    # Parse Other Facts
    probation_mos = float(employee_data.get("probation_months", 6) or 6)
    notice_mos = float(employee_data.get("notice_period_months", 2) or 2)
    
    # Initialize Totals
    total_likely = 0.0
    total_worst = 0.0
    breakdown_list = []

    # Safety check: If AI didn't return a risk assessment list, return empty
    # Note: We look for 'risk_assessment' based on the Simplified Prompt
    # If using older prompt, it might be 'violations'. We check both.
    risk_list = risk_json.get("risk_assessment", [])
    if not risk_list:
        risk_list = risk_json.get("violations", [])

    if not risk_list:
        return {}

    # --- 2. CALCULATION LOOP ---
    for item in risk_list:
        
        # A. EXTRACT AI DATA
        # key names might vary slightly depending on which prompt you used last
        tag = item.get("calc_tag") or item.get("calculation_tag") or "CALC_NONE"
        violation_name = item.get("violation_name") or item.get("violation_type") or "Issue"
        
        # Fine Amount
        try:
            max_fine = float(item.get("max_fine_rm", 50000))
        except:
            max_fine = 50000.0

        # Jail / Serious Offense Check
        jail_term = item.get("jail_term", "None")
        is_serious = False
        if jail_term and str(jail_term).lower() != "none":
            is_serious = True
        # Keyword check for safety
        if "forced" in violation_name.lower() or "foreign" in violation_name.lower():
            is_serious = True

        # B. FINE CALCULATION (Government Penalty)
        # Logic: 50% for standard offenses, 100% for serious/jail offenses
        if is_serious:
            likely_fine = max_fine
        else:
            likely_fine = max_fine * 0.25

        # C. ARREARS CALCULATION (Employee Debt)
        arrears = 0.0
        math_note = ""

        if tag == "CALC_OT":
            # Formula: Hourly Rate * 1.5 * 5 hours/week * 52 weeks
            # 26 days is the statutory divisor
            hourly_rate = (salary / 26) / 8
            arrears = hourly_rate * 1.5 * 5 * 52
            math_note = "(Est. 5hrs OT/week x 1 year)"

        elif tag == "CALC_EPF":
            # Formula: 13% * Salary * Probation Months
            arrears = (salary * 0.13) * probation_mos
            math_note = f"(13% EPF for {probation_mos} months)"

        elif tag == "CALC_NOTICE" or tag == "CALC_TERMINATION":
            # Formula: Salary * Notice Months
            arrears = salary * notice_mos
            math_note = f"({notice_mos} months indemnity pay)"

        elif tag == "CALC_MIN_WAGE":
            if salary < 1500:
                arrears = (1500 - salary) * 12
                math_note = "(Top-up to RM1,500 for 1 year)"
        
        elif tag == "CALC_LEAVE":
            # Formula: Daily Rate * 4 days (conservative avg of days denied)
            daily_rate = salary / 26
            arrears = daily_rate * 4
            math_note = "(Compensation for approx 4 days leave)"

        # --- 3. AGGREGATE ---
        item_likely_total = likely_fine + arrears
        item_worst_total = max_fine + arrears
        
        total_likely += item_likely_total
        total_worst += item_worst_total

        # Format the String for UI
        jail_badge = f" | ⛓️ Jail: {jail_term}" if is_serious else ""
        
        breakdown_str = (
            f"⚠️ {violation_name}: RM {likely_fine:,.0f} (Fine) + "
            f"RM {arrears:,.2f} (Arrears) **{math_note}**{jail_badge}"
        )
        breakdown_list.append(breakdown_str)

    # --- 4. FINAL OUTPUT STRUCTURE ---
    # This dictionary matches exactly what 'render_financial_dashboard' expects
    return {
        "breakdown": breakdown_list,
        "total_likely_liability": total_likely,
        "total_worst_case_liability": total_worst
    }