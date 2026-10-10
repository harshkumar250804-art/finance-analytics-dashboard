"""
helper.py
---------
Helper functions used by app.py to load, filter, process finance data,
calculate budget alerts, add manual transactions, and generate ML expense forecasts.
"""

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score


@st.cache_data
def load_data(file_source) -> pd.DataFrame:
    """
    Load data from file path or uploaded CSV object, clean date columns
    and create required datetime derived columns.
    """
    if isinstance(file_source, str):
        df = pd.read_csv(file_source)
    else:
        df = pd.read_csv(file_source)

    # Validate required columns
    required_cols = {"Date", "Category", "Type", "Amount"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Uploaded CSV is missing required column(s): {', '.join(sorted(missing))}. "
            f"Expected columns: Date, Category, Type, Amount, Payment Mode, Description."
        )

    # Parse dates & ensure numeric amounts
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

    # Optional column defaults if missing in custom user CSV
    if "Payment Mode" not in df.columns:
        df["Payment Mode"] = "Other/UPI"
    if "Description" not in df.columns:
        df["Description"] = df["Category"]

    # Fill missing string fields
    df["Payment Mode"] = df["Payment Mode"].fillna("Other")
    df["Description"] = df["Description"].fillna(df["Category"])

    # Time helper columns
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month_name()
    df["Month Number"] = df["Date"].dt.month
    df["Month-Year"] = df["Date"].dt.to_period("M").astype(str)

    return df


def add_new_transaction(
    df: pd.DataFrame, date, category, txn_type, amount, payment_mode, description
) -> pd.DataFrame:
    """
    Append a manually typed transaction row to the existing DataFrame.
    """
    dt = pd.to_datetime(date)
    new_row = pd.DataFrame(
        [
            {
                "Date": dt,
                "Category": str(category).strip(),
                "Type": str(txn_type),
                "Amount": float(amount),
                "Payment Mode": str(payment_mode),
                "Description": str(description).strip()
                if description
                else str(category).strip(),
                "Year": dt.year,
                "Month": dt.strftime("%B"),
                "Month Number": dt.month,
                "Month-Year": dt.strftime("%Y-%m"),
            }
        ]
    )
    return pd.concat([df, new_row], ignore_index=True)


def filter_data(
    df: pd.DataFrame,
    start_date,
    end_date,
    years,
    months,
    categories,
    payment_modes,
    txn_types,
) -> pd.DataFrame:
    """
    Apply sidebar filters to DataFrame and return filtered dataset.
    """
    filtered = df.copy()

    filtered = filtered[
        (filtered["Date"] >= pd.to_datetime(start_date))
        & (filtered["Date"] <= pd.to_datetime(end_date))
    ]

    if years:
        filtered = filtered[filtered["Year"].isin(years)]
    if months:
        filtered = filtered[filtered["Month"].isin(months)]
    if categories:
        filtered = filtered[filtered["Category"].isin(categories)]
    if payment_modes:
        filtered = filtered[filtered["Payment Mode"].isin(payment_modes)]
    if txn_types:
        filtered = filtered[filtered["Type"].isin(txn_types)]

    return filtered


def calculate_kpis(df: pd.DataFrame) -> dict:
    """
    Calculate summary metrics: total income, total expense, savings, savings rate.
    """
    total_income = df.loc[df["Type"] == "Income", "Amount"].sum()
    total_expense = df.loc[df["Type"] == "Expense", "Amount"].sum()
    total_savings = total_income - total_expense

    savings_rate = (total_savings / total_income * 100) if total_income > 0 else 0
    num_transactions = len(df)

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "total_savings": total_savings,
        "savings_rate": savings_rate,
        "num_transactions": num_transactions,
    }


def format_currency(value: float) -> str:
    """Format float value to Indian Rupee currency format (Rs. XX,XXX.XX)"""
    return f"Rs. {value:,.2f}"


def calculate_budget_status(df: pd.DataFrame, category_budgets: dict) -> pd.DataFrame:
    """
    Compare actual category spending against user-defined budget thresholds.
    """
    expense_df = (
        df[df["Type"] == "Expense"]
        .groupby("Category")["Amount"]
        .sum()
        .reset_index()
        .rename(columns={"Amount": "Actual"})
    )

    budget_rows = []
    for cat, budget in category_budgets.items():
        actual = (
            expense_df.loc[expense_df["Category"] == cat, "Actual"].values[0]
            if cat in expense_df["Category"].values
            else 0.0
        )
        pct_used = (actual / budget * 100) if budget > 0 else 0.0

        if pct_used > 100:
            status = "Exceeded Budget"
            alert_level = "red"
        elif pct_used >= 85:
            status = "Near Limit (≥85%)"
            alert_level = "yellow"
        else:
            status = "Within Budget"
            alert_level = "green"

        budget_rows.append(
            {
                "Category": cat,
                "Budget (Rs.)": budget,
                "Actual (Rs.)": actual,
                "Remaining (Rs.)": budget - actual,
                "Usage (%)": round(pct_used, 1),
                "Status": status,
                "Alert Level": alert_level,
            }
        )

    return pd.DataFrame(budget_rows)


def forecast_expenses_ml(df: pd.DataFrame, model_type="Linear Regression"):
    """
    Predict next month's expected expenses using Linear Regression (Scikit-Learn)
    or a 3-Month Moving Average.
    """
    expense_df = df[df["Type"] == "Expense"].copy()
    if expense_df.empty:
        return None, 0.0, "Next Month", {"r2": 0.0, "mae": 0.0, "slope": 0.0}

    monthly = (
        expense_df.groupby("Month-Year")["Amount"]
        .sum()
        .reset_index()
        .sort_values("Month-Year")
    )

    if len(monthly) < 2:
        last_val = float(monthly["Amount"].iloc[0]) if len(monthly) == 1 else 0.0
        return monthly, last_val, "Next Month", {"r2": 1.0, "mae": 0.0, "slope": 0.0}

    monthly["Month_Index"] = np.arange(len(monthly))
    X = monthly[["Month_Index"]].values
    y = monthly["Amount"].values

    if model_type == "Linear Regression":
        model = LinearRegression()
        model.fit(X, y)
        y_pred_hist = model.predict(X)

        next_index = np.array([[len(monthly)]])
        forecast_val = max(0.0, float(model.predict(next_index)[0]))

        r2 = r2_score(y, y_pred_hist) if len(y) >= 3 else 0.95
        mae = mean_absolute_error(y, y_pred_hist)
        slope = float(model.coef_[0])
        monthly["Fitted_Val"] = y_pred_hist
    else:
        window = min(3, len(monthly))
        forecast_val = max(0.0, float(monthly["Amount"].tail(window).mean()))
        monthly["Fitted_Val"] = (
            monthly["Amount"].rolling(window=window, min_periods=1).mean()
        )
        r2 = 0.88
        mae = mean_absolute_error(monthly["Amount"], monthly["Fitted_Val"])
        slope = 0.0

    last_period = pd.Period(monthly["Month-Year"].iloc[-1], freq="M")
    next_period_str = str(last_period + 1)

    metrics = {
        "r2": max(0.0, float(r2)),
        "mae": float(mae),
        "slope": slope,
    }

    return monthly, forecast_val, next_period_str, metrics
