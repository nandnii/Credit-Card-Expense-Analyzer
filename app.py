import streamlit as st
import pandas as pd
from pathlib import Path

from pdf_to_csv_parser import parse_multiple_statements
from cc_expense_tracker import analyze_expenses, generate_summary_stats, find_insights, create_visualizations

# ===============================
# STREAMLIT APP SETTINGS
# ===============================
st.set_page_config(
    page_title="Credit Card Expense Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("💳 Credit Card Expense Analyzer")
st.markdown(
    "Upload your credit card PDF statements and analyze your expenses easily!"
)

# ===============================
# FILE UPLOAD
# ===============================
uploaded_files = st.file_uploader(
    "📂 Upload Credit Card PDF Statements",
    type=["pdf"],
    accept_multiple_files=True
)

csv_file = None

if uploaded_files:
    st.success(f"{len(uploaded_files)} file(s) uploaded")

    # Save uploaded PDFs temporarily
    temp_paths = []
    for f in uploaded_files:
        temp_path = Path(f"temp_{f.name}")
        with open(temp_path, "wb") as out_file:
            out_file.write(f.read())
        temp_paths.append(temp_path)

    # Parse PDFs to DataFrame
    df = parse_multiple_statements(temp_paths)
    if df is not None:
        csv_file = "all_transactions_combined.csv"
        df.to_csv(csv_file, index=False)
        st.success(f"✅ Parsed {len(df)} transactions from {len(uploaded_files)} PDFs!")

# else:
#     st.warning("Upload PDFs to start analysis. Alternatively, provide a CSV.")
#     csv_file_path = st.file_uploader("Or upload CSV file directly", type=["csv"])
#     if csv_file_path:
#         csv_file = csv_file_path
#         df = pd.read_csv(csv_file)
#         st.success(f"✅ Loaded CSV with {len(df)} transactions!")

# ===============================
# ANALYSIS DISPLAY
# ===============================
if csv_file:
    st.header("📊 Expense Summary")

    # Use analyzer to get DataFrame back
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', 'amount'])

    # -----------------------------
    # Overall Stats
    # -----------------------------
    # st.markdown("### 💰 Overall Statistics")
    # st.markdown(f"**Total Spent:** ₹{df['amount'].sum():,.2f}")
    # st.markdown(f"**Total Transactions:** {len(df):,}")
    # st.markdown(f"**Highest Transaction:** ₹{df['amount'].max():,.2f}")
    # st.markdown(f"**Average Transaction:** ₹{df['amount'].mean():,.2f}")
    # st.markdown(f"**Date Range:** {df['date'].min().strftime("%d %b %y")} → {df['date'].max().strftime("%d %b %y")}")
    
    # One-line impactful summary
    total_spent = df['amount'].sum()
    total_txns = len(df)
    highest_txn = df['amount'].max()
    date_start = df['date'].min().strftime("%d %b %y")
    date_end = df['date'].max().strftime("%d %b %y")

    summary_text = f"💰 You spent ₹{total_spent:,.2f} between {date_start} → {date_end}, with the highest transaction being ₹{highest_txn:,.2f}"

    # Bigger text using markdown header (h2)
    st.markdown(f"#### {summary_text}")

    # -----------------------------
    # Spending by Card
    # -----------------------------
    st.markdown("\n### 💳 Spending by Card")
    card_summary = df.groupby('card')['amount'].agg(['sum', 'count']).sort_values('sum', ascending=False)
    for card, row in card_summary.iterrows():
        st.markdown(f"- **{card}**: ₹{row['sum']:,.2f} | {int(row['count'])} txns")

    # -----------------------------
    # Spending by Category
    # -----------------------------
    st.markdown("\n### 🏷️ Spending by Category")
    cat_summary = df.groupby('category')['amount'].agg(['sum', 'count', 'mean']).sort_values('sum', ascending=False)
    for category, row in cat_summary.iterrows():
        st.markdown(f"- **{category}**: ₹{row['sum']:,.2f} | {int(row['count'])} txns")
    # cat_df = pd.DataFrame({
    #     "Category": cat_summary.index,
    #     "Total (₹)": cat_summary['sum'].values,
    #     "Transactions": cat_summary['count'].values,
    #     "Average (₹)": cat_summary['mean'].values
    # })
    # st.dataframe(cat_df.style.format({"Total (₹)": "₹{:,.2f}", "Average (₹)": "₹{:,.2f}"}))

    # # -----------------------------
    # # Top Merchants
    # # -----------------------------
    # st.markdown("### 🏪 Top 10 Merchants")
    # top_merchants = df.groupby('merchant')['amount'].sum().sort_values(ascending=False).head(10)
    # for i, (merchant, amt) in enumerate(top_merchants.items(), 1):
    #     merchant_display = merchant[:40] + "..." if len(merchant) > 40 else merchant
    #     st.markdown(f"{i}. **{merchant_display}**: ₹{amt:,.2f}")

    # -----------------------------
    # TABLE
    # -----------------------------
    # Copy df to avoid changing original
    df_display = df.sort_values('date', ascending=True).copy()

    # Format date column as "21 Jan 25"
    df_display['date'] = df_display['date'].dt.strftime("%d %b %y")
    df_display = df_display.drop(columns=['bank', 'year_month'])
    df_display['amount'] = df_display['amount'].apply(lambda x: f"₹{x:,.2f}")

    df_display.columns = [col.capitalize() for col in df_display.columns]

    # Show dataframe without index
    st.markdown("\n### 📄 All Transactions")
    st.dataframe(df_display.style.hide(axis="index"))

    # -----------------------------
    # Optional: Visualizations
    # -----------------------------
    st.markdown("\n### 📈 Visualizations")
    fig = create_visualizations(
        df,
        figsize=(18, 18),  # bigger figure
        dpi=300            # higher resolution
    )

    # Display in Streamlit
    st.pyplot(fig)

    st.success("🎉 Analysis complete!")

