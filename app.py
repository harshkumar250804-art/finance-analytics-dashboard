"""
app.py
------
Finance Analytics & ML Forecasting Dashboard
A comprehensive, B.Tech mini-project dashboard built with Streamlit, Pandas,
Plotly, and Scikit-Learn.

Features:
- Custom CSV File Upload with schema validation
- Manual Expense & Income Entry (type custom transactions with real-time recalculation)
- Multi-dimensional sidebar filters
- Interactive financial metrics & charts
- Budget vs. Actual Alert System with red/yellow warning banners
- Machine Learning Expense Forecasting (Scikit-Learn Linear Regression)
- Quick Expense & Tax Calculator

Run with:
    streamlit run app.py
"""

import datetime
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils.helper import (
    add_new_transaction,
    calculate_budget_status,
    calculate_kpis,
    filter_data,
    forecast_expenses_ml,
    format_currency,
    load_data,
)

# ---------------------------------------------------------
# 1. Page Configuration & Custom CSS
# ---------------------------------------------------------

st.set_page_config(
    page_title="Finance Analytics & ML Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main {
            padding-top: 1rem;
        }
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .stAlert {
            border-radius: 8px;
        }
        h1, h2, h3 {
            color: #0f172a;
            font-weight: 700;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. Sidebar - Data Source Selection & Session State Management
# ---------------------------------------------------------

st.sidebar.title("📁 Data Source & Filters")

data_source = st.sidebar.radio(
    "Select Data Input Method",
    options=["Use Demo Dataset", "Upload Custom CSV"],
    index=0,
)

DATA_PATH = "data/finance_data.csv"

# Track data source change
if "data_source_mode" not in st.session_state:
    st.session_state["data_source_mode"] = data_source

if st.session_state["data_source_mode"] != data_source:
    st.session_state["data_source_mode"] = data_source
    if "df" in st.session_state:
        del st.session_state["df"]

if data_source == "Upload Custom CSV":
    uploaded_file = st.sidebar.file_uploader(
        "Upload transaction CSV file",
        type=["csv"],
        help="Upload a CSV with columns: Date, Category, Type, Amount (optional: Payment Mode, Description)",
    )
    if uploaded_file is not None:
        if "df" not in st.session_state or st.session_state.get("uploaded_filename") != uploaded_file.name:
            try:
                st.session_state["df"] = load_data(uploaded_file)
                st.session_state["uploaded_filename"] = uploaded_file.name
                st.sidebar.success("✅ Custom CSV uploaded successfully!")
            except Exception as e:
                st.sidebar.error(f"Error reading CSV: {e}")
                st.stop()
    else:
        st.sidebar.info("Upload a CSV file or switch to 'Use Demo Dataset'.")
        sample_csv_text = "Date,Category,Type,Amount,Payment Mode,Description\n2026-01-01,Salary,Income,50000,Bank Transfer,Monthly Salary\n2026-01-05,Rent,Expense,12000,UPI,House Rent\n2026-01-10,Groceries,Expense,3500,Credit Card,Supermarket\n"
        st.sidebar.download_button(
            label="📥 Download Sample CSV Template",
            data=sample_csv_text,
            file_name="sample_finance_template.csv",
            mime="text/csv",
        )
        st.stop()
else:
    if "df" not in st.session_state:
        try:
            st.session_state["df"] = load_data(DATA_PATH)
        except Exception as e:
            st.error(f"Could not load demo dataset at '{DATA_PATH}': {e}")
            st.stop()

# Alias active dataframe
df = st.session_state["df"]

# ---------------------------------------------------------
# 3. Sidebar - Manual Transaction Quick Entry
# ---------------------------------------------------------

with st.sidebar.expander("➕ Add Transaction Manually", expanded=False):
    st.markdown("**Type & record a custom transaction:**")
    with st.form("sidebar_add_form", clear_on_submit=True):
        sb_date = st.date_input("Date", value=datetime.date.today())
        sb_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
        
        existing_cats = sorted(df["Category"].unique().tolist())
        sb_cat_choice = st.selectbox("Category", options=existing_cats + ["+ New Category"])
        if sb_cat_choice == "+ New Category":
            sb_category = st.text_input("Custom Category Name", value="Subscriptions")
        else:
            sb_category = sb_cat_choice

        sb_amount = st.number_input("Amount (Rs.)", min_value=1.0, value=500.0, step=50.0)
        sb_paymode = st.selectbox("Payment Mode", ["UPI", "Credit Card", "Debit Card", "Cash", "Bank Transfer", "Other"])
        sb_desc = st.text_input("Description", placeholder="e.g. Dinner with friends")
        
        sb_submitted = st.form_submit_button("➕ Save & Recalculate")
        if sb_submitted:
            if not sb_category.strip():
                st.error("Please enter a valid category name.")
            else:
                st.session_state["df"] = add_new_transaction(
                    st.session_state["df"],
                    sb_date,
                    sb_category,
                    sb_type,
                    sb_amount,
                    sb_paymode,
                    sb_desc,
                )
                st.success(f"Added {sb_type}: {sb_category} - Rs. {sb_amount:,.2f}")
                st.rerun()

st.sidebar.markdown("---")

# ---------------------------------------------------------
# 4. Sidebar Filters
# ---------------------------------------------------------

st.sidebar.subheader("🔎 Filter Transactions")

min_date, max_date = df["Date"].min(), df["Date"].max()
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

year_options = sorted(df["Year"].unique())
selected_years = st.sidebar.multiselect("Year", options=year_options)

month_options = list(df.sort_values("Month Number")["Month"].unique())
selected_months = st.sidebar.multiselect("Month", options=month_options)

category_options = sorted(df["Category"].unique())
selected_categories = st.sidebar.multiselect("Category", options=category_options)

payment_mode_options = sorted(df["Payment Mode"].unique())
selected_payment_modes = st.sidebar.multiselect(
    "Payment Mode", options=payment_mode_options
)

type_options = sorted(df["Type"].unique())
selected_types = st.sidebar.multiselect("Transaction Type", options=type_options)

filtered_df = filter_data(
    df,
    start_date,
    end_date,
    selected_years,
    selected_months,
    selected_categories,
    selected_payment_modes,
    selected_types,
)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Filtered **{len(filtered_df)}** of **{len(df)}** total transactions"
)

# ---------------------------------------------------------
# 5. Header & Top KPI Cards
# ---------------------------------------------------------

st.title("💰 Finance Analytics & ML Forecasting Dashboard")
st.markdown(
    "An interactive dashboard for tracking income, adding custom transactions, analyzing spending patterns, setting budgets, and forecasting future expenses with Machine Learning."
)
st.markdown("---")

if filtered_df.empty:
    st.warning("No transactions match the selected filters. Please adjust your criteria.")
    st.stop()

kpis = calculate_kpis(filtered_df)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Income", format_currency(kpis["total_income"]))
col2.metric("Total Expenses", format_currency(kpis["total_expense"]))
col3.metric("Total Savings", format_currency(kpis["total_savings"]))
col4.metric("Savings Rate", f"{kpis['savings_rate']:.1f}%")
col5.metric("Transactions", kpis["num_transactions"])

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. Main Content Tabs
# ---------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Analytics & Trends",
        "🎯 Budget vs Actual Alerts",
        "🔮 ML Expense Forecasting",
        "➕ Manual Entry & Calculator",
    ]
)

# =========================================================
# TAB 1: Analytics & Trends
# =========================================================
with tab1:
    st.subheader("📊 Expense & Income Overview")

    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        monthly_summary = (
            filtered_df.groupby(["Month-Year", "Type"])["Amount"].sum().reset_index()
        )
        fig_monthly = px.bar(
            monthly_summary,
            x="Month-Year",
            y="Amount",
            color="Type",
            barmode="group",
            title="Monthly Income vs Expense",
            color_discrete_map={"Income": "#10b981", "Expense": "#ef4444"},
        )
        fig_monthly.update_layout(xaxis_title="Month", yaxis_title="Amount (Rs.)")
        st.plotly_chart(fig_monthly, use_container_width=True)

    with row1_col2:
        expense_by_category = (
            filtered_df[filtered_df["Type"] == "Expense"]
            .groupby("Category")["Amount"]
            .sum()
            .reset_index()
        )
        fig_pie = px.pie(
            expense_by_category,
            names="Category",
            values="Amount",
            title="Expense Breakdown by Category",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        monthly_income = (
            filtered_df[filtered_df["Type"] == "Income"]
            .groupby("Month-Year")["Amount"]
            .sum()
        )
        monthly_expense = (
            filtered_df[filtered_df["Type"] == "Expense"]
            .groupby("Month-Year")["Amount"]
            .sum()
        )
        savings_trend = (monthly_income - monthly_expense).fillna(0).reset_index()
        savings_trend.columns = ["Month-Year", "Savings"]
        savings_trend = savings_trend.sort_values("Month-Year")

        fig_savings = px.line(
            savings_trend,
            x="Month-Year",
            y="Savings",
            title="Monthly Net Savings Trend",
            markers=True,
        )
        fig_savings.update_traces(line_color="#2563eb", line_width=3)
        fig_savings.update_layout(xaxis_title="Month", yaxis_title="Savings (Rs.)")
        st.plotly_chart(fig_savings, use_container_width=True)

    with row2_col2:
        payment_mode_summary = (
            filtered_df[filtered_df["Type"] == "Expense"]
            .groupby("Payment Mode")["Amount"]
            .sum()
            .reset_index()
            .sort_values("Amount", ascending=False)
        )
        fig_payment = px.bar(
            payment_mode_summary,
            x="Payment Mode",
            y="Amount",
            title="Spending Distribution by Payment Mode",
            color="Payment Mode",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_payment.update_layout(
            xaxis_title="Payment Mode", yaxis_title="Amount (Rs.)"
        )
        st.plotly_chart(fig_payment, use_container_width=True)

    row3_col1, row3_col2 = st.columns(2)

    with row3_col1:
        top_categories = (
            filtered_df[filtered_df["Type"] == "Expense"]
            .groupby("Category")["Amount"]
            .sum()
            .reset_index()
            .sort_values("Amount", ascending=False)
            .head(10)
        )
        fig_top = px.bar(
            top_categories,
            x="Amount",
            y="Category",
            orientation="h",
            title="Top Expense Categories",
            color="Amount",
            color_continuous_scale="Reds",
        )
        fig_top.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_top, use_container_width=True)

    with row3_col2:
        daily_expense = (
            filtered_df[filtered_df["Type"] == "Expense"]
            .groupby("Date")["Amount"]
            .sum()
            .reset_index()
        )
        fig_daily = px.line(
            daily_expense,
            x="Date",
            y="Amount",
            title="Daily Expense Trend",
        )
        fig_daily.update_traces(line_color="#f97316")
        fig_daily.update_layout(xaxis_title="Date", yaxis_title="Amount (Rs.)")
        st.plotly_chart(fig_daily, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Transaction Log")

    search_term = st.text_input(
        "🔎 Search transactions (Category, Description, Payment Mode)"
    )

    table_df = filtered_df.copy()
    if search_term:
        mask = (
            table_df["Category"].str.contains(search_term, case=False, na=False)
            | table_df["Description"].str.contains(search_term, case=False, na=False)
            | table_df["Payment Mode"].str.contains(search_term, case=False, na=False)
        )
        table_df = table_df[mask]

    display_df = table_df[
        ["Date", "Category", "Type", "Amount", "Payment Mode", "Description"]
    ].sort_values("Date", ascending=False)

    st.dataframe(display_df, use_container_width=True, height=350)
    
    t_log_col1, t_log_col2 = st.columns([3, 1])
    with t_log_col1:
        st.caption(f"Displaying {len(display_df)} matching transaction records")
    with t_log_col2:
        csv_data = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Export Report (CSV)",
            data=csv_data,
            file_name="finance_analytics_report.csv",
            mime="text/csv",
        )


# =========================================================
# TAB 2: Budget vs Actual Alerts
# =========================================================
with tab2:
    st.subheader("🎯 Category Budget vs. Actual Expenses Alert System")
    st.markdown(
        "Configure your target monthly budget limit per category to monitor real-time spending thresholds and automated alerts."
    )

    expense_categories = sorted(
        df[df["Type"] == "Expense"]["Category"].unique().tolist()
    )

    default_budgets = {}
    total_months = max(1, df["Month-Year"].nunique())
    for cat in expense_categories:
        avg_monthly = (
            df[(df["Type"] == "Expense") & (df["Category"] == cat)]["Amount"].sum()
            / total_months
        )
        default_budgets[cat] = float(round(avg_monthly * 0.9, -2))

    with st.expander("⚙️ Customize Monthly Category Budgets", expanded=False):
        st.info(
            "Adjust the budget allocations below to see how actual spending compares against limits."
        )
        user_budgets = {}
        budget_cols = st.columns(3)
        for idx, cat in enumerate(expense_categories):
            col = budget_cols[idx % 3]
            user_budgets[cat] = col.number_input(
                f"Budget for '{cat}' (Rs.)",
                min_value=100.0,
                max_value=1000000.0,
                value=max(100.0, default_budgets.get(cat, 5000.0)),
                step=500.0,
            )

    budget_df = calculate_budget_status(filtered_df, user_budgets)

    st.markdown("### ⚠️ Real-Time Spending Alert Banners")

    exceeded_items = budget_df[budget_df["Alert Level"] == "red"]
    warning_items = budget_df[budget_df["Alert Level"] == "yellow"]

    if not exceeded_items.empty:
        for _, row in exceeded_items.iterrows():
            st.error(
                f"🚨 **CRITICAL OVER-BUDGET ALERT**: Category **{row['Category']}** has exceeded its budget! "
                f"Spent: **{format_currency(row['Actual (Rs.)'])}** / Budget: **{format_currency(row['Budget (Rs.)'])}** "
                f"(**{row['Usage (%)']:.1f}%** used — Over by {format_currency(abs(row['Remaining (Rs.)']))})"
            )

    if not warning_items.empty:
        for _, row in warning_items.iterrows():
            st.warning(
                f"⚠️ **BUDGET WARNING**: Category **{row['Category']}** is nearing its threshold (≥85%). "
                f"Spent: **{format_currency(row['Actual (Rs.)'])}** / Budget: **{format_currency(row['Budget (Rs.)'])}** "
                f"(**{row['Usage (%)']:.1f}%** used — Remaining: {format_currency(row['Remaining (Rs.)'])})"
            )

    if exceeded_items.empty and warning_items.empty:
        st.success(
            "🎉 **EXCELLENT FINANCIAL DISCIPLINE**: All category expenses are well within budget limits!"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    b_col1, b_col2 = st.columns([3, 2])

    with b_col1:
        fig_budget = go.Figure()
        fig_budget.add_trace(
            go.Bar(
                x=budget_df["Category"],
                y=budget_df["Budget (Rs.)"],
                name="Budget Limit",
                marker_color="#94a3b8",
            )
        )
        fig_budget.add_trace(
            go.Bar(
                x=budget_df["Category"],
                y=budget_df["Actual (Rs.)"],
                name="Actual Expense",
                marker_color=[
                    "#ef4444"
                    if status == "red"
                    else ("#f59e0b" if status == "yellow" else "#10b981")
                    for status in budget_df["Alert Level"]
                ],
            )
        )
        fig_budget.update_layout(
            barmode="group",
            title="Budget vs. Actual Expenses by Category",
            xaxis_title="Category",
            yaxis_title="Amount (Rs.)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_budget, use_container_width=True)

    with b_col2:
        st.markdown("### 📊 Budget Allocation Summary")
        st.dataframe(
            budget_df[
                [
                    "Category",
                    "Budget (Rs.)",
                    "Actual (Rs.)",
                    "Remaining (Rs.)",
                    "Usage (%)",
                    "Status",
                ]
            ],
            column_config={
                "Usage (%)": st.column_config.ProgressColumn(
                    "Usage (%)",
                    format="%.1f%%",
                    min_value=0,
                    max_value=150,
                ),
                "Budget (Rs.)": st.column_config.NumberColumn(format="Rs. %.2f"),
                "Actual (Rs.)": st.column_config.NumberColumn(format="Rs. %.2f"),
                "Remaining (Rs.)": st.column_config.NumberColumn(format="Rs. %.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# TAB 3: ML Expense Forecasting
# =========================================================
with tab3:
    st.subheader("🔮 Machine Learning Expense Forecasting")
    st.markdown(
        "Predict future monthly expenses using Machine Learning time-series regression models fitted on historical expenditure trends."
    )

    ml_col1, ml_col2 = st.columns([1, 2])

    with ml_col1:
        model_choice = st.radio(
            "Select Forecasting Model Algorithm",
            options=["Linear Regression (Scikit-Learn)", "3-Month Moving Average"],
            index=0,
            help="Linear Regression fits a trendline over time using scikit-learn. Moving Average computes recent expenditure mean.",
        )

        model_type_key = (
            "Linear Regression"
            if "Linear Regression" in model_choice
            else "Moving Average"
        )

        monthly_df, next_expense, next_month_str, metrics = forecast_expenses_ml(
            df, model_type=model_type_key
        )

        st.markdown("### 📈 Model Evaluation Metrics")
        m1, m2 = st.columns(2)
        m1.metric("Model R² Score", f"{metrics.get('r2', 0.0):.2f}")
        m2.metric("Mean Abs Error (MAE)", f"Rs. {metrics.get('mae', 0.0):,.0f}")

        if model_type_key == "Linear Regression":
            slope = metrics.get("slope", 0.0)
            trend_str = "Increasing 📈" if slope > 0 else "Decreasing 📉"
            st.info(f"**Monthly Expenditure Trend**: {trend_str} (~Rs. {abs(slope):,.2f} / month)")

        st.success(
            f"🎯 **Predicted Expense for {next_month_str}**:\n"
            f"### **{format_currency(next_expense)}**"
        )

    with ml_col2:
        if monthly_df is not None and not monthly_df.empty:
            fig_ml = go.Figure()

            fig_ml.add_trace(
                go.Scatter(
                    x=monthly_df["Month-Year"],
                    y=monthly_df["Amount"],
                    mode="lines+markers",
                    name="Actual Historical Expense",
                    line=dict(color="#1e293b", width=3),
                    marker=dict(size=8),
                )
            )

            if "Fitted_Val" in monthly_df.columns:
                fig_ml.add_trace(
                    go.Scatter(
                        x=monthly_df["Month-Year"],
                        y=monthly_df["Fitted_Val"],
                        mode="lines",
                        name=f"Fitted Model ({model_type_key})",
                        line=dict(color="#3b82f6", width=2, dash="dash"),
                    )
                )

            last_hist_month = monthly_df["Month-Year"].iloc[-1]
            last_hist_val = monthly_df["Amount"].iloc[-1]

            fig_ml.add_trace(
                go.Scatter(
                    x=[last_hist_month, next_month_str],
                    y=[last_hist_val, next_expense],
                    mode="lines+markers",
                    name=f"Forecasted ({next_month_str})",
                    line=dict(color="#ef4444", width=3, dash="dot"),
                    marker=dict(size=12, symbol="star", color="#ef4444"),
                )
            )

            fig_ml.update_layout(
                title=f"Historical Expenditure vs. ML Forecast ({model_choice})",
                xaxis_title="Month-Year",
                yaxis_title="Expense Amount (Rs.)",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )

            st.plotly_chart(fig_ml, use_container_width=True)

    st.markdown("---")
    st.markdown("### 💡 Financial Planning Advisory & Insights")
    avg_past_expense = monthly_df["Amount"].mean() if monthly_df is not None else 0
    diff_from_avg = next_expense - avg_past_expense

    if diff_from_avg > 0:
        st.warning(
            f"💡 **Recommendation**: Next month's predicted expense of **{format_currency(next_expense)}** is "
            f"**{format_currency(diff_from_avg)}** higher than your historical monthly average ({format_currency(avg_past_expense)}). "
            "Consider reviewing discretionary categories like Shopping & Entertainment."
        )
    else:
        st.info(
            f"💡 **Recommendation**: Next month's predicted expense of **{format_currency(next_expense)}** is "
            f"within your expected average spending range ({format_currency(avg_past_expense)}). Great job keeping spending controlled!"
        )


# =========================================================
# TAB 4: Manual Entry & Quick Expense Calculator
# =========================================================
with tab4:
    st.subheader("➕ Manual Transaction Logging & Quick Calculator")
    st.markdown(
        "Type in your manual expenses or income transactions to update all metrics, charts, and forecasts in real time, or use the quick expense tax calculator."
    )

    t4_col1, t4_col2 = st.columns([1, 1])

    with t4_col1:
        st.markdown("### 📝 Manual Transaction Form")
        with st.form("tab4_manual_form", clear_on_submit=True):
            f_date = st.date_input("Transaction Date", value=datetime.date.today())
            f_type = st.radio("Transaction Type", ["Expense", "Income"], horizontal=True)

            existing_cats_t4 = sorted(df["Category"].unique().tolist())
            f_cat_choice = st.selectbox("Category", options=existing_cats_t4 + ["+ Create New Category"])

            if f_cat_choice == "+ Create New Category":
                f_category = st.text_input("New Category Name", value="Personal")
            else:
                f_category = f_cat_choice

            f_amount = st.number_input("Amount (Rs.)", min_value=1.0, value=1200.0, step=100.0)
            f_paymode = st.selectbox(
                "Payment Mode",
                ["UPI", "Credit Card", "Debit Card", "Cash", "Bank Transfer", "Other"],
            )
            f_desc = st.text_input("Description / Notes", placeholder="e.g. Grocery shopping at D-Mart")

            f_submitted = st.form_submit_button("➕ Submit & Calculate Expense")

            if f_submitted:
                if not f_category.strip():
                    st.error("Please enter a category name.")
                else:
                    st.session_state["df"] = add_new_transaction(
                        st.session_state["df"],
                        f_date,
                        f_category,
                        f_type,
                        f_amount,
                        f_paymode,
                        f_desc,
                    )
                    st.success(
                        f"✅ Successfully added **{f_type}** of **Rs. {f_amount:,.2f}** under **{f_category}**!"
                    )
                    st.rerun()

    with t4_col2:
        st.markdown("### 🧮 Quick Expense & Tax Calculator")
        st.info("Calculate total expenses with tax (GST) and check their budget impact before adding.")

        calc_items = st.text_area(
            "Enter Item Amounts (separated by commas or new lines)",
            value="450, 1200, 350, 800",
            help="Example: 450, 1200, 350",
            height=100,
        )

        tax_rate = st.slider("Tax / GST Rate (%)", min_value=0.0, max_value=28.0, value=18.0, step=1.0)

        # Parse amounts
        parsed_amounts = []
        for line in calc_items.replace(",", "\n").splitlines():
            line_str = line.strip()
            if line_str:
                try:
                    parsed_amounts.append(float(line_str))
                except ValueError:
                    pass

        subtotal = sum(parsed_amounts)
        tax_amount = subtotal * (tax_rate / 100.0)
        grand_total = subtotal + tax_amount

        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Subtotal", format_currency(subtotal))
        c_m2.metric(f"Tax ({tax_rate:.0f}%)", format_currency(tax_amount))
        c_m3.metric("Grand Total", format_currency(grand_total))

        st.caption(f"Calculated from {len(parsed_amounts)} item entries.")


# ---------------------------------------------------------
# 7. Footer
# ---------------------------------------------------------

st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#64748b;'>Finance Analytics & ML Dashboard | Built with Streamlit, Pandas, Plotly & Scikit-Learn</p>",
    unsafe_allow_html=True,
)
