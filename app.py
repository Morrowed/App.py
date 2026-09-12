from datetime import datetime, date
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Household Retirement Monte Carlo Simulator",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Household Retirement Monte Carlo Simulator")
st.caption("Stress-test your joint retirement readiness across thousands of randomized market sequences.")

today = date.today()
# Allow dates all the way back to 1920 for birthdates
MIN_ALLOWED_DATE = date(1920, 1, 1)
MAX_ALLOWED_DATE = date(2100, 12, 31)

# =========================================================
# SIDEBAR: USER INPUTS (BLANK DEFAULTS)
# =========================================================
st.sidebar.header("Partner 1")
p1_dob = st.sidebar.date_input(
    "Partner 1 Birthdate",
    value=date(1970, 1, 1),
    min_value=MIN_ALLOWED_DATE,
    max_value=MAX_ALLOWED_DATE
)
p1_retire_date = st.sidebar.date_input(
    "Partner 1 Target Retirement Date",
    value=today,
    min_value=MIN_ALLOWED_DATE,
    max_value=MAX_ALLOWED_DATE
)
p1_ss_age = st.sidebar.number_input("Partner 1 SS Claim Age", min_value=62, max_value=70, value=67)
p1_ss_monthly = st.sidebar.number_input("Partner 1 Monthly SS Benefit ($)", min_value=0.0, value=0.0, step=100.0)

st.sidebar.subheader("Partner 1 Balances")
p1_401k = st.sidebar.number_input("Partner 1 401(k) ($)", min_value=0.0, value=0.0, step=5000.0)
p1_ira = st.sidebar.number_input("Partner 1 Traditional IRA ($)", min_value=0.0, value=0.0, step=5000.0)
p1_roth = st.sidebar.number_input("Partner 1 Roth Accounts ($)", min_value=0.0, value=0.0, step=5000.0)
p1_other = st.sidebar.number_input("Partner 1 Other / Taxable ($)", min_value=0.0, value=0.0, step=5000.0)

st.sidebar.markdown("---")
st.sidebar.header("Partner 2")
p2_dob = st.sidebar.date_input(
    "Partner 2 Birthdate",
    value=date(1970, 1, 1),
    min_value=MIN_ALLOWED_DATE,
    max_value=MAX_ALLOWED_DATE
)
p2_retire_date = st.sidebar.date_input(
    "Partner 2 Target Retirement Date",
    value=today,
    min_value=MIN_ALLOWED_DATE,
    max_value=MAX_ALLOWED_DATE
)
p2_ss_age = st.sidebar.number_input("Partner 2 SS Claim Age", min_value=62, max_value=70, value=67)
p2_ss_monthly = st.sidebar.number_input("Partner 2 Monthly SS Benefit ($)", min_value=0.0, value=0.0, step=100.0)

st.sidebar.subheader("Partner 2 Balances")
p2_401k = st.sidebar.number_input("Partner 2 401(k) ($)", min_value=0.0, value=0.0, step=5000.0)
p2_ira = st.sidebar.number_input("Partner 2 Traditional IRA ($)", min_value=0.0, value=0.0, step=5000.0)
p2_roth = st.sidebar.number_input("Partner 2 Roth Accounts ($)", min_value=0.0, value=0.0, step=5000.0)
p2_other = st.sidebar.number_input("Partner 2 Other / Taxable ($)", min_value=0.0, value=0.0, step=5000.0)

st.sidebar.markdown("---")
st.sidebar.header("Household & Assumptions")
joint_cash = st.sidebar.number_input("Joint Cash / Reserves ($)", min_value=0.0, value=0.0, step=5000.0)
annual_spending = st.sidebar.number_input("Target Annual Spending ($)", min_value=0.0, value=0.0, step=1000.0)

expected_return = st.sidebar.slider("Expected Nominal Return (%)", min_value=1.0, max_value=15.0, value=7.0, step=0.25) / 100.0
volatility = st.sidebar.slider("Market Volatility / StDev (%)", min_value=1.0, max_value=25.0, value=12.0, step=0.5) / 100.0
inflation_rate = st.sidebar.slider("Annual Inflation Rate (%)", min_value=0.0, max_value=8.0, value=2.5, step=0.1) / 100.0
num_simulations = st.sidebar.select_slider("Number of Simulations", options=[1000, 2500, 5000], value=2500)

# =========================================================
# CALCULATIONS & ENGINE
# =========================================================
p1_current_age = max(0.0, (today - p1_dob).days / 365.25)
p2_current_age = max(0.0, (today - p2_dob).days / 365.25)

p1_retire_years = max(0.0, (p1_retire_date - today).days / 365.25)
p2_retire_years = max(0.0, (p2_retire_date - today).days / 365.25)

p1_ss_years = max(0.0, p1_ss_age - p1_current_age)
p2_ss_years = max(0.0, p2_ss_age - p2_current_age)

total_portfolio = (
    p1_401k + p1_ira + p1_roth + p1_other +
    p2_401k + p2_ira + p2_roth + p2_other +
    joint_cash
)

p1_ss_annual = p1_ss_monthly * 12.0
p2_ss_annual = p2_ss_monthly * 12.0

SIM_YEARS = 35

# Gracefully handle the start screen before the user has entered data
if total_portfolio == 0 and annual_spending == 0:
    st.info("👈 Open the sidebar menu on the left and enter your details to start the simulation.")
    st.stop()

np.random.seed(42)
portfolio_paths = np.zeros((SIM_YEARS + 1, num_simulations))
portfolio_paths[0, :] = total_portfolio
success_count = 0

for sim in range(num_simulations):
    balance = total_portfolio
    annual_returns = np.random.normal(expected_return, volatility, SIM_YEARS)
    
    for t in range(SIM_YEARS):
        inflation_factor = (1 + inflation_rate) ** t
        balance *= (1 + annual_returns[t])
        
        # Withdrawals begin once either partner hits their target date
        if t >= min(p1_retire_years, p2_retire_years):
            spending = annual_spending * inflation_factor
            p1_ss = (p1_ss_annual * inflation_factor) if t >= p1_ss_years else 0.0
            p2_ss = (p2_ss_annual * inflation_factor) if t >= p2_ss_years else 0.0
            
            net_draw = spending - (p1_ss + p2_ss)
            if net_draw > 0:
                balance -= net_draw
                
        if balance < 0:
            balance = 0.0
            
        portfolio_paths[t + 1, sim] = balance
        
    if balance > 0:
        success_count += 1

success_rate = (success_count / num_simulations) * 100

# =========================================================
# DASHBOARD DISPLAY
# =========================================================
col1, col2, col3 = st.columns(3)
col1.metric("Total Starting Portfolio", f"${total_portfolio:,.0f}")
col2.metric(
    "Probability of Success",
    f"{success_rate:.1f}%",
    delta="Strong" if success_rate >= 85 else ("Moderate" if success_rate >= 70 else "At Risk"),
    delta_color="normal" if success_rate >= 85 else "inverse"
)
col3.metric("Combined Annual SS (Future)", f"${(p1_ss_annual + p2_ss_annual):,.0f}/yr")

st.markdown("---")

# Trajectory Chart
percentiles = [10, 25, 50, 75, 90]
percentile_curves = np.percentile(portfolio_paths, percentiles, axis=1)
years_index = np.arange(SIM_YEARS + 1)

fig = go.Figure()
fig.add_trace(go.Scatter(x=years_index, y=percentile_curves[4], name="90th Percentile (Optimistic)", line=dict(color="#2ca02c", dash="dot")))
fig.add_trace(go.Scatter(x=years_index, y=percentile_curves[2], name="50th Percentile (Median)", line=dict(color="#1f77b4", width=3)))
fig.add_trace(go.Scatter(x=years_index, y=percentile_curves[0], name="10th Percentile (Pessimistic)", line=dict(color="#d62728", dash="dash")))

fig.update_layout(
    title="Portfolio Balance Trajectories (Next 35 Years)",
    xaxis_title="Years from Today",
    yaxis_title="Portfolio Balance ($)",
    hovermode="x unified",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# Milestone Data Table
milestone_years = sorted(list(set([
    0,
    int(round(p1_retire_years)),
    int(round(p1_ss_years)),
    int(round(p2_retire_years)),
    int(round(p2_ss_years)),
    SIM_YEARS
])))
milestone_years = [y for y in milestone_years if y <= SIM_YEARS]

df = pd.DataFrame(
    percentile_curves.T,
    index=years_index,
    columns=[f"p{p}" for p in percentiles]
)
df["P1 Age"] = np.round(p1_current_age + years_index, 1)
df["P2 Age"] = np.round(p2_current_age + years_index, 1)

summary_table = df.loc[milestone_years, ["P1 Age", "P2 Age", "p10", "p50", "p90"]].copy()
summary_table.rename(columns={
    "p10": "10th %ile ($)",
    "p50": "Median ($)",
    "p90": "90th %ile ($)"
}, inplace=True)

for col in ["10th %ile ($)", "Median ($)", "90th %ile ($)"]:
    summary_table[col] = summary_table[col].map(lambda x: f"${x:,.0f}")

st.subheader("Key Milestone Balances")
st.dataframe(summary_table.reset_index(drop=True), use_container_width=True)
