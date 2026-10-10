"""
generate_data.py
-----------------
This script generates a realistic sample dataset of personal finance
transactions and saves it as data/finance_data.csv

Run this file once to (re)create the dataset:
    python generate_data.py
"""

import random
from datetime import date, timedelta
import pandas as pd

# Make results repeatable every time the script is run
random.seed(42)

# ---------------------------------------------------------
# 1. Basic setup - date range, categories, payment modes
# ---------------------------------------------------------

START_DATE = date(2023, 1, 1)
END_DATE = date(2024, 12, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days

PAYMENT_MODES = ["Cash", "UPI", "Debit Card", "Credit Card", "Bank Transfer"]

# Each category is mapped to:
#   type -> Income / Expense
#   amount_range -> (min, max) rupees for a single transaction
CATEGORY_INFO = {
    "Salary":       {"type": "Income",  "range": (35000, 65000)},
    "Freelancing":  {"type": "Income",  "range": (2000, 20000)},
    "Investment":   {"type": "Income",  "range": (500, 15000)},
    "Food":         {"type": "Expense", "range": (100, 1500)},
    "Rent":         {"type": "Expense", "range": (8000, 18000)},
    "Shopping":     {"type": "Expense", "range": (300, 6000)},
    "Travel":       {"type": "Expense", "range": (200, 5000)},
    "Bills":        {"type": "Expense", "range": (500, 4000)},
    "Entertainment":{"type": "Expense", "range": (150, 2500)},
    "Healthcare":   {"type": "Expense", "range": (200, 8000)},
    "Education":    {"type": "Expense", "range": (500, 10000)},
    "Other":        {"type": "Expense", "range": (100, 3000)},
}

# Simple description templates for each category (adds a bit of realism)
DESCRIPTIONS = {
    "Salary": ["Monthly salary credited", "Salary payment", "Company payroll"],
    "Freelancing": ["Freelance project payment", "Client payment received", "Gig work income"],
    "Investment": ["Dividend received", "Mutual fund returns", "Stock sale profit"],
    "Food": ["Groceries", "Restaurant bill", "Online food order", "Snacks and beverages"],
    "Rent": ["Monthly house rent", "Rent payment to landlord"],
    "Shopping": ["Clothing purchase", "Online shopping order", "Electronics purchase"],
    "Travel": ["Cab fare", "Bus ticket", "Fuel expense", "Flight booking"],
    "Bills": ["Electricity bill", "Water bill", "Mobile recharge", "Internet bill"],
    "Entertainment": ["Movie tickets", "Streaming subscription", "Concert tickets"],
    "Healthcare": ["Doctor consultation", "Medicine purchase", "Health checkup"],
    "Education": ["Course fee", "Book purchase", "Tuition fee"],
    "Other": ["Miscellaneous expense", "Gift purchase", "Donation"],
}

# Weight (probability) of each category appearing.
# Income categories occur less often than everyday expenses.
CATEGORY_WEIGHTS = {
    "Salary": 5,
    "Freelancing": 4,
    "Investment": 4,
    "Food": 20,
    "Rent": 3,
    "Shopping": 12,
    "Travel": 10,
    "Bills": 8,
    "Entertainment": 9,
    "Healthcare": 6,
    "Education": 5,
    "Other": 8,
}

CATEGORIES = list(CATEGORY_INFO.keys())
WEIGHTS = [CATEGORY_WEIGHTS[c] for c in CATEGORIES]

# ---------------------------------------------------------
# 2. Generate transactions
# ---------------------------------------------------------

NUM_TRANSACTIONS = 1200  # more than the required 1000

rows = []
for _ in range(NUM_TRANSACTIONS):
    # Pick a random category based on weights
    category = random.choices(CATEGORIES, weights=WEIGHTS, k=1)[0]
    info = CATEGORY_INFO[category]

    # Random date within the range
    random_day = random.randint(0, TOTAL_DAYS)
    txn_date = START_DATE + timedelta(days=random_day)

    # Random amount within the category's typical range
    low, high = info["range"]
    amount = round(random.uniform(low, high), 2)

    # Salary is usually paid once a month - round it to nearest 100 for realism
    if category == "Salary":
        amount = round(amount / 100) * 100

    payment_mode = random.choice(PAYMENT_MODES)
    description = random.choice(DESCRIPTIONS[category])

    rows.append({
        "Date": txn_date,
        "Category": category,
        "Type": info["type"],
        "Amount": amount,
        "Payment Mode": payment_mode,
        "Description": description,
    })

# ---------------------------------------------------------
# 3. Create DataFrame, sort by date, and save to CSV
# ---------------------------------------------------------

df = pd.DataFrame(rows)
df = df.sort_values("Date").reset_index(drop=True)

output_path = "data/finance_data.csv"
df.to_csv(output_path, index=False)

print(f"Generated {len(df)} transactions and saved to '{output_path}'")
