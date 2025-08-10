import os
import re
import logging
from typing import Dict, List, Any
from pathlib import Path
import json
import asyncio

from src.tools.vnstockquery_tool import VNStockQueryTool
from src.tools.serperdev_tool import SerperDevToolAsync
from src.agent.create_agent import Agent

import dotenv
import pandas as pd
from groq import Groq

import nest_asyncio
nest_asyncio.apply()

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

# Load environment variables
dotenv.load_dotenv()

def load_system_prompt(file_name: str = '../agent/system_prompt.txt') -> str:
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
    vnstockquery_tool = VNStockQueryTool()
    serperdev_tool = SerperDevToolAsync(api_key=os.getenv('SERPER_API_KEY'))

    if chosen_tool == "query_vnstock_data":
        try:
            result = vnstockquery_tool.query_vnstock_data(args_str)
            logger.info(f"Tool result for query '{args_str}': {result}")
            return result
        except Exception as e:
            logger.error(f"Error in query_vnstock_data: {e}")
            return f"Error running VNStock query: {e}"

    elif chosen_tool == "call_serper_search":
        try:
            # args_str có thể là JSON string như: { "query": "Khái niệm về chỉ số roe" }
            search_params = json.loads(args_str) if isinstance(args_str, str) else args_str
            search_query = search_params.get("query")
            if not search_query:
                return "Error: Missing 'query' parameter for call_serper_search"

            logger.info(f"Calling SerperDevToolAsync with query: {search_query}")

            # Luôn chạy trong context async an toàn
            result = asyncio.run(serperdev_tool.run(search_query=search_query, n_results=5))
            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error in call_serper_search: {e}")
            return f"Error running Serper search: {e}"
        
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
    
    # Nếu Agent trả về call_serper_search
    if "Action: call_serper_search" in result:
        action_match = re.search(r"Action:\s*([a-z_]+):\s*(\{.*\})", result, re.IGNORECASE | re.DOTALL)
        if action_match:
            chosen_tool, args_str = action_match.groups()
            search_result = execute_tool(chosen_tool, args_str)

            logger.info(f"Serper search result: {search_result}")
            print(f"Serper search result: {search_result}")
            
            # Ghép kết quả tìm kiếm với câu hỏi gốc
            followup_prompt = f"""User question: {query}

            Serper search result:
            {search_result}

            Based on the result above, answer the user's question in natural language.
            """
            interpretation = agent(followup_prompt)
            logger.info(f"Final interpretation: {interpretation}")
            return interpretation
            
    if "Action: query_vnstock_data" in result:
        action_match = re.search(r"Action:\s*([a-z_]+):\s*(.+)", result, re.IGNORECASE | re.DOTALL)
        if action_match:
            chosen_tool, args_str = action_match.groups()
            observation = execute_tool(chosen_tool, args_str)
            logger.info(f"Observation: {observation}")
            print(f"Observation: {observation}")

            # Sau khi có dữ liệu truy vấn (observation), gọi lại LLM để phân tích
            followup_prompt = f"""User question: {query}

            SQL result:
            {observation}

            Based on the result above, answer the user's question in natural language.
            """
            interpretation = agent(followup_prompt)
            logger.info(f"Final interpretation: {interpretation}")
            return interpretation
    
    return result