import os
import re
import logging
from typing import Dict, List, Any
from pathlib import Path

from tools.financial_tool import FinancialTool

import dotenv
import pandas as pd
from groq import Groq

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

# Load environment variables
dotenv.load_dotenv()

# Agent
class Agent:
    def __init__(self, client, system):
        self.client = client
        self.system = system
        self.messages = []
        
        if self.system:
            self.messages.append({"role": "system", "content": self.system})
            
    def __call__(self, message=""):
        if message:
            self.messages.append({"role": "user", "content": message})
        result = self.execute()
        return result
    
    def execute(self):
        try:
            completion = self.client.chat.completions.create(
                messages=self.messages,
                model="llama3-70b-8192",
            )
            result = completion.choices[0].message.content
            self.messages.append({"role": "assistant", "content": result})
            logger.debug(f"Groq API response: {result}")
            return result
        except Exception as e:
            logger.error(f"Error during Groq API call: {e}")
            return f"Error: Unable to process your request - {str(e)}"

def load_system_prompt(file_name: str = 'system_prompt_v1.txt') -> str:
    try:
        current_dir = Path(__file__).parent
        prompt_path = current_dir / file_name
        logger.info(f"Loading system prompt from {prompt_path}")
        return prompt_path.read_text(encoding='utf-8').strip()
    except FileNotFoundError:
        logger.warning("System prompt file not found. Using default.")
        return """You are an Investment Portfolio Analysis Agent..."""
    except Exception as e:
        logger.error(f"Error loading system prompt: {e}")
        return """You are an Investment Portfolio Analysis Agent..."""

def execute_tool(chosen_tool: str, args_str: str) -> str:
    financial_tool = FinancialTool()
    if chosen_tool == "query_stock_data":
        result = financial_tool.query_stock_data(args_str)
        logger.info(f"Tool result for query '{args_str}': {result}")
        return result
    elif chosen_tool == "query_stock_info":
        result = financial_tool.query_stock_info(args_str)
        logger.info(f"Tool result for query '{args_str}': {result}")
        return result
    elif chosen_tool == "plot_result":
        financial_tool.plot_result(args_str)
        logger.info(f"Tool executed plot_result with args: {args_str}")
        return "Chart generated successfully."
    else:
        logger.error(f"Unknown tool: {chosen_tool}")
        return f"Error: Tool {chosen_tool} not recognized."

def agent_loop(max_iterations: int, system_prompt: str, query: str) -> str:
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        logger.error("GROQ_API_KEY not set in environment variables.")
        return "Error: GROQ_API_KEY is not set."
    
    client = Groq(api_key=api_key)
    agent = Agent(client, system_prompt)
    
    # Gọi Groq API một lần để tạo truy vấn SQL
    result = agent(query)
    logger.info(f"Agent response: {result}")
    print(f"Agent response: {result}")

    # Kiểm tra phản hồi từ agent
    if "Error" in result:
        return result
    if "Action: query_stock_data" in result:
        action_match = re.search(r"Action:\s*([a-z_]+):\s*(.+)", result, re.IGNORECASE | re.DOTALL)
        if action_match:
            chosen_tool, args_str = action_match.groups()
            observation = execute_tool(chosen_tool, args_str)
            logger.info(f"Observation: {observation}")
            print(f"Observation: {observation}")
            
            if observation.strip().lower().startswith("no data found"):
                ticker_match = re.search(r"Ticker\s*=\s*'([^']+)'", args_str)
                tickers_match = re.search(r"Ticker\s*IN\s*\(([^)]+)\)", args_str, re.IGNORECASE)
                date_match = re.search(r"Date\s*=\s*'([^']+)'", args_str)
                if ticker_match:
                    ticker_info = ticker_match.group(1)
                elif tickers_match:
                    ticker_info = tickers_match.group(1).replace("'", "").replace(",", ", ")
                else:
                    ticker_info = "specified ticker(s)"
                date_info = date_match.group(1) if date_match else "specified date"
                return f"No data found for {ticker_info} on {date_info}."

            # Sau khi có dữ liệu truy vấn (observation), gọi lại LLM để phân tích
            followup_prompt = f"""User question: {query}

            SQL result:
            {observation}

            Based on the result above, answer the user's question in natural language.
            """
            interpretation = agent(followup_prompt)
            logger.info(f"Final interpretation: {interpretation}")
            return interpretation
    elif "Action: query_stock_info" in result:
        action_match = re.search(r"Action:\s*([a-z_]+):\s*(.+)", result, re.IGNORECASE | re.DOTALL)
        if action_match:
            chosen_tool, args_str = action_match.groups()
            observation = execute_tool(chosen_tool, args_str)
            logger.info(f"Observation: {observation}")
            print(f"Observation: {observation}")
            
            if observation.strip().lower().startswith("no data found"):
                symbol_match = re.search(r"symbol\s*=\s*'([^']+)'", args_str, re.IGNORECASE)
                symbol_info = symbol_match.group(1) if symbol_match else "specified symbol"
                return f"No company info found for {symbol_info}."

            followup_prompt = f"""User question: {query}

            SQL result:
            {observation}

            Based on the result above, answer the user's question in natural language.
            """
            interpretation = agent(followup_prompt)
            logger.info(f"Final interpretation: {interpretation}")
            return interpretation
    elif "Action: plot_result" in result:
        action_match = re.search(r"Action:\s*([a-z_]+):\s*(.+)", result, re.IGNORECASE | re.DOTALL)
        if action_match:
            chosen_tool, args_str = action_match.groups()
            observation = execute_tool(chosen_tool, args_str)
            logger.info(f"Observation: {observation}")
            print(f"Observation: {observation}")
            return observation

    return result