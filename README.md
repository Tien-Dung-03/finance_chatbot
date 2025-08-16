# Financial Chatbot

## 📌 Introduction
Financial Chatbot is an **AI Agent** system that acts as a financial investment assistant.  
The application can:
- Understand user questions in natural language.
- Automatically convert questions into **SQL queries** or search the web via Google.
- Execute queries, retrieve data from the Vietnam stock market database.
- Return results in natural language.

## 👨‍🏫 How ReAct Agent works

The Investment Portfolio Analysis AI Agent is built on the ReAct (Reasoning and Action) framework, which combines the strength of large language models with a structured approach to problem-solving. Here's the workflow:

1. **Thought**: The agent analyzes the user's query and formulates a plan of action.
2. **Action**: Based on the thought, the agent selects and executes an appropriate tool or API call.
3. **Observation**: The agent observes and interprets the results of the action.
4. **Repeat**: This cycle continues until the agent has gathered enough information to provide a comprehensive answer.

### Extension to Tool Calling
The ReAct framework can be extended to incorporate specialized tools:
- **Tool Definition**: Each tool (e.g., vnstockquery_tool) is defined with clear inputs and outputs.
- **Tool Selection**: The agent learns to choose the most appropriate tool based on the current context and user query.
- **Tool Execution**: The selected tool is called with the necessary parameters.
- **Result Integration**: The agent incorporates tool outputs into its reasoning process for the final response.
This extension allows the agent to leverage specific  functions while maintaining a flexible, language-model-driven interaction flow.

## ⚙️ Technologies Used
- **Python 3.8+**
- **Streamlit** – interactive web interface.
- **Groq API** – natural language processing.
- **LangChain / AI Agent logic** – orchestrating the processing flow.
- **SQLite** – stock market database storage.
- **SerperDevTool** – Google search integration.

## 🗂 Project Structure
```
.
├── data
├── ├── auto_down_data                 # Folder containing files that automatically download data and transfer to db
├── ├── csv_file                       # Folder containing csv files
├── ├── memory                         # Folder containing chat history db
├── ├── stock.py                       # Database connection & query for stock data
├── log                                # Log folder
├── src
├── ├── config
├── ├── ├── systerm_prompt             # Prompt
├── ├── history
├── ├── ├── sqlite_memory              # Create SQL file of chat memory
├── ├── ├── summarizer_groq.py         # Chat history summary agent
├── ├── create_agent.py                # Agent class connecting to Groq API
├── ├── run_agent.py                   # Agent loop, main logic
├── ├── tools
├── ├── ├── vnstockquery_tool.py       # VNStock data query tool
├── ├── ├── serperdev_tool.py          # Google search tool
├── app.py                             # Streamlit interface
└── requirements.txt                   # Required dependencies
```

## 📥 Installation

1. **Clone the repository**
```bash
git clone https://github.com/Tien-Dung-03/finance_chatbot
cd financial-chatbot
```

2. **Create and activate a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set environment variables**
Create a `.env` file and add:
```env
GROQ_API_KEY=your_groq_api_key
SERPER_API_KEY=your_serper_api_key
```

5. **Prepare the data**
Run one after another to download data:
``` bash
python ./data/auto_down_data/download_vnstock_prices.py
python ./data/auto_down_data/download_vnstock_prices.py
```
Then run
``` bash
python ./data/auto_down_data/import_to_sql.py
```
to create `vnstock_data.db`

## 🚀 Run the Application
```bash
streamlit run app.py
```
After running, open your browser at `http://localhost:8501`.

## 💡 Usage
1. Select **Task**: currently supports `VNStock Data Lookup`.
2. Enter a question in Vietnamese, e.g.:
   ```
   Giá đóng cửa của cổ phiếu Vietcombank vào ngày 15 tháng 3 năm 2024?
   ```
   Or English:
   ```
   What is closing price of Vietcombank shares on March 15, 2024?
   ```
3. Click **Submit** to get the answer.
4. Optionally, view the **Log file** to check the processing steps.

## 🛠 Key Features
- **Query Vietnam stock market data** from the database.
- **Search information on Google** when data is not available locally.
- **Detailed logging** for debugging.

## 📄 License
MIT License.
