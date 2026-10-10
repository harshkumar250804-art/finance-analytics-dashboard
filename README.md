# 💰 Personal Finance Analytics & ML Forecasting Dashboard

A comprehensive, B.Tech 2nd-Year Mini Project for **Data Analytics, Interactive Visualization, and Machine Learning Forecasting** built using **Python, Streamlit, Pandas, Plotly, and Scikit-Learn**.

---

## 📌 Features & Highlights

### 📝 1. Manual Expense Logging & Quick Tax Calculator
- **Type Custom Transactions**: Users can manually type and log expense or income transactions (date, category, amount, payment mode, description).
- **Real-Time Recalculation**: Submitting a transaction instantly recalculates all top KPI metrics, category charts, budget alerts, and ML predictions.
- **Quick Expense & GST Calculator**: Interactive tool to sum multiple item prices, apply customizable GST/tax rates, and view grand total before logging.

### 📁 2. Custom CSV Upload & Validation
- **Upload Your Own CSV**: Users can upload their bank/expense CSV transaction history directly via the sidebar.
- **Automated Validation & Fallbacks**: Validates required columns (`Date`, `Category`, `Type`, `Amount`) with automatic default fallbacks for payment modes and transaction descriptions.
- **Template Download**: Downloadable sample CSV template provided.

### 🎯 3. Budget vs. Actual Warning Alert System
- **Category-Wise Budget Allocations**: Customizable monthly spending limits per category.
- **Real-Time Warning Banners**:
  - 🚨 **Red Critical Alert**: Displays an explicit banner if spending exceeds 100% of the set budget.
  - ⚠️ **Yellow Caution Warning**: Triggers when category spending reaches ≥85% of budget limits.
  - 🎉 **Green Safe Indicator**: Confirms when spending stays well within budget parameters.

### 🔮 4. Machine Learning Expense Forecasting
- **Time-Series Regression**: Uses `scikit-learn` Linear Regression to model historical monthly expenditures and predict next month's expected expenses.
- **Algorithm Options**: Toggle between **Linear Regression (Scikit-Learn)** and **3-Month Moving Average**.
- **Model Performance Metrics**: Displays **R² Accuracy Score**, **Mean Absolute Error (MAE)**, and **Monthly Expenditure Slope/Trend**.

---

## 🗂️ Project Structure

```
Finance Analytics Dashboard/
│
├── app.py                  # Main Streamlit UI layout & multi-tab navigation
├── generate_data.py        # Script used to generate synthetic financial datasets
├── requirements.txt        # Dependencies (streamlit, pandas, plotly, scikit-learn)
├── README.md                # Project documentation
├── data/
│   └── finance_data.csv    # Default sample dataset (1200+ transactions)
└── utils/
    └── helper.py            # Core analytics, CSV loading, budget check & ML forecasting
```

---

## ⚙️ Installation & Running

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch Streamlit Dashboard**:
   ```bash
   streamlit run app.py
   ```

3. Open `http://localhost:8501` in your browser.

---

## 🛠️ Tech Stack & Concepts

- **Python 3.10+**: Core programming language.
- **Streamlit**: Web application framework and dynamic reactive UI.
- **Pandas**: DataFrame vectorization, time-series conversion, data aggregation.
- **Plotly Express & Graph Objects**: Interactive financial charts (Bar, Donut, Line, Scatter).
- **Scikit-Learn (`sklearn.linear_model.LinearRegression`)**: Machine learning model for expense trend fitting and next-month predictive forecasting.

---

## 📄 License
Created for academic demonstration & learning purposes (B.Tech Computer Science / Data Science Mini Project).
