import pandas as pd
import sqlite3
from pathlib import Path

# Đọc dữ liệu từ CSV
symbols_path = "csv_file/vnstock_symbols.csv"
prices_path = "csv_file/vnstock_data_prices.csv"
screener_path = "csv_file/vnstock_screeners.csv"
db_path = "vnstock_data.db"

current_dir = Path(__file__).parent.resolve()
symbols_file = current_dir.parent.resolve() / symbols_path 
prices_file = current_dir.parent.resolve() / prices_path
screener_file = current_dir.parent.resolve() / screener_path
db_file = current_dir.parent.resolve() / db_path

symbols_df = pd.read_csv(symbols_file)
prices_df = pd.read_csv(prices_file)
screener_df = pd.read_csv(screener_file)

# Tạo file SQLite mới
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Bật hỗ trợ khóa ngoại (bắt buộc trong SQLite)
cursor.execute("PRAGMA foreign_keys = ON;")

# Tạo bảng symbols
cursor.execute("""
CREATE TABLE IF NOT EXISTS vnstock_symbols (
    symbol TEXT PRIMARY KEY,
    organ_short_name TEXT,
    organ_name TEXT
);
""")

# Tạo bảng screener
cursor.execute("""
CREATE TABLE IF NOT EXISTS vnstock_screeners (
    ticker TEXT PRIMARY KEY,
    exchange TEXT,
    industry TEXT,
    market_cap REAL,
    roe REAL,
    stock_rating REAL,
    business_operation REAL,
    business_model REAL,
    financial_health REAL,
    alpha REAL,
    beta REAL,
    uptrend TEXT,
    active_buy_pct REAL,
    strong_buy_pct REAL,
    high_vol_match REAL,
    forecast_vol_ratio REAL,
    pe REAL,
    pb REAL,
    ev_ebitda REAL,
    dividend_yield REAL,
    price_vs_sma5 TEXT,
    price_vs_sma20 TEXT,
    revenue_growth_1y REAL,
    revenue_growth_5y REAL,
    eps_growth_1y REAL,
    eps_growth_5y REAL,
    gross_margin REAL,
    net_margin REAL,
    doe REAL,
    avg_trading_value_5d REAL,
    avg_trading_value_10d REAL,
    avg_trading_value_20d REAL,
    relative_strength_3d INTEGER,
    rel_strength_1m INTEGER,
    rel_strength_3m INTEGER,
    rel_strength_1y INTEGER,
    total_trading_value REAL,
    foreign_transaction TEXT,
    price_near_realtime REAL,
    rsi14 REAL,
    foreign_vol_pct REAL,
    tc_rs INTEGER,
    tcbs_recommend TEXT,
    tcbs_buy_sell_signal TEXT,
    foreign_buysell_20s REAL,
    num_increase_continuous_day INTEGER,
    num_decrease_continuous_day INTEGER,
    eps REAL,
    macd_histogram TEXT,
    vol_vs_sma5 REAL,
    vol_vs_sma10 REAL,
    vol_vs_sma20 REAL,
    vol_vs_sma50 REAL,
    price_vs_sma10 TEXT,
    price_vs_sma50 TEXT,
    price_break_out52_week TEXT,
    price_wash_out52_week TEXT,
    sar_vs_macd_hist TEXT,
    bolling_band_signal TEXT,
    dmi_signal TEXT,
    rsi14_status TEXT,
    price_growth_1w REAL,
    price_growth_1m REAL,
    breakout TEXT,
    prev_1d_growth_pct REAL,
    prev_1m_growth_pct REAL,
    prev_1y_growth_pct REAL,
    prev_5y_growth_pct REAL,
    has_financial_report TEXT,
    free_transfer_rate INTEGER,
    net_cash_per_market_cap REAL,
    net_cash_per_total_assets REAL,
    profit_last_4q REAL,
    last_quarter_revenue_growth REAL,
    second_quarter_revenue_growth REAL,
    last_quarter_profit_growth REAL,
    second_quarter_profit_growth REAL,
    pct_1y_from_peak REAL,
    pct_away_from_hist_peak REAL,
    pct_1y_from_bottom REAL,
    pct_off_hist_bottom REAL,
    price_vs_sma100 TEXT,
    heating_up TEXT,
    price_growth1_day REAL,
    vsma5 REAL,
    vsma10 REAL,
    vsma20 REAL,
    vsma50 REAL,
    corporate_percentage REAL,
    ev INTEGER,
    quarter_revenue_growth REAL,
    quarter_income_growth REAL,
    peg_forward REAL,
    peg_trailing REAL,
    quarterly_income REAL,
    quarterly_revenue REAL,
    ps REAL,
    roa REAL,
    npl REAL,
    nim REAL,
    price_vs_sma200 TEXT,
    eps_ttm_growth1_year REAL,
    eps_ttm_growth5_year REAL,
    equity_mi INTEGER,
    eps_recently INTEGER,
    percent_price_vs_ma200 REAL,
    percent_price_vs_ma20 REAL,
    percent_price_vs_ma50 REAL,
    percent_price_vs_ma100 REAL,
    FOREIGN KEY (ticker) REFERENCES vnstock_symbols(symbol) ON DELETE CASCADE ON UPDATE CASCADE
);
""")

# Tạo bảng prices với ràng buộc khóa ngoại tới symbols
cursor.execute("""
CREATE TABLE IF NOT EXISTS vnstock_prices (
    time TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    ticker TEXT,
    FOREIGN KEY (ticker) REFERENCES vnstock_symbols(symbol) ON DELETE CASCADE ON UPDATE CASCADE
);
""")

# Ghi dữ liệu vào bảng
symbols_df.to_sql("vnstock_symbols", conn, if_exists="append", index=False)
prices_df.to_sql("vnstock_prices", conn, if_exists="append", index=False)
screener_df.to_sql("vnstock_screeners", conn, if_exists="append", index=False)

# Kiểm tra ràng buộc FK có hoạt động
cursor.execute("PRAGMA foreign_key_check;")
fk_issues = cursor.fetchall()

if fk_issues:
    print("Foreign key constraint issues:", fk_issues)
else:
    print("Database created successfully with foreign key constraint!")

conn.commit()
conn.close()