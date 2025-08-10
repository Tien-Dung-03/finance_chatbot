import vnstock as vs
from pathlib import Path
import pandas as pd
import time
from download_symbol_screener import get_symbol

def download_vnstock_financial_reports(symbols, period, output_dir, lang: str = 'en', batch_size: int = 10):
    start_time = time.time()

    # Khởi tạo các DataFrame để lưu trữ dữ liệu cho từng loại báo cáo
    all_income_statements = pd.DataFrame()
    all_balance_sheets = pd.DataFrame()
    all_cash_flows = pd.DataFrame()
    all_ratios = pd.DataFrame()

    while symbols:
        # Xử lý một batch tối đa batch_size mã chứng khoán
        batch = symbols[:batch_size]
        symbols = symbols[batch_size:]  # Xóa các mã đã xử lý khỏi danh sách

        for symbol in batch:
            try:
                # Lấy dữ liệu chứng khoán
                finance = vs.Finance(symbol=symbol, source='VCI')
                
                # Lấy các báo cáo tài chính
                income_statement = finance.income_statement(period=period, lang=lang)
                balance_sheet = finance.balance_sheet(period=period, lang=lang)
                cash_flow = finance.cash_flow(period=period, lang=lang)
                ratios = finance.ratio(period=period, lang=lang)

                # Thêm cột ticker vào mỗi báo cáo
                income_statement['ticker'] = symbol
                balance_sheet['ticker'] = symbol
                cash_flow['ticker'] = symbol
                ratios['ticker'] = symbol
                
                # Lọc dữ liệu cho năm 2024 và 2025
                # income_statement = income_statement[income_statement['yearReport'].isin([2024, 2025])]
                # balance_sheet = balance_sheet[balance_sheet['yearReport'].isin([2024, 2025])]
                # cash_flow = cash_flow[cash_flow['yearReport'].isin([2024, 2025])]
                # ratios = ratios[ratios['yearReport'].isin([2024, 2025])]
                
                # Gộp dữ liệu vào các DataFrame chung
                all_income_statements = pd.concat([all_income_statements, income_statement], ignore_index=True)
                all_balance_sheets = pd.concat([all_balance_sheets, balance_sheet], ignore_index=True)
                all_cash_flows = pd.concat([all_cash_flows, cash_flow], ignore_index=True)
                all_ratios = pd.concat([all_ratios, ratios], ignore_index=True)
                              
                income_statements_path = Path(output_dir) / 'income_statements.csv'
                balance_sheets_path = Path(output_dir) / 'balance_sheets.csv'
                cash_flows_path = Path(output_dir) / 'cash_flows.csv'
                ratios_path = Path(output_dir) / 'ratios.csv'
                
                # Lưu tất cả dữ liệu vào các file CSV riêng biệt
                all_income_statements.to_csv(income_statements_path, mode='a',
                                            header=not pd.io.common.file_exists(income_statements_path), index=False)
                all_balance_sheets.to_csv(balance_sheets_path, mode='a',
                                            header=not pd.io.common.file_exists(balance_sheets_path), index=False)
                all_cash_flows.to_csv(cash_flows_path, mode='a',
                                            header=not pd.io.common.file_exists(cash_flows_path), index=False)
                all_ratios.to_csv(ratios_path, mode='a',
                                            header=not pd.io.common.file_exists(ratios_path), index=False)

                print(f"Data for {symbol} processed.")

            except Exception as e:
                print(f"Failed to fetch data for {symbol}: {e}")

        # Chờ sau khi xử lý một batch nếu còn mã chứng khoán
        if symbols:
            wait_time = max(60 - (time.time() - start_time), 60)
            if wait_time > 0:
                print(f"Waiting {wait_time:.2f} seconds before processing next batch.")
                time.sleep(wait_time)
            start_time = time.time()

    print("All financial reports have been saved successfully.")

# Main execution
if __name__ == "__main__":
    # Khởi tạo tham số
    period = 'month'
    lang = 'en'
    
    # Định nghĩa đường dẫn đầu ra
    output_dir = 'csv_file'
    symbol_path = 'csv_file/vnstock_symbols.csv'
    
    current_dir = Path(__file__).parent.resolve()
    symbol_file = current_dir.parent.resolve() / symbol_path 
    output_dir = current_dir.parent.resolve() / output_dir

    # Lấy mã chứng khoán từ file CSV
    symbols = get_symbol(symbol_file) 
    download_vnstock_financial_reports(symbols[:2], period, output_dir, lang, batch_size=10)

    print("Completed !!!")
