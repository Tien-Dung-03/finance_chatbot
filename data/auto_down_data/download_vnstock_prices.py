import vnstock as vs
from datetime import datetime
import pandas as pd
import time
from pathlib import Path
from download_symbol_screener import get_symbol

def download_vnstock_prices(symbols, start_date, end_date, csv_file, batch_size: int = 10):
    """
    Fetch stock data for given symbols and save to CSV, respecting rate limits.
    
    Args:
        symbols (list): List of stock symbols to fetch data for.
        start_date (str): Start date for historical data (YYYY-MM-DD).
        end_date (str): End date for historical data (YYYY-MM-DD).
        csv_file (str): Path to the output CSV file.
        batch_size (int): Number of symbols to process per minute.
        request_limit (int): API request limit per minute.
    """
    start_time = time.time()

    while symbols:
        # Process a batch of up to batch_size symbols
        batch = symbols[:batch_size]
        symbols = symbols[batch_size:]  # Remove processed symbols from the list

        for symbol in batch:
            try:
                # Fetch stock data
                stock = vs.Quote(symbol=symbol, source='VCI')
                df = stock.history(start=start_date, end=end_date, interval='1D')
                df['ticker'] = symbol

                # Append data to CSV
                df.to_csv(csv_file, mode='a', 
                          columns=['time', 'open', 'high', 'low', 'close', 'volume', 'ticker'],
                          header=not pd.io.common.file_exists(csv_file), index=False)
                
                print(f"Data for {symbol} saved to {csv_file}.")

            except Exception as e:
                print(f"Failed to fetch data for {symbol}: {e}")

        # Wait after processing a batch if more symbols remain
        if symbols:
            wait_time = max(70 - (time.time() - start_time), 0)
            if wait_time > 0:
                print(f"Waiting {wait_time:.2f} seconds before processing next batch.")
                time.sleep(wait_time)
            start_time = time.time()

# Main execution
if __name__ == "__main__":
    # Initialize vnstock Listing
    start_date = '2024-01-01'
    end_date = datetime.now().strftime("%Y-%m-%d")
    # number_stop = 10
        
    file_path = 'csv_file/vnstock_data_prices.csv'
    symbol_path = 'csv_file/vnstock_symbols.csv'
    
    current_dir = Path(__file__).parent.resolve()
    symbol_file = current_dir.parent.resolve() / symbol_path
    prices_file = current_dir.parent.resolve() / file_path 

    symbols = get_symbol(symbol_file) 
    download_vnstock_prices(symbols, start_date, end_date, prices_file, batch_size=30)
    # download_vnstock_prices(symbols, number_stop, start_date, end_date, prices_file, batch_size=30)

    print("Completed !!!")