# vnstockquery_tool.py
import logging
from data.stock import VNStockData

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/portfolio_optimization.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class VNStockQueryTool:
    def __init__(self):
        self.db = VNStockData()

    def query_vnstock_data(self, query: str) -> str:
        if not self.db.conn:
            logger.error("Cannot execute query: database connection is not established")
            return "Error: No database connection. Please check the database file."
        try:
            logger.debug(f"Executing SQL query: {query}")
            cursor = self.db.conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            logger.debug(f"Query result: {result}")
            if not result:
                logger.info("Query returned empty result")
                return "No data found for the given query."

            headers = [desc[0] for desc in cursor.description]
            formatted_rows = []
            for row in result:
                row_str = ", ".join([f"{col}: {val}" for col, val in zip(headers, row)])
                formatted_rows.append(row_str)
            return "\n".join(formatted_rows)
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return f"Error: Unable to execute query - {str(e)}"