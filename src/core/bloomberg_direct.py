import pandas as pd
from typing import Dict, Tuple, Optional
from xbbg import blp

class BloombergDirect:
    def __init__(self):
        pass

    def fetch_bloomberg_data(
        self,
        mapping: Dict[Tuple[str, str], str],
        start_date: str = '2000-01-01',
        end_date: Optional[str] = None,
        periodicity: str = 'D',
        align_start: bool = False
    ) -> pd.DataFrame:
        """
        Fetch Bloomberg data using a mapping of (ticker, field) pairs to column names.
        
        Args:
            mapping: Dictionary with (ticker, field) tuples as keys and desired column names as values
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format (defaults to today if None)
            periodicity: Data frequency ('D' for daily, 'M' for monthly, etc.)
            align_start: If True, trim data to start from the latest first valid date across all series
            
        Returns:
            DataFrame with processed Bloomberg data
        """
        if end_date is None:
            end_date = pd.Timestamp('today').strftime('%Y-%m-%d')
        
        tickers = list({k[0] for k in mapping.keys()})
        fields = list({k[1] for k in mapping.keys()})
        
        df_raw = blp.bdh(
            tickers=tickers,
            flds=fields,
            start_date=start_date,
            end_date=end_date,
            Per=periodicity
        )
        
        df_raw.columns = df_raw.columns.to_flat_index()
        df_raw.rename(columns=lambda col: mapping.get(col, f"{col[0]}|{col[1]}"), inplace=True)
        
        desired_order = [mapping[pair] for pair in mapping]
        final_df = df_raw[[c for c in desired_order if c in df_raw.columns]]
        
        if align_start:
            first_valid_per_col = []
            for col in final_df.columns:
                first_valid = final_df[col].first_valid_index()
                if first_valid is not None:
                    first_valid_per_col.append(first_valid)
            if first_valid_per_col:
                start_cutoff = max(first_valid_per_col)
                final_df = final_df.loc[final_df.index >= start_cutoff]
        
        # Make a copy here before forward-fill
        final_df = final_df.copy()
        
        # Forward-fill
        final_df = final_df.ffill()
        
        # Drop duplicates, sort index, etc.
        final_df = final_df.loc[~final_df.index.duplicated(keep='first')].copy()
        final_df.sort_index(inplace=True)
        final_df.index.name = 'Date'
        
        return final_df

    def __del__(self):
        """Cleanup connection when object is destroyed"""
        try:
            pass  # No connection to stop for xbbg
        except:
            pass
