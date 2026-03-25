import streamlit as st
import pandas as pd
import pdfplumber
import requests
import numpy_financial as npf

# --- PLATFORM BRANDING ---
st.set_page_config(page_title="Moneyplan Retirement & Insurance", layout="wide")
st.sidebar.title("Moneyplan Financial Services")
st.sidebar.write("**Advisor:** Sachin Thorat")
st.sidebar.markdown("---")

st.title("Retirement & Policy Analytics Platform")

# --- 1. LIVE AMFI MF DATABASE (RETAINED FROM PREVIOUS APP) ---
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

# --- 2. PDF PROCESSING ENGINE ---
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

# --- UI TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🚨 Portfolio Health (Underperformers)", 
    "🎯 Pension Planner", 
    "⚖️ UPS vs NPS vs SWP", 
    "📄 Insurance IRR Projector"
])

# ==========================================
# TAB 1: UNDERPERFORMING FUNDS FINDER
# ==========================================
with tab1:
    st.markdown("### Identify Underperforming Assets via CAS Upload")
    uploaded_cas = st.file_uploader("Upload Client CAS PDF", type=["pdf"], key="cas_upload")
    
    if uploaded_cas:
        with st.spinner("Scanning portfolio..."):
            client_funds = process_cas_pdf(uploaded_cas)
            
        if client_funds:
            st.success(f"Detected {len(client_funds)} funds in the portfolio.")
            
            underperformers = []
            for fund in client_funds:
                # Automatically flag Regular Plans as underperformers due to commission drag
                if "Regular" in fund or "REGULAR" in fund.upper():
                     underperformers.append({
                            "Fund Name": fund,
                            "Issue": "Regular Plan (High Expense Ratio)",
                            "Impact": "Losing 1% to 1.5% CAGR annually",
                            "Advisory Action": "🚨 SWITCH TO DIRECT"
                        })
                # Flag Dividend/IDCW plans (tax inefficient for compounding)
                elif "Dividend" in fund or "IDCW" in fund.upper():
                    underperformers.append({
                            "Fund Name": fund,
                            "Issue": "IDCW/Dividend Option",
                            "Impact": "Tax inefficient, disrupts compounding",
                            "Advisory Action": "⚠️ SWITCH TO GROWTH"
                        })
            
            if underperformers:
                st.markdown("#### 🚩 Structural Red Flags Found:")
                st.dataframe(pd.DataFrame(underperformers), use_container_width=True)
            else:
                st.info("No structural red flags (like Regular/IDCW plans) detected. All funds are Direct Growth.")
                
            st.markdown("---")
            st.markdown("#### Replace Underperforming Schemes")
            col_old, col_new = st.columns(2)
            with col_old:
                selected_old = st.selectbox("Select a detected fund to replace:", options=client_funds)
            with col_new:
                selected_new = st.selectbox("Search AMFI for a Better Alternative:", options=all_fund_names)
            
            if st.button("Generate Replacement Recommendation"):
                st.warning(f"**Action:** Recommend stopping SIP in '{selected_old}' and initiating fresh SIPs in '{selected_new}' (AMFI Code: {all_funds_db.get(selected_new, 'N/A')}).")

# ==========================================
# TAB 2: PENSION PLANNER (Lumpsum / SIP)
# ==========================================
with tab2:
    st.markdown("### Reverse-Engineer the Retirement Corpus")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        desired_pension = st.number_input("Desired Monthly Pension (₹)", value=100000, step=10000)
    with col2:
        years_to_retire = st.slider("Years until Retirement", 1, 30, 15)
    with col3:
        swp_rate = st.number_input("Safe Withdrawal Rate (%)", value=6.0, step=0.5, help="Annual withdrawal rate post-retirement")

    st.markdown("---")
    
    # Math: Required Corpus = (Monthly Pension * 12) / Withdrawal Rate
    annual_pension = desired_pension * 12
    required_corpus = annual_pension / (swp_rate / 100)
    
    accumulation_rate = 12.0 # Standard equity return assumption
    monthly_rate = (accumulation_rate / 100) / 12
    months = years_to_retire * 12
    required_sip = (required_corpus * monthly_rate) / (((1 + monthly_rate)**months - 1) * (1 + monthly_rate))
    required_lumpsum = required_corpus / ((1 + (accumulation_rate/100)) ** years_to_retire)

    st.markdown(f"### Target Retirement Corpus: **<span style='color:#10b981'>₹ {int(required_corpus):,}</span>**", unsafe_allow_html=True)
    
    rc1, rc2 = st.columns(2)
    with rc1:
        st.info(f"#### Option A: Regular SIP\nRequires an ongoing SIP of **₹ {int(required_sip):,}/month** for the next {years_to_retire} years.")
    with rc2:
        st.success(f"#### Option B: One-Time Lumpsum\nRequires a lumpsum investment of **₹ {int(required_lumpsum):,}** today.")

