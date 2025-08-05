import matplotlib.pyplot as plt
import pandas as pd
import logging

from data.stock import StockData, StockInfo

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/investment_portfolio.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class FinancialTool:
    def __init__(self):
        self.data = StockData()
        self.info = StockInfo()

    def query_stock_data(self, query: str) -> str:
        if not self.data.conn:
            logger.error("Cannot execute query: database connection is not established")
            return "Error: No database connection. Please check the database file."
        try:
            logger.debug(f"Executing SQL query: {query}")
            cursor = self.data.conn.cursor()
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
        
    def query_stock_info(self, query: str) -> str:
        if not self.info.conn:
            logger.error("Cannot execute query: database connection is not established")
            return "Error: No database connection. Please check the database file."
        try:
            logger.debug(f"Executing SQL query: {query}")
            cursor = self.info.conn.cursor()
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
        
    def plot_result(self, query: str, image_path: str = "src/image/chart_output.png"):
        result_str = self.query_stock_data(query)
        if result_str.startswith("Error") or "No data found" in result_str:
            return

        # Loại biểu đồ
        lower_query = query.lower()
        if "bar" in lower_query:
            chart_type = "bar"
        elif "pie" in lower_query:
            chart_type = "pie"
        elif "scatter" in lower_query:
            chart_type = "scatter"
        elif "hist" in lower_query or "histogram" in lower_query:
            chart_type = "hist"
        elif "boxplot" in lower_query or "box plot" in lower_query:
            chart_type = "boxplot"
        else:
            chart_type = "line"

        # Parse kết quả thành DataFrame
        lines = result_str.strip().split("\n")
        headers = [cell.split(":")[0].strip() for cell in lines[0].split(", ")]
        data_rows = []
        for line in lines:
            values = [cell.split(":")[1].strip() for cell in line.split(", ")]
            data_rows.append(values)
        df = pd.DataFrame(data_rows, columns=headers)

        for col in headers:
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass
        try:
            df[headers[0]] = pd.to_datetime(df[headers[0]])
        except:
            pass
        
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Data rows: {data_rows}")
        logger.debug(f"Chart type: {chart_type}")

        fig, ax = plt.subplots()
        if chart_type == "line":
            x = df[headers[0]]
            for col in headers[1:]:
                ax.plot(x, df[col], label=col)
            ax.set_xlabel(headers[0])
            ax.set_title("Line Chart")
            if len(headers) > 2:
                ax.legend()
        elif chart_type == "bar":
            ax.bar(df[headers[0]], df[headers[1]])
            ax.set_title("Bar Chart")
        elif chart_type == "pie":
            ax.pie(df[headers[1]], labels=df[headers[0]], autopct='%1.1f%%')
            ax.set_title("Pie Chart")
        elif chart_type == "scatter":
            ax.scatter(df[headers[0]], df[headers[1]])
            ax.set_title("Scatter Plot")
        elif chart_type == "hist":
            numeric_cols = [col for col in headers if pd.api.types.is_numeric_dtype(df[col])]
            if numeric_cols:
                ax.hist(df[numeric_cols[0]])
                ax.set_title("Histogram")
        elif chart_type == "boxplot":
            if len(headers) >= 2:
                # if df[headers[0]].dtype != "O":
                #     df[headers[0]] = df[headers[0]].astype(str)  
                # groups = df.groupby(headers[0])[headers[1]].apply(list)
                ax.boxplot(headers, labels=headers.index)
                ax.set_xlabel(headers[0])
                ax.set_ylabel(headers[1])
                ax.set_title("Boxplot of " + headers[1] + " by " + headers[0])

        # Lưu hình
        fig.tight_layout()
        fig.savefig(image_path)
        plt.close(fig)