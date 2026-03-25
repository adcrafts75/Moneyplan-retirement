import streamlit as st
import pandas as pd
import pdfplumber
import requests
import numpy_financial as npf
from fpdf import FPDF
from datetime import date

# ==========================================
# --- SECURITY GATEKEEPER ---
# ==========================================
def check_password():
    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 Moneyplan Secure Login")
    
    def password_entered():
        if st.session_state["entered_pin"] == st.secrets["admin_pin"]:
            st.session_state["password_correct"] = True
            del st.session_state["entered_pin"]
        else:
            st.session_state["password_correct"] = False

    st.text_input("Enter Admin PIN", type="password", on_change=password_entered, key="entered_pin")
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Incorrect PIN. Access Denied.")
        
    return False

if not check_password():
    st.stop()

# ==========================================
# --- PLATFORM BRANDING ---
# ==========================================
st.set_page_config(page_title="Moneyplan Retirement & Insurance", layout="wide")
st.sidebar.title("Moneyplan Financial Services")
st.sidebar.write("**Advisor:** Sachin Thorat")
st.sidebar.markdown("---")

st.title("Retirement & Policy Analytics Platform")

@st.cache_data(ttl=86400) 
def get_all_indian_mutual_funds():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get("https://www.amfiindia.com/spages/NAVAll.txt", headers=headers, timeout=15)
        response.raise_for_status() 
        fund_dict = {}
        lines = response.text.split('\n')
        for line in lines:
            parts = line.split(';')
            if len(parts) >= 4 and parts[0].strip().isdigit():
                fund_dict[parts[3].strip()] = parts[0].strip()
        return dict(sorted(fund_dict.items()))
    except Exception as e:
        return {"Error loading live funds.": 0}

with st.spinner("Syncing Live AMFI Database..."):
    all_funds_db = get_all_indian_mutual_funds()
    all_fund_names = list(all_funds_db.keys())

def process_cas_pdf(uploaded_file):
    extracted_funds = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    if "INF" in line and "|" in line:
                        fund_name = line.split('|')[0].strip()
                        if fund_name not in extracted_funds:
                            extracted_funds.append(fund_name)
                    elif ("- Regular Plan" in line or "- Direct Plan" in line) and "Fund" in line:
                        fund_name = line.split('-')[0].strip()
                        if fund_name not in extracted_funds:
                            extracted_funds.append(fund_name)
    return extracted_funds

tab1, tab2, tab3, tab4 = st.tabs(["🚨 Portfolio Health", "🎯 Pension Planner", "⚖️ UPS vs NPS", "📄 Insurance IRR"])

with tab1:
    st.markdown("### Identify Underperforming Assets")
    uploaded_cas = st.file_uploader("Upload Client CAS PDF", type=["pdf"], key="cas_upload")
    
    if uploaded_cas:
        with st.spinner("Scanning portfolio..."):
            client_funds = process_cas_pdf(uploaded_cas)
            
        if client_funds:
            underperformers = []
            for fund in client_funds:
                if "Regular" in fund or "REGULAR" in fund.upper():
                     underperformers.append({"Fund Name": fund, "Issue": "Regular Plan", "Advisory Action": "🚨 SWITCH TO DIRECT"})
                elif "Dividend" in fund or "IDCW" in fund.upper():
                    underperformers.append({"Fund Name": fund, "Issue": "IDCW Option", "Advisory Action": "⚠️ SWITCH TO GROWTH"})
            
            if underperformers:
                st.dataframe(pd.DataFrame(underperformers), use_container_width=True)
            else:
                st.info("No structural red flags detected.")

with tab2:
    st.markdown("### Reverse-Engineer the Retirement Corpus")
    col1, col2, col3 = st.columns(3)
    with col1:
        desired_pension = st.number_input("Desired Monthly Pension (₹)", value=100000, step=10000)
    with col2:
        years_to_retire = st.slider("Years until Retirement", 1, 30, 15)
    with col3:
        swp_rate = st.number_input("Safe Withdrawal Rate (%)", value=6.0, step=0.5)

    annual_pension = desired_pension * 12
    required_corpus = annual_pension / (swp_rate / 100)
    
    accumulation_rate = 12.0
    monthly_rate = (accumulation_rate / 100) / 12
    months = years_to_retire * 12
    required_sip = (required_corpus * monthly_rate) / (((1 + monthly_rate)**months - 1) * (1 + monthly_rate))
    required_lumpsum = required_corpus / ((1 + (accumulation_rate/100)) ** years_to_retire)

    st.markdown(f"### Target Retirement Corpus: **<span style='color:#10b981'>₹ {int(required_corpus):,}</span>**", unsafe_allow_html=True)
    rc1, rc2 = st.columns(2)
    with rc1:
        st.info(f"#### Option A: Regular SIP\nRequires an ongoing SIP of **₹ {int(required_sip):,}/month** for the next {years_to_retire} years.")
    with rc2:
        st.success(f"#### Option B: Lumpsum\nRequires **₹ {int(required_lumpsum):,}** today.")

with tab3:
    st.markdown("### ⚖️ UPS vs NPS Calculator & Framework")
    emp_name = st.text_input("Employee Name", value="Govt Employee")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        current_nps = st.number_input("Current NPS Corpus (₹)", value=1500000, step=100000)
        monthly_contribution = st.number_input("Total Monthly NPS SIP (₹)", value=15000, step=1000)
    with c2:
        served_years = st.number_input("Years of Service Completed", value=12, step=1)
        balance_years = st.number_input("Balance Years to Retirement", value=18, step=1)
    with c3:
        expected_last_basic_da = st.number_input("Expected Last Drawn Basic + DA (₹)", value=120000, step=5000)
        nps_cagr = st.number_input("Expected NPS Return (CAGR %)", value=10.0, step=0.5)

    if st.button("Run UPS vs NPS Analysis"):
        total_service = served_years + balance_years
        
        # UPS Logic
        if total_service < 10:
            ups_monthly_pension = 0
            ups_note = "Not eligible for UPS Pension (<10 years service)."
        else:
            base_pension = expected_last_basic_da / 2
            ups_monthly_pension = base_pension if total_service >= 25 else base_pension * (total_service / 25)
            ups_monthly_pension = max(ups_monthly_pension, 10000)
            ups_note = "Eligible for UPS Pension."
        ups_lumpsum = (expected_last_basic_da / 10) * (total_service * 2)
        
        # NPS Logic
        months = balance_years * 12
        monthly_rate = (nps_cagr / 100) / 12
        if months > 0 and monthly_rate > 0:
            total_nps_corpus = (current_nps * ((1 + monthly_rate) ** months)) + (monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate))
        else:
            total_nps_corpus = current_nps

        annuity_rate = 6.0 
        nps_annuity_corpus = total_nps_corpus * 0.40 
        nps_lumpsum = total_nps_corpus * 0.60 
        nps_monthly_pension = (nps_annuity_corpus * (annuity_rate / 100)) / 12
        
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.success("### Unified Pension Scheme (UPS)")
            st.metric("Guaranteed Monthly Pension", f"₹ {int(ups_monthly_pension):,}")
            st.metric("Superannuation Lumpsum", f"₹ {int(ups_lumpsum):,}")

        with res_col2:
            st.info("### National Pension System (NPS)")
            st.metric(f"Expected Pension (@{annuity_rate}%)", f"₹ {int(nps_monthly_pension):,}")
            st.metric("Tax-Free Lumpsum (60%)", f"₹ {int(nps_lumpsum):,}")

        def generate_ups_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", 'B', 16)
            pdf.set_text_color(30, 58, 138)
            pdf.cell(0, 10, "MONEYPLAN FINANCIAL SERVICES", ln=True, align='C')
            pdf.set_font("Helvetica", 'I', 11)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 8, "UPS vs NPS - Comparative Pension Analysis", ln=True, align='C')
            pdf.ln(10)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", '', 11)
            pdf.cell(0, 8, f"Prepared For: {emp_name}", ln=True)
            pdf.cell(0, 8, f"Total Estimated Service: {total_service} Years", ln=True)
            pdf.ln(5)
            
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(0, 10, " 1. UNIFIED PENSION SCHEME (UPS)", ln=True)
            pdf.set_font("Helvetica", '', 11)
            pdf.cell(0, 8, f"Guaranteed Monthly Pension: Rs. {int(ups_monthly_pension):,}", ln=True)
            pdf.cell(0, 8, f"Superannuation Lumpsum: Rs. {int(ups_lumpsum):,}", ln=True)
            pdf.ln(5)
            
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(0, 10, " 2. NATIONAL PENSION SYSTEM (NPS)", ln=True)
            pdf.set_font("Helvetica", '', 11)
            pdf.cell(0, 8, f"Expected Monthly Pension: Rs. {int(nps_monthly_pension):,} (Assuming {annuity_rate}% Annuity)", ln=True)
            pdf.cell(0, 8, f"Tax-Free Lumpsum (60%): Rs. {int(nps_lumpsum):,}", ln=True)
            pdf.ln(10)
            
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 6, "Moneyplan Financial Services", ln=True)
            return bytes(pdf.output())

        st.download_button("📄 Download UPS vs NPS Report", data=generate_ups_pdf(), file_name=f"{emp_name}_UPS_vs_NPS.pdf", mime="application/pdf")

with tab4:
    st.markdown("### Expose the True Return of Insurance Policies")
    c1, c2, c3 = st.columns(3)
    with c1:
        annual_premium = st.number_input("Annual Premium Paid (₹)", value=50000, step=5000)
        premium_paying_term = st.slider("Premium Paying Term (Years)", 5, 20, 10)
    with c2:
        policy_term = st.slider("Total Policy Term (Years until maturity)", 10, 30, 20)
        maturity_benefit = st.number_input("Final Maturity Benefit (₹)", value=1000000, step=50000)
    with c3:
        has_survival_benefit = st.checkbox("Policy has regular cash payouts before maturity")
        survival_benefit = 0
        survival_interval = 0
        if has_survival_benefit:
            survival_benefit = st.number_input("Payout Amount (₹)", value=20000, step=5000)
            survival_interval = st.number_input("Paid every X years", value=5, min_value=1, max_value=15)
        
    if st.button("Calculate True Policy IRR"):
        cashflows = [0.0] * (policy_term + 1)
        for year in range(policy_term + 1):
            if year < premium_paying_term:
                cashflows[year] -= annual_premium
            if has_survival_benefit and year > 0 and year % survival_interval == 0 and year < policy_term:
                cashflows[year] += survival_benefit
            if year == policy_term:
                cashflows[year] += maturity_benefit
        
        irr = npf.irr(cashflows) * 100
        total_paid = annual_premium * premium_paying_term
        total_received = maturity_benefit + sum([cashflows[y] for y in range(policy_term) if cashflows[y] > 0])
        
        res1, res2, res3 = st.columns(3)
        res1.metric("Total Premium Paid", f"₹ {int(total_paid):,}")
        res2.metric("Total Money Received", f"₹ {int(total_received):,}")
        
        if irr < 6.0:
            res3.markdown(f"### True Return: <span style='color:#ef4444'>{irr:.2f}%</span>", unsafe_allow_html=True)
            st.error("⚠️ This policy fails to beat inflation.")
        else:
            res3.markdown(f"### True Return: <span style='color:#10b981'>{irr:.2f}%</span>", unsafe_allow_html=True)