# ==========================================
# TAB 3: UPS vs NPS vs MF SWP
# ==========================================
with tab3:
    st.markdown("### Pension Framework Showdown")
    st.write("Educate clients on the structural differences between government schemes and private market withdrawal strategies.")
    
    comparison_data = {
        "Feature": ["Guarantee", "Market Risk", "Inflation Protection", "Liquidity / Lock-in", "Taxation on Pension", "Wealth Transmission (Legacy)"],
        "UPS (Unified Pension Scheme)": ["50% of last drawn salary guaranteed", "Zero risk to employee", "Indexed to inflation (DR)", "Zero liquidity. Locked for life.", "Taxable as salary slab", "Family pension applies, but no corpus passed to heirs."],
        "NPS (National Pension System)": ["No guarantee. Market linked.", "Moderate to High (Equity/Debt mix)", "Depends on annuity chosen", "Rigid. 40% must be annuitized.", "Annuity income is fully taxable", "Remaining annuity purchase price goes to nominee."],
        "Mutual Fund SWP": ["No guarantee.", "Moderate to High (Depends on fund)", "High (Equity usually beats inflation)", "100% Liquid anytime.", "Highly tax-efficient (LTCG exemption)", "Entire remaining corpus passes seamlessly to heirs."]
    }
    
    st.table(pd.DataFrame(comparison_data).set_index("Feature"))
    
    st.markdown("### 💡 Moneyplan Advisory Verdict")
    st.info("**For Government Employees:** Opt for UPS for the baseline guaranteed security. However, build a parallel Mutual Fund portfolio for liquidity and generational wealth transfer.\n\n**For Private Sector:** Combine voluntary EPF for the debt portion, and use Flexi-Cap/Hybrid Mutual Funds with an SWP strategy at retirement to beat inflation and minimize taxes.")

# ==========================================
# TAB 4: INSURANCE IRR PROJECTOR (Money-Back & Endowment)
# ==========================================
with tab4:
    st.markdown("### Expose the True Return of Traditional Insurance Policies")
    st.write("Calculate the actual Internal Rate of Return (IRR) for complex Money-Back and Endowment policies.")
    
    st.markdown("#### Policy Details")
    c1, c2, c3 = st.columns(3)
    with c1:
        annual_premium = st.number_input("Annual Premium Paid (₹)", value=50000, step=5000)
        premium_paying_term = st.slider("Premium Paying Term (Years)", 5, 20, 10)
    with c2:
        policy_term = st.slider("Total Policy Term (Years until maturity)", 10, 30, 20)
        maturity_benefit = st.number_input("Final Maturity Benefit (₹)", value=1000000, step=50000)
    with c3:
        st.markdown("**Money-Back / Survival Benefits**")
        has_survival_benefit = st.checkbox("Policy has regular cash payouts before maturity")
        survival_benefit = 0
        survival_interval = 0
        if has_survival_benefit:
            survival_benefit = st.number_input("Payout Amount (₹)", value=20000, step=5000)
            survival_interval = st.number_input("Paid every X years", value=5, min_value=1, max_value=15)
        
    if st.button("Calculate True Policy IRR"):
        # Build the dynamic cash flow array
        cashflows = [0.0] * (policy_term + 1)
        
        for year in range(policy_term + 1):
            # Client pays premium
            if year < premium_paying_term:
                cashflows[year] -= annual_premium
            
            # Client receives intermediate survival benefit
            if has_survival_benefit and year > 0 and year % survival_interval == 0 and year < policy_term:
                cashflows[year] += survival_benefit
                
            # Final maturity payout
            if year == policy_term:
                cashflows[year] += maturity_benefit
        
        # Calculate IRR
        irr = npf.irr(cashflows) * 100
        total_paid = annual_premium * premium_paying_term
        total_received = maturity_benefit + (sum([cashflows[y] for y in range(policy_term) if cashflows[y] > 0]))
        
        st.markdown("---")
        res1, res2, res3 = st.columns(3)
        res1.metric("Total Premium Paid", f"₹ {int(total_paid):,}")
        res2.metric("Total Money Received", f"₹ {int(total_received):,}")
        
        if irr < 6.0:
            res3.markdown(f"### True Return: <span style='color:#ef4444'>{irr:.2f}%</span>", unsafe_allow_html=True)
            st.error("⚠️ **Advisory Action:** This policy's return is failing to beat inflation. Recommend making it 'Paid-Up' or surrendering it. Shift the premium to a Term Plan + Mutual Fund SIP combination.")
        else:
            res3.markdown(f"### True Return: <span style='color:#10b981'>{irr:.2f}%</span>", unsafe_allow_html=True)
            st.success("This return is relatively healthy for a traditional policy, though it likely still trails pure equity.")