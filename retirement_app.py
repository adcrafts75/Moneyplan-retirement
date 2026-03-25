# ==========================================
# TAB 3: UPS vs NPS (Govt Employee Calculator)
# ==========================================
with tab3:
    st.markdown("### ⚖️ UPS vs NPS Calculator & Framework")
    
    with st.expander("📖 View Structural Differences (Cheat Sheet)", expanded=False):
        st.write("Educate clients on the structural differences between government schemes and private market withdrawal strategies.")
        comparison_data = {
            "Feature": ["Guarantee", "Market Risk", "Inflation Protection", "Liquidity / Lock-in", "Taxation on Pension", "Wealth Transmission (Legacy)"],
            "UPS (Unified Pension Scheme)": ["50% of last drawn salary guaranteed", "Zero risk to employee", "Indexed to inflation (DR)", "Zero liquidity. Locked for life.", "Taxable as salary slab", "Family pension applies, but no corpus passed to heirs."],
            "NPS (National Pension System)": ["No guarantee. Market linked.", "Moderate to High (Equity/Debt mix)", "Depends on annuity chosen", "Rigid. 40% must be annuitized.", "Annuity income is fully taxable", "Remaining annuity purchase price goes to nominee."]
        }
        st.table(pd.DataFrame(comparison_data).set_index("Feature"))

    st.markdown("#### 🧮 Personalized Pension Projection")
    st.write("Input the employee's current data to mathematically compare UPS guarantees against expected NPS market returns.")
    
    emp_name = st.text_input("Employee Name", value="Govt Employee")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        current_nps = st.number_input("Current NPS Corpus (₹)", value=1500000, step=100000)
        monthly_contribution = st.number_input("Total Monthly NPS SIP (Employee + Govt) (₹)", value=15000, step=1000)
    with c2:
        served_years = st.number_input("Years of Service Completed", value=12, step=1)
        balance_years = st.number_input("Balance Years to Retirement", value=18, step=1)
    with c3:
        expected_last_basic_da = st.number_input("Expected Last Drawn Basic + DA (₹)", value=120000, step=5000)
        nps_cagr = st.number_input("Expected NPS Return (CAGR %)", value=10.0, step=0.5)

    st.markdown("---")
    
    if st.button("Run UPS vs NPS Analysis"):
        total_service = served_years + balance_years
        
        # --- UPS CALCULATIONS ---
        # Pension: 50% of basic, pro-rata if < 25 years. Min 10,000 if > 10 years.
        if total_service < 10:
            ups_monthly_pension = 0
            ups_note = "Not eligible for UPS Pension (<10 years service)."
        else:
            base_pension = expected_last_basic_da / 2
            if total_service >= 25:
                ups_monthly_pension = base_pension
            else:
                ups_monthly_pension = base_pension * (total_service / 25)
            
            if ups_monthly_pension < 10000:
                ups_monthly_pension = 10000
            ups_note = "Eligible for UPS Pension."
            
        # UPS Lumpsum: 1/10th of basic+DA for every 6 months of service
        ups_lumpsum = (expected_last_basic_da / 10) * (total_service * 2)
        
        # --- NPS CALCULATIONS ---
        months = balance_years * 12
        monthly_rate = (nps_cagr / 100) / 12
        
        if months > 0 and monthly_rate > 0:
            fv_corpus = current_nps * ((1 + monthly_rate) ** months)
            fv_sip = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
            total_nps_corpus = fv_corpus + fv_sip
        else:
            total_nps_corpus = current_nps

        annuity_rate = 6.0 # Standard expected annuity rate
        nps_annuity_corpus = total_nps_corpus * 0.40 # 40% mandatory annuity
        nps_lumpsum = total_nps_corpus * 0.60 # 60% tax-free withdrawal
        nps_monthly_pension = (nps_annuity_corpus * (annuity_rate / 100)) / 12
        
        # --- DISPLAY RESULTS ---
        st.markdown(f"### 📊 Total Expected Service: {total_service} Years")
        
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            st.success("### Unified Pension Scheme (UPS)")
            st.metric("Guaranteed Monthly Pension", f"₹ {int(ups_monthly_pension):,}")
            st.metric("Superannuation Lumpsum", f"₹ {int(ups_lumpsum):,}")
            st.write(f"*{ups_note}*")
            st.write("*Note: UPS pension is indexed to inflation (DR).*")

        with res_col2:
            st.info("### National Pension System (NPS)")
            st.metric(f"Expected Monthly Pension (@{annuity_rate}% Annuity)", f"₹ {int(nps_monthly_pension):,}")
            st.metric("Tax-Free Lumpsum (60%)", f"₹ {int(nps_lumpsum):,}")
            st.write(f"*Total Estimated Corpus: ₹ {int(total_nps_corpus):,}*")
            st.write("*Note: NPS pension is fixed and NOT indexed to inflation.*")

        # --- PDF GENERATOR FOR TAB 3 ---
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
            pdf.cell(0, 8, f"Date: {date.today().strftime('%B %d, %Y')}", ln=True)
            pdf.cell(0, 8, f"Prepared For: {emp_name}", ln=True)
            pdf.cell(0, 8, f"Total Estimated Service: {total_service} Years", ln=True)
            pdf.ln(5)
            
            pdf.set_font("Helvetica", 'B', 12)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 10, " 1. UNIFIED PENSION SCHEME (UPS) PROJECTION", ln=True, fill=True)
            pdf.set_font("Helvetica", '', 11)
            pdf.cell(0, 8, f"Guaranteed Monthly Pension: Rs. {int(ups_monthly_pension):,} (Indexed to Inflation)", ln=True)
            pdf.cell(0, 8, f"Superannuation Lumpsum: Rs. {int(ups_lumpsum):,}", ln=True)
            pdf.ln(5)
            
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(0, 10, " 2. NATIONAL PENSION SYSTEM (NPS) PROJECTION", ln=True, fill=True)
            pdf.set_font("Helvetica", '', 11)
            pdf.cell(0, 8, f"Expected NPS Return Assumed: {nps_cagr}%", ln=True)
            pdf.cell(0, 8, f"Total Estimated Corpus: Rs. {int(total_nps_corpus):,}", ln=True)
            pdf.cell(0, 8, f"Expected Monthly Pension: Rs. {int(nps_monthly_pension):,} (Assuming {annuity_rate}% Annuity)", ln=True)
            pdf.cell(0, 8, f"Tax-Free Lumpsum (60%): Rs. {int(nps_lumpsum):,}", ln=True)
            pdf.ln(10)
            
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 6, "Moneyplan Financial Services", ln=True)
            pdf.set_font("Helvetica", '', 10)
            pdf.cell(0, 6, "AMFI Registered Mutual Fund Distributor", ln=True)
            pdf.cell(0, 6, "Nashik & Pune", ln=True)
            pdf.ln(10)
            
            pdf.set_text_color(120, 120, 120)
            pdf.set_font("Helvetica", 'I', 8)
            disclaimer = "STANDARD DISCLAIMER: This report is auto-generated for illustration purposes only. NPS returns are subject to market risks. UPS rules are subject to final government gazette notifications. This does not constitute binding financial, legal, or tax advice."
            pdf.multi_cell(0, 4, disclaimer)
            
            return bytes(pdf.output())

        st.markdown("---")
        st.download_button(
            label="📄 Download UPS vs NPS Report (PDF)",
            data=generate_ups_pdf(),
            file_name=f"{emp_name.replace(' ', '_')}_UPS_vs_NPS_Report.pdf",
            mime="application/pdf"
        )
