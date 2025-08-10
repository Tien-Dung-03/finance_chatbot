import vnstock as vs
from pathlib import Path
import pandas as pd

def get_symbol(symbol_file) -> list:
    """
    Get stock symbols from the vnstock listing.
    
    Args:
        symbol_file (str): Path to the CSV file containing stock symbols.
        
    Returns:
        list: Filtered list of stock symbols.
    """
    symbol_df = pd.read_csv(symbol_file)
    symbols = symbol_df['symbol'].unique().tolist()
    return symbols
    
def export_symbol_screeners(listing, screener, symbol_file, screener_file):
    """
    Export stock symbol and screener data to CSV files, ensuring consistent ticker/symbol order.
    
    Args:
        listing: vnstock Listing object.
        screener: vnstock Screener object.
        symbol_file (str): Path to the output symbol CSV file.
        screener_file (str): Path to the output screener CSV file.
    """
    print("Exporting screener data to CSV...")
    # Get symbols data and filter for STOCK type
    df = listing.symbols_by_exchange()
    newdf = df[df['type'] == 'STOCK']
    
    # Get screener data
    screener_df = screener.stock(params={"exchangeName": "HOSE,HNX,UPCOM"}, limit=1700)

    # Get unique symbols and tickers
    symbols = newdf['symbol'].unique().tolist()
    screener_tickers = screener_df['ticker'].unique().tolist()

    # Find common tickers (intersection of symbols and screener_tickers)
    filtered_tickers = [ticker for ticker in symbols if ticker in screener_tickers]

    # Filter DataFrames
    filtered_symbols_df = newdf[newdf['symbol'].isin(filtered_tickers)]
    filtered_screener_df = screener_df[screener_df['ticker'].isin(filtered_tickers)]

    # Sort DataFrames to ensure consistent order based on filtered_tickers
    filtered_symbols_df = filtered_symbols_df.set_index('symbol').loc[filtered_tickers].reset_index()
    filtered_screener_df = filtered_screener_df.set_index('ticker').loc[filtered_tickers].reset_index()

    # Export to CSV
    filtered_symbols_df.to_csv(symbol_file, columns=['symbol', 'organ_short_name', 'organ_name'], index=False)
    filtered_screener_df.to_csv(screener_file, index=False)
    print(f"Exported {len(filtered_tickers)} symbols to {symbol_file} and screener data to {screener_file}")
    
# Main execution
if __name__ == "__main__":
    # Initialize vnstock Listing
    listing = vs.Listing()
    screener = vs.Screener()
    
    symbol_path = 'csv_file/vnstock_symbols.csv'
    screener_path = 'csv_file/vnstock_screeners.csv'
    
    current_dir = Path(__file__).parent.resolve()
    symbol_file = current_dir.parent.resolve() / symbol_path 
    screener_file = current_dir.parent.resolve() / screener_path
    
    # Export symbols
    export_symbol_screeners(listing, screener, symbol_file, screener_file)

    print("Completed!!!")