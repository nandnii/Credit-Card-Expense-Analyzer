# 💳 Credit Card Expense Analyzer

A **Python-based tool** to analyze your credit card statements (PDFs) and generate **insights, visualizations, and a transaction table**. This project allows you to quickly see your spending patterns across banks, categories, and merchants.

---

## 🚀 Features

- Upload **one or multiple PDF credit card statements**.
- Automatically **parse PDFs** into a unified CSV.
- **Generate summary statistics**:
  - Total spent
  - Highest transaction
  - Time Duration
- **Spending breakdowns**:
  - By card
  - By category
- **Interactive transactions table**:
  - Downloadable CSV
- **Visualizations**:
  - Spending by category
  - Spending by card
  - Monthly trend
  - Top merchants
  - Transaction counts by category
- Fully built with **Streamlit** for an interactive web experience.

---

## 🗂 Project Structure
credit-card-analyzer/
├─ app.py                   # Main Streamlit app
├─ pdf_to_csv_parser.py     # PDF to CSV parser
├─ cc_expense_tracker.py    # Analysis and visualization functions
├─ requirements.txt         # Python dependencies
└─ README.md                # This file
