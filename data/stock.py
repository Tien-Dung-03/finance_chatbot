# stock.py
from pathlib import Path
import logging
import sqlite3
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/finance_chatbot.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class VNStockData:
    def __init__(self, db_path: str = 'vnstock_data.db'):
        try:
            current_dir = Path(__file__).parent.resolve()
            self.db_path = current_dir / db_path  
            logger.info(f"Using database path: {self.db_path}")
            self.conn = self.connect_db()
        except Exception as e:
            logger.error(f"Error in StockData initialization: {e}")
            self.conn = None
        
    def connect_db(self) -> sqlite3.Connection:
        if not os.path.exists(self.db_path):
            logger.error(f"Database file not found at {self.db_path}")
            return None
        try:
            conn = sqlite3.connect(self.db_path)
            logger.info(f"Successfully connected to database {self.db_path}")
            return conn
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return None

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logger.info(f"Closed database connection {self.db_path}")
