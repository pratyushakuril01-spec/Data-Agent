"""
core/parser.py
Robust Statement Ingestion Engine for CSV and PDF financial statement exports.
Auto-detects schemas, column naming variations, and polarity (debits vs credits).
"""

import io
import re
from typing import Optional, Union, BinaryIO
import pandas as pd
from dateutil import parser as date_parser

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


DATE_COL_CANDIDATES = [
    'date', 'transaction date', 'trans date', 'posting date', 'post date',
    'txn date', 'booking date', 'date of transaction'
]

DESC_COL_CANDIDATES = [
    'description', 'raw_description', 'merchant', 'details', 'memo',
    'payee', 'narrative', 'transaction description', 'appears on your statement as',
    'name', 'merchant name'
]

AMOUNT_COL_CANDIDATES = [
    'amount', 'amt', 'transaction amount', 'net amount'
]

DEBIT_COL_CANDIDATES = [
    'debit', 'debits', 'charge', 'withdrawal', 'expense'
]

CREDIT_COL_CANDIDATES = [
    'credit', 'credits', 'deposit', 'payment'
]

CATEGORY_COL_CANDIDATES = [
    'category', 'type', 'spend category', 'classification'
]


class StatementParser:
    """
    Parses bank and credit card statement files (CSV, PDF, or DataFrame)
    into a standardized schema:
      - date: pd.Timestamp
      - raw_description: str
      - amount: float (positive = spend/debit, negative = refund/credit)
      - category: str (optional/detected)
      - original_id: int
    """

    @classmethod
    def parse(cls, file_source: Union[str, BinaryIO, pd.DataFrame], filename: Optional[str] = None) -> pd.DataFrame:
        """
        Main entrypoint. Accepts filepath, file-like buffer, or existing DataFrame.
        """
        if isinstance(file_source, pd.DataFrame):
            return cls._normalize_dataframe(file_source)

        fname = (filename or getattr(file_source, 'name', '') or str(file_source)).lower()

        if fname.endswith('.pdf'):
            return cls._parse_pdf(file_source)
        else:
            # Assume CSV / Delimited text
            return cls._parse_csv(file_source)

    @classmethod
    def _parse_csv(cls, source: Union[str, BinaryIO]) -> pd.DataFrame:
        """Parse CSV with delimiter and header sniffing."""
        # Try standard reading
        try:
            if hasattr(source, 'seek'):
                source.seek(0)
            df = pd.read_csv(source)
        except Exception:
            if hasattr(source, 'seek'):
                source.seek(0)
            df = pd.read_csv(source, sep=None, engine='python')

        # If columns look like metadata or first few rows are empty, skip until headers
        if not cls._has_valid_columns(df):
            if hasattr(source, 'seek'):
                source.seek(0)
            for skip in range(1, 10):
                try:
                    if hasattr(source, 'seek'):
                        source.seek(0)
                    temp_df = pd.read_csv(source, skiprows=skip)
                    if cls._has_valid_columns(temp_df):
                        df = temp_df
                        break
                except Exception:
                    continue

        return cls._normalize_dataframe(df)

    @classmethod
    def _parse_pdf(cls, source: Union[str, BinaryIO]) -> pd.DataFrame:
        """
        Extract tabular text lines from PDF statement exports.
        Uses regex heuristics for common bank layouts:
        e.g.: '01/15/2024  NETFLIX.COM  15.49' or 'Jan 15, 2024  AMZN DIG*2948  $14.99'
        """
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf is required to parse PDF statements. Run `pip install pypdf`.")

        reader = pypdf.PdfReader(source)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text() or ""
            full_text += "\n" + text

        records = []
        # Pattern 1: MM/DD/YYYY or YYYY-MM-DD or MM/DD followed by text and an amount
        line_pattern = re.compile(
            r'(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|\w{3}\s+\d{1,2},?\s*\d{0,4})\s+(.+?)\s+(-?\$?\s*\d{1,3}(?:,\d{3})*\.\d{2})'
        )

        for line in full_text.splitlines():
            line = line.strip()
            match = line_pattern.search(line)
            if match:
                date_str, desc, amt_str = match.groups()
                # Clean amount
                clean_amt_str = amt_str.replace('$', '').replace(',', '').strip()
                try:
                    parsed_date = date_parser.parse(date_str, fuzzy=True)
                    amt_val = float(clean_amt_str)
                    records.append({
                        'date': parsed_date,
                        'raw_description': desc.strip(),
                        'amount': amt_val,
                        'category': 'General'
                    })
                except Exception:
                    continue

        if not records:
            # Fallback to empty df with standard schema
            return pd.DataFrame(columns=['date', 'raw_description', 'amount', 'category', 'original_id'])

        df = pd.DataFrame(records)
        df['original_id'] = range(len(df))
        return cls._normalize_dataframe(df)

    @classmethod
    def _has_valid_columns(cls, df: pd.DataFrame) -> bool:
        cols_lower = [str(c).strip().lower() for c in df.columns]
        has_date = any(any(cand in col for cand in DATE_COL_CANDIDATES) for col in cols_lower)
        has_desc = any(any(cand in col for cand in DESC_COL_CANDIDATES) for col in cols_lower)
        has_amt = any(any(cand in col for cand in (AMOUNT_COL_CANDIDATES + DEBIT_COL_CANDIDATES)) for col in cols_lower)
        return has_date and (has_desc or has_amt)

    @classmethod
    def _find_column(cls, df_cols, candidates):
        """Match column name against list of candidate synonyms."""
        # 1. Exact match
        for col in df_cols:
            c_clean = str(col).strip().lower()
            if c_clean in candidates:
                return col
        # 2. Substring match
        for col in df_cols:
            c_clean = str(col).strip().lower()
            for cand in candidates:
                if cand in c_clean:
                    return col
        return None

    @classmethod
    def _normalize_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Map heterogeneous bank columns to standardized schema and sanitize values."""
        df = df.copy()

        # Drop entirely blank rows and columns
        df = df.dropna(how='all')
        if df.empty:
            return pd.DataFrame(columns=['date', 'raw_description', 'amount', 'category', 'original_id'])

        cols = list(df.columns)
        date_col = cls._find_column(cols, DATE_COL_CANDIDATES)
        desc_col = cls._find_column(cols, DESC_COL_CANDIDATES)
        amount_col = cls._find_column(cols, AMOUNT_COL_CANDIDATES)
        debit_col = cls._find_column(cols, DEBIT_COL_CANDIDATES)
        credit_col = cls._find_column(cols, CREDIT_COL_CANDIDATES)
        cat_col = cls._find_column(cols, CATEGORY_COL_CANDIDATES)

        if not date_col:
            raise ValueError(f"Could not identify a Date column. Found headers: {cols}")
        if not desc_col:
            # If no explicit description, pick the first string/object column
            obj_cols = [c for c in cols if df[c].dtype == 'object' and c != date_col]
            if obj_cols:
                desc_col = obj_cols[0]
            else:
                desc_col = 'Description'
                df[desc_col] = 'Unknown Merchant'

        # Standardize Date
        def safe_date_parse(val):
            if pd.isna(val):
                return pd.NaT
            try:
                return pd.to_datetime(val)
            except Exception:
                try:
                    return date_parser.parse(str(val), fuzzy=True)
                except Exception:
                    return pd.NaT

        df['date_std'] = df[date_col].apply(safe_date_parse)
        df = df.dropna(subset=['date_std'])

        # Standardize Amount
        def clean_numeric(val):
            if pd.isna(val):
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            s = str(val).replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip()
            # Handle parentheses notation for negative: (12.34) -> -12.34
            if s.startswith('(') and s.endswith(')'):
                s = '-' + s[1:-1]
            try:
                return float(s)
            except ValueError:
                return 0.0

        if debit_col and debit_col in df.columns:
            # Split debit / credit layout
            debits = df[debit_col].apply(clean_numeric).abs()
            if credit_col and credit_col in df.columns:
                credits = df[credit_col].apply(clean_numeric).abs()
                df['amount_std'] = debits - credits
            else:
                df['amount_std'] = debits
        elif amount_col and amount_col in df.columns:
            raw_amounts = df[amount_col].apply(clean_numeric)
            
            # Polarity detection heuristic:
            # In credit card statements: positive amounts are usually charges (expenses), negative are payments/credits.
            # In bank checking accounts: negative amounts are debits/expenses, positive are payroll deposits.
            # We want: Expenses = POSITIVE amounts, Payments/Deposits = NEGATIVE amounts.
            # If more than 70% of non-zero rows are negative, it's a checking account statement where debits are negative.
            non_zeros = raw_amounts[raw_amounts != 0]
            if len(non_zeros) > 0 and (non_zeros < 0).mean() > 0.6:
                df['amount_std'] = -raw_amounts
            else:
                df['amount_std'] = raw_amounts
        else:
            df['amount_std'] = 0.0

        # Descriptions
        df['raw_description_std'] = df[desc_col].astype(str).str.strip()

        # Category (if present)
        if cat_col and cat_col in df.columns:
            df['category_std'] = df[cat_col].astype(str).str.strip()
        else:
            df['category_std'] = 'General'

        # Filter out rows with 0 or non-charge transactions (like payments/transfers to card)
        # We also keep track of original row index
        result = pd.DataFrame({
            'date': df['date_std'],
            'raw_description': df['raw_description_std'],
            'amount': df['amount_std'],
            'category': df['category_std'],
            'original_id': df.index
        })

        # Sort chronologically
        result = result.sort_values('date').reset_index(drop=True)
        return result
