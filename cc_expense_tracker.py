"""
Credit Card Expense Analyzer
Analyzes parsed credit card data and generates insights + visualizations

Requires: parser.py (the PDF parser)

Usage:
    python analyzer.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import the parser
try:
    from pdf_to_csv_parser import parse_multiple_statements
    PARSER_AVAILABLE = True
except ImportError:
    print("Warning: parser.py not found. You'll need to load CSV files manually.")
    PARSER_AVAILABLE = False

# Set plotting style
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def generate_summary_stats(df):
    """Generate summary statistics"""
    
    print("\n" + "="*70)
    print("📊 EXPENSE ANALYSIS SUMMARY")
    print("="*70)
    
    # Overall stats
    print(f"\n💰 Overall Statistics:")
    print(f"   Total Transactions: {len(df):,}")
    print(f"   Total Spent: Rs. {df['amount'].sum():,.2f}")
    print(f"   Average Transaction: Rs. {df['amount'].mean():,.2f}")
    print(f"   Median Transaction: Rs. {df['amount'].median():,.2f}")
    start = df['date'].min().strftime("%d %b %y")
    end = df['date'].max().strftime("%d %b %y")
    print(f"   Date Range: {start} → {end}")    
    
    # Spending by bank/card
    print(f"\n💳 Spending by Card:")
    card_totals = df.groupby('card')['amount'].agg(['sum', 'count']).sort_values('sum', ascending=False)
    for card, row in card_totals.iterrows():
        percentage = (row['sum'] / df['amount'].sum()) * 100
        print(f"   {card}: Rs. {row['sum']:,.2f} ({percentage:.1f}%) | {int(row['count'])} transactions")
    
    # Spending by category
    print(f"\n🏷️  Spending by Category:")
    category_totals = df.groupby('category')['amount'].agg(['sum', 'count']).sort_values('sum', ascending=False)
    for category, row in category_totals.iterrows():
        percentage = (row['sum'] / df['amount'].sum()) * 100
        avg = row['sum'] / row['count']
        print(f"   {category:20s}: Rs. {row['sum']:>10,.2f} ({percentage:>5.1f}%) | {int(row['count']):>3} txns | Avg: Rs. {avg:>8,.2f}")
    
    # Top merchants
    print(f"\n🏪 Top 15 Merchants:")
    top_merchants = df.groupby('merchant')['amount'].sum().sort_values(ascending=False).head(15)
    for i, (merchant, total) in enumerate(top_merchants.items(), 1):
        # Truncate long merchant names
        merchant_display = merchant[:45] + '...' if len(merchant) > 45 else merchant
        print(f"   {i:2d}. {merchant_display:48s} Rs. {total:>10,.2f}")
    
    # Monthly breakdown
    if 'year_month' in df.columns:
        print(f"\n📅 Monthly Spending:")
        monthly = df.groupby('year_month')['amount'].agg(['sum', 'count']).sort_index()
        for month, row in monthly.iterrows():
            avg_per_day = row['sum'] / 30  # Rough estimate
            print(f"   {month}: Rs. {row['sum']:>10,.2f} | {int(row['count']):>3} transactions | ≈₹{avg_per_day:>8,.2f}/day")
    
    return card_totals, category_totals

def create_visualizations(df, save_path='expense_analysis.png', figsize=(18, 18), dpi=300):
    """Create comprehensive expense visualizations"""
    
    fig = plt.figure(figsize=figsize, dpi=dpi)
    gs = fig.add_gridspec(3, 3, hspace=0.5, wspace=0.4)  # increased spacing
    
    colors = sns.color_palette("husl", 12)
    
    # 1. Spending by Category (Top-left, spans 2 columns)
    ax1 = fig.add_subplot(gs[0, :2])
    category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=True)
    ax1.barh(category_totals.index, category_totals.values, color=colors[:len(category_totals)])
    ax1.set_xlabel('Amount (Rs.)', fontsize=12, fontweight='bold', labelpad=10)
    ax1.set_title('Spending by Category', fontsize=14, fontweight='bold', pad=25)
    # ax1.grid(axis='x', alpha=0.3)
    for i, v in enumerate(category_totals.values):
        ax1.text(v, i, f' {v:,.0f}', va='center', fontsize=10)
    
    # 2. Card Distribution (Pie Chart, Top-right)
    ax2 = fig.add_subplot(gs[0, 2])
    card_totals = df.groupby('card')['amount'].sum()
    wedges, texts, autotexts = ax2.pie(card_totals.values, labels=card_totals.index, 
                                       autopct='%1.1f%%', startangle=90, colors=colors)
    ax2.set_title('Spending by Card', fontsize=14, fontweight='bold', pad=25)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    # 3. Monthly Trend (Middle row, full width)
    ax3 = fig.add_subplot(gs[1, :])
    if 'year_month' in df.columns:
        monthly = df.groupby('year_month')['amount'].sum().sort_index()
        ax3.plot(range(len(monthly)), monthly.values, marker='o', linewidth=2.5, 
                 markersize=8, color='#2E86AB', markerfacecolor='#A23B72')
        ax3.fill_between(range(len(monthly)), monthly.values, alpha=0.2, color='#2E86AB')
        ax3.set_xticks(range(len(monthly)))
        ax3.set_xticklabels(monthly.index, rotation=0, fontsize=11)
        ax3.set_ylabel('Amount (Rs.)', fontsize=12, fontweight='bold', labelpad=10)
        ax3.set_title('Monthly Spending Trend', fontsize=14, fontweight='bold', pad=25)
        ax3.grid(True, alpha=0.3)
        for i, v in enumerate(monthly.values):
            ax3.text(i, v, f'{v:,.0f}', ha='center', va='bottom', fontsize=10)
    
    # 4. Top 10 Merchants (Bottom-left, now X-axis = merchants)
    ax4 = fig.add_subplot(gs[2, :2])
    top_merchants = df.groupby('merchant')['amount'].sum().sort_values(ascending=False).head(10)
    merchant_names = [m[:30] + '...' if len(m) > 30 else m for m in top_merchants.index]

    x = range(len(top_merchants))  # numeric positions for bars
    bars = ax4.bar(x, top_merchants.values, color=colors[:len(top_merchants)])

    # Axis labels
    ax4.set_ylabel('Amount (Rs.)', fontsize=12, fontweight='bold', labelpad=15)
    ax4.set_xlabel('Merchants', fontsize=12, fontweight='bold', labelpad=10)
    ax4.set_title('Top 10 Merchants', fontsize=14, fontweight='bold', pad=25)

    # X-axis ticks
    ax4.set_xticks(x)
    ax4.set_xticklabels(merchant_names, rotation=45, ha='right', fontsize=10)

    # Grid
    ax4.grid(axis='y', alpha=0.3)

    # Value labels above bars
    for i, v in enumerate(top_merchants.values):
        ax4.text(i, v + max(top_merchants.values)*0.01, f'Rs. {v:,.0f}', ha='center', fontsize=10)


    
    # 5. Transaction Count by Category (Bottom-right)
    ax5 = fig.add_subplot(gs[2, 2])
    category_counts = df.groupby('category').size().sort_values(ascending=False).head(8)
    ax5.bar(category_counts.index, category_counts.values, color=colors[:len(category_counts)])
    ax5.set_ylabel('Number of Transactions', fontsize=12, fontweight='bold', labelpad=10)
    ax5.set_title('Transaction Count by Category', fontsize=13, fontweight='bold', pad=20)
    ax5.tick_params(axis='x', rotation=45, labelsize=10)
    ax5.grid(axis='y', alpha=0.3)

    plt.suptitle('Credit Card Expense Analysis Dashboard', fontsize=18, fontweight='bold', y=0.95)

    # plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n📊 Visualizations saved to: {save_path}")
    
    return fig


def find_insights(df):
    """Generate interesting insights from the data"""
    
    print("\n" + "="*70)
    print("💡 KEY INSIGHTS")
    print("="*70)
    
    # Highest single transaction
    max_txn = df.loc[df['amount'].idxmax()]
    print(f"\n🔥 Highest Single Transaction:")

    txn_date = max_txn['date'].strftime("%d %b %y")
    print(f"   Rs. {max_txn['amount']:,.2f} at {max_txn['merchant']} on {txn_date}")
    
    # Most frequent merchant
    merchant_freq = df['merchant'].value_counts()
    if len(merchant_freq) > 0:
        top_merchant = merchant_freq.index[0]
        count = merchant_freq.iloc[0]
        total = df[df['merchant'] == top_merchant]['amount'].sum()
        print(f"\n🔄 Most Frequent Merchant:")
        print(f"   {top_merchant}: {count} transactions, Rs. {total:,.2f} total")
    
    # Average spending by day of week
    df['day_of_week'] = df['date'].dt.day_name()
    day_avg = df.groupby('day_of_week')['amount'].mean().sort_values(ascending=False)
    print(f"\n📆 Average Spending by Day:")
    for day, avg in day_avg.head(3).items():
        print(f"   {day}: Rs. {avg:,.2f}")
    
    # Category insights
    print(f"\n🎯 Category Insights:")
    for category in df['category'].unique()[:5]:
        cat_data = df[df['category'] == category]
        if len(cat_data) > 0:
            avg = cat_data['amount'].mean()
            total = cat_data['amount'].sum()
            count = len(cat_data)
            print(f"   {category}: {count} txns, Avg Rs. {avg:,.2f}, Total Rs. {total:,.2f}")
    
    # Uncategorized transactions
    uncategorized = df[df['category'] == 'Other']
    if len(uncategorized) > 0:
        unc_total = uncategorized['amount'].sum()
        unc_pct = (unc_total / df['amount'].sum()) * 100
        print(f"\n⚠️  Uncategorized Spending:")
        print(f"   Rs. {unc_total:,.2f} ({unc_pct:.1f}% of total)")
        print(f"\n   Top uncategorized merchants:")
        unc_merchants = uncategorized.groupby('merchant')['amount'].sum().sort_values(ascending=False).head(5)
        for merchant, amount in unc_merchants.items():
            print(f"   • {merchant[:50]}: Rs. {amount:,.2f}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def analyze_expenses(df):
    """
    Analyze expenses from a DataFrame
    Returns a formatted summary string
    """

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', 'amount'])

    lines = []

    # ------------------------------
    # Overall stats
    # ------------------------------
    total_txns = len(df)
    total_spent = df['amount'].sum()
    avg_txn = df['amount'].mean()
    median_txn = df['amount'].median()
    date_range = f"{df['date'].min().date()} to {df['date'].max().date()}"

    lines.append("📊 EXPENSE ANALYSIS SUMMARY")
    lines.append("=" * 50)
    lines.append(f"Total Transactions: {total_txns}")
    lines.append(f"Total Spent: Rs. {total_spent:,.2f}")
    lines.append(f"Average Transaction: Rs. {avg_txn:,.2f}")
    lines.append(f"Median Transaction: Rs. {median_txn:,.2f}")
    lines.append(f"Date Range: {date_range}\n")

    # ------------------------------
    # Spending by CARD
    # ------------------------------
    lines.append("💳 Spending by Card:")
    for card, amt in df.groupby('card')['amount'].sum().items():
        count = len(df[df['card'] == card])
        lines.append(f"  {card}: Rs. {amt:,.2f} | {count} txns")

    lines.append("")

    # ------------------------------
    # Spending by category
    # ------------------------------
    lines.append("🏷️ Spending by Category:")
    cat_summary = df.groupby('category')['amount'].agg(['sum', 'count', 'mean'])
    for cat, row in cat_summary.sort_values('sum', ascending=False).iterrows():
        lines.append(
            f"  {cat:15} : Rs. {row['sum']:>8,.2f} | {int(row['count'])} txns | Avg Rs. {row['mean']:,.2f}"
        )

    return "\n".join(lines)

# def analyze_csv(csv_file):
#     df = pd.read_csv(csv_file)
#     df['date'] = pd.to_datetime(df['date'], errors='coerce')
#     df = df.dropna(subset=['date', 'amount'])
#     return analyze_expenses(df)

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("\n\n")
    print("="*70)
    print("💳 CREDIT CARD EXPENSE ANALYZER (CSV MODE)")
    print("="*70)

    csv_file = "all_transactions_combined.csv"
    df = pd.read_csv(csv_file)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # 1️⃣ PRINT TEXT SUMMARY
    summary = analyze_expenses(df)
    print(summary)

    # 2️⃣ DETAILED CONSOLE STATS
    generate_summary_stats(df)

    # 3️⃣ INSIGHTS
    find_insights(df)

    # 4️⃣ VISUALS
    create_visualizations(df)

    plt.show()   # <-- IMPORTANT


