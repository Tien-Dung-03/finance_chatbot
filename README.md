# Investment Portfolio AI Agent

## Project Overview

An AI-powered information retrieval tool that uses FinancialTool to query and visualize data to provide information on stock prices as well as technical indicators of stocks. This intelligent agent provides easy, convenient information retrieval and overviews of them.

## Key Features
- **Stock Price Lookup**: Retrieve information about stock prices, technical indicators of that company's stock, visualize query data.

## How It Works

The Agent system acts as a financial investment AI assistant, which can understand natural language and automatically convert user questions into SQL queries, execute them, and display visual results if needed.

1. **Users enter queries naturally:** Example: "What was the closing price of Apple on March 15, 2024?".
2. **Agent receives query and generates SQL:** The agent uses the LLM language model (Groq LLaMA3) to process the query and generate appropriate SQL statements based on the instructions in system_prompt_v1.txt.
3. **Run SQL query:** Agent sử dụng FinancialTool
- Based on Action type:
  - query_stock_data: Query stock price data (stock_price)
  - query_stock_info: Query basic company information (stock_info)
  - plot_result: Query data and create chart and display
4. **Streamlit display:**
- Text results are displayed using st.markdown(result)
- If there is a chart_output.png image, Streamlit will display it using st.image(...)
- After displaying, the image will be automatically deleted to free up memory.

### Extension to Tool Calling

- **Financial Tool**: Query stock prices, query stock related information and visualize query data.

This section allows the agent to leverage specific financial analysis functions while maintaining a flexible interaction flow according to the language model.

## Technologies Used

- **Backend**: Python
- **AI Model**: Groq API
- **Frontend**: Streamlit
- **Key Libraries**:
  - Groq
  - python-dotenv
  - Logging
  - SQLite3
  - Pandas
  - matplotlib

## 🔧 Installation

### Prerequisites
- Python 3.8+
- Groq API Key

### Setup Steps
1. Clone the repository
```bash
git clone https://github.com/yourusername/investment-portfolio-ai.git
cd finance_chatbot
```

2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
- Create a `.env` file
- Add your Groq API key: `GROQ_API_KEY=your_groq_api_key`

## Usage

### Streamlit Web Application
```bash
streamlit run src/app.py
```

### Example Queries
- "What was the closing price of Microsoft on March 15, 2024?"
- "On January 15, 2025, which company had a higher closing price, Apple or Microsoft?"
- "What is the ticker symbol for Walt Disney?"
- "Plot the time series of Microsoft (MSFT) stock closing price from June 1, 2024 to September 30, 2024."

### Key Components
- **FinancialTools**: Intuitive, query method
- **Agent**: Intelligent interaction and tool selection
- **Streamlit Interface**: User-friendly web application

## Acknowledgments

- Groq for providing the API used in this project.
- Streamlit for the excellent web app framework.