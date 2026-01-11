"""
Multi-Bank Credit Card Statement Parser
Supports: Axis Bank Flipkart, HDFC Tata Neu

Usage:
    python parser.py <pdf_file>
    
Or import and use:
    from parser import parse_statement
    df = parse_statement('statement.pdf')
"""

import PyPDF2
import pandas as pd
import re
from datetime import datetime
from pathlib import Path

# ============================================================================
# AXIS BANK FLIPKART PARSER
# ============================================================================

def parse_axis(text, card):
    """
    Parse Axis Bank Flipkart credit card statement
    
    Format:
    Date | Transaction Details | Amount (INR) | Debit/Credit
    09 Dec '25 | FLIPKART PAYMENTS,BANGALORE | ₹ 534.00 | Debit
    """
    
    transactions = []
    lines = text.split('\n')
    
    # Pattern to match transaction lines
    # Date format: DD MMM 'YY (e.g., "09 Dec '25")
    pattern = r"(\d{1,2}\s+\w{3}\s+'\d{2})\s+(.+?)\s+₹\s*([\d,]+\.?\d*)\s+(Debit|Credit)"
    
    for line in lines:
        match = re.search(pattern, line)
        if match:
            date_str, merchant, amount_str, trans_type = match.groups()
            
            # Only include debits (actual spending)
            if trans_type == "Debit":
                # Parse date
                date = datetime.strptime(date_str, "%d %b '%y")
                
                # Clean amount
                amount = float(amount_str.replace(',', ''))
                
                # Clean merchant name
                merchant = merchant.strip()
                
                transactions.append({
                    'date': date,
                    'merchant': merchant,
                    'amount': amount,
                    'category': None,  # Will categorize later
                    'bank': 'Axis',
                    'card': card,
                })
    
    return pd.DataFrame(transactions)

# ============================================================================
# HDFC TATA NEU PARSER
# ============================================================================

def parse_hdfc(text, card):
    """
    Parse HDFC Tata Neu credit card statement
    
    Format:
    DATE & TIME | TRANSACTION DESCRIPTION | Base NeuCoins* | AMOUNT | PI
    20/11/2025| 20:40 | WESTSIDEMUMBAI | + 22 | C 2,244.00 | l
    
    Rules:
    - Lines starting with '+' in amount are credits (skip these)
    - Lines with 'PAYMENT' in description are payments (skip these)
    - PI column has category indicator (l = specific category)
    """
    
    transactions = []
    lines = text.split('\n')
    
    # Pattern to match transaction lines
    pattern = r"(\d{2}/\d{2}/\d{4})\|\s*(\d{2}:\d{2})\s+(.+?)(?:\s+\+\s*\d+)?\s*([+-]?\s*C)\s*([\d,]+(?:\.\d{2})?)"


    for line in lines:
        # Skip payment lines
        if 'PAYMENT' in line.upper() or 'BPPY' in line:
            continue
        
        # Try detailed pattern first
        match = re.search(pattern, line)
        if match:
            date_str, time_str, merchant, txn_type, amount_str = match.groups()
            
            # Check if it's a credit (has + before C)
            is_credit = txn_type.strip().startswith('+')
            
            # Skip credits (we only want spending/debits)
            if is_credit:
                continue
            
            # Parse date
            try:
                date = datetime.strptime(date_str, "%d/%m/%Y")
            except:
                continue
            
            # Clean amount
            amount = float(amount_str.replace(',', ''))
            
            # Clean merchant/description
            merchant = merchant.strip()
            
            # Try to extract category from merchant name
            category = extract_hdfc_category(merchant)
            
            transactions.append({
                'date': date,
                'merchant': merchant,
                'amount': amount,
                'category': category,
                'bank': 'HDFC',
                'card': card,
            })
    
    return pd.DataFrame(transactions)


def extract_hdfc_category(merchant):
    """
    Extract category from HDFC merchant name
    HDFC already categorizes some transactions
    """
    merchant_lower = merchant.lower()
    
    # Common HDFC merchant patterns
    if any(x in merchant_lower for x in ['westside', 'zara', 'h&m', 'max fashion']):
        return 'Apparels'
    elif any(x in merchant_lower for x in ['zomato', 'swiggy', 'bistro', 'restaurant']):
        return 'Restaurant'
    elif any(x in merchant_lower for x in ['blink', 'bigbasket', 'dmart', 'grofers']):
        return 'Groceries'
    elif any(x in merchant_lower for x in ['uber', 'ola', 'rapido']):
        return 'Transport'
    
    return None

# ============================================================================
# GENERIC CATEGORIZATION (for transactions without bank categories)
# ============================================================================

CATEGORY_KEYWORDS = {
    'Groceries': ['bigbasket', 'blinkit', 'zepto', 'dmart', 'reliance fresh', 'more', 'grocery', 'blink commerce', 'instamart'],
    'Dining': ['swiggy', 'zomato', 'restaurant', 'cafe', 'dominos', 'pizza', 'kfc', 'mcdonald', 'bistro'],
    'Shopping': ['amazon', 'flipkart', 'myntra', 'ajio', 'nykaa', 'meesho', 'westside', 'max', 'pantaloons', 'fashnear', 'savana'],
    'Transport': ['uber', 'ola', 'rapido', 'metro', 'petrol', 'fuel', 'hp', 'indian oil'],
    'Bills & Utilities': ['electricity', 'airtel', 'jio', 'vodafone', 'broadband', 'gas', 'water'],
    'Entertainment': ['netflix', 'prime', 'spotify', 'bookmyshow', 'pvr', 'hotstar', 'cinema', 'district'],
    'Travel': ['irctc', 'makemytrip', 'goibibo', 'cleartrip', 'hotel', 'flight', 'booking'],
    'Health': ['pharmacy', 'apollo', 'medplus', 'hospital', 'clinic', 'doctor']
}

def categorize_transaction(merchant, existing_category=None):
    """Categorize transaction based on merchant name"""
    
    # If bank already provided a category, use it
    if existing_category:
        return existing_category
    
    if pd.isna(merchant):
        return 'Other'
    
    merchant_lower = str(merchant).lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in merchant_lower for keyword in keywords):
            return category
    
    return 'Other'

# ============================================================================
# MAIN PARSER - Auto-detect bank and parse
# ============================================================================

def detect_bank(text):
    """Detect which bank statement this is"""
    
    if 'axis bank' in text.lower():
        return 'AXIS'
    elif 'hdfc bank' in text.lower():
        return 'HDFC'
    else:
        return None
    
def detect_card(text):
    """
    Detect credit card name from the PDF text
    Returns: card_name (str)
    """
    text_upper = text.upper()

    # Search for HDFC header robustly
    match = re.search(r"(.+?)\s+HDFC\s+BANK\s+CREDIT\s+CARD\s+STATEMENT", text_upper, re.DOTALL)
    if match:
        prefix = match.group(1).replace('\n', ' ').strip()  # replace any newlines
        if "SWIGGY" in prefix:
            return "HDFC Swiggy"
        elif "NEU" in prefix:  # matches 'Tata Neu', 'Neu Plus', etc
            return "HDFC Tata Neu"
        else:
            return "HDFC Credit Card"

    # Axis Flipkart variant
    match = re.search(r"AXIS\s+(.+?)\s+CREDIT CARD", text_upper)
    if match:
        prefix = match.group(1).strip()
        if "FLIPKART" in prefix:
            return "Axis Flipkart"
        else:
            return "Axis Bank Credit Card"

    # fallback
    return "Unknown Card"


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def parse_statement(pdf_path):
    """
    Main function to parse any supported credit card statement
    
    Returns:
        DataFrame with columns: date, merchant, amount, category, bank
    """
    
    # Extract text from PDF
    print(f"Reading PDF: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("Failed to extract text from PDF")
        return None
    
    # Detect bank
    bank = detect_bank(text)
    print(f"Detected bank: {bank}")
    card = detect_card(text)
    print(f"Detected card: {card}")
    
    # Parse based on bank
    if bank == 'AXIS':
        df = parse_axis(text, card)
    elif bank == 'HDFC':
        df = parse_hdfc(text, card)
    else:
        print("Unknown bank format. Supported: Axis & HDFC Credit Cards")
        return None
    
    if df is None or df.empty:
        print("No transactions found")
        return None
    
    # Apply categorization
    df['category'] = df.apply(
        lambda row: categorize_transaction(row['merchant'], row['category']), 
        axis=1
    )
    
    # Add formatted date for display
    # df['month'] = df['date'].dt.strftime('%b')
    df['year_month'] = df['date'].dt.strftime('%b-%y')
    
    print(f"✓ Parsed {len(df)} transactions from {bank.upper()}")
    
    return df

# ============================================================================
# BATCH PROCESSING - Parse multiple PDFs
# ============================================================================

def parse_multiple_statements(pdf_files):
    """
    Parse multiple PDF statements and combine them
    
    Parameters:
        pdf_files: list of PDF file paths or dict like {'Card Name': 'path/to/pdf'}
    
    Returns:
        Combined DataFrame with all transactions
    """
    
    all_transactions = []
    
    # Handle both list and dict inputs
    if isinstance(pdf_files, dict):
        files_to_process = pdf_files.items()
    else:
        files_to_process = [(Path(f).stem, f) for f in pdf_files]
    
    for name, pdf_path in files_to_process:
        print(f"\n{'='*60}")
        print(f"Processing: {name}")
        print('='*60)
        
        df = parse_statement(pdf_path)
        
        if df is not None and not df.empty:
            all_transactions.append(df)
        else:
            print(f"⚠ Warning: Could not parse {name}")
    
    if not all_transactions:
        print("\n❌ No transactions extracted from any file")
        return None
    
    # Combine all dataframes
    combined_df = pd.concat(all_transactions, ignore_index=True)
    combined_df = combined_df.sort_values('date').reset_index(drop=True)
    
    print(f"\n{'='*60}")
    print(f"✅ Total transactions extracted: {len(combined_df)}")
    print(f"   Date range: {combined_df['date'].min().date()} to {combined_df['date'].max().date()}")
    print(f"   Total amount: ₹{combined_df['amount'].sum():,.2f}")
    print('='*60)
    
    return combined_df

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("="*70)
    print("MULTI-BANK CREDIT CARD STATEMENT PARSER")
    print("="*70)
    print("\nSupported Banks:")
    print("  • HDFC Bank")
    print("  • Axis Bank")
    print("\n" + "="*70 + "\n")
    
    # Check if PDF files were provided as arguments
    if len(sys.argv) > 1:
        
        pdf_files = sys.argv[1:]  # Get ALL arguments after script name

        print(f"Processing {len(pdf_files)} PDF files...")
        df = parse_multiple_statements(pdf_files)
        
        if df is not None:
            print("\n📊 Combined Summary:")
            print(f"   Total Transactions: {len(df)}")
            print(f"   Total Amount: ₹{df['amount'].sum():,.2f}")
            print(f"\n   By Bank:")
            for bank, total in df.groupby('bank')['amount'].sum().items():
                count = len(df[df['bank'] == bank])
                print(f"      {bank}: ₹{total:,.2f} ({count} transactions)")
            
            print("\nFirst 10 transactions:")
            print(df[['date', 'merchant', 'amount', 'category', 'bank']].head(10))
            
            # Save combined data
            output_file = 'all_transactions_combined.csv'
            df.to_csv(output_file, index=False)
            print(f"\n💾 Saved to: {output_file}")
    
    else:
        print("Usage:")
        print("  Single file:    python parser.py statement.pdf")
        print("  Multiple files: python parser.py file1.pdf file2.pdf file3.pdf")
        print("\nExample:")
        print("  python parser.py Flip_Dec.pdf Neu_Dec.pdf Swig_Dec.pdf")