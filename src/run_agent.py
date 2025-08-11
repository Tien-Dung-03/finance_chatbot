import os
import re
import logging
from typing import Dict, List, Any
from pathlib import Path
import json
import asyncio

from src.tools.vnstockquery_tool import VNStockQueryTool
from src.create_agent import Agent

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
        logging.FileHandler('log/portfolio_optimization.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()

def load_system_prompt(file_name: str = 'config/system_prompt.txt') -> str:
    """
    Load system prompt from a text file

    Args:
        file_name (str): File path to system prompt txt file
    
    Returns:
        str: system_prompt
    """
    try:
        # Get the current file's directory
        current_dir = Path(__file__).parent
        prompt_path = current_dir / file_name
        
        return prompt_path.read_text(encoding='utf-8').strip()
    except FileNotFoundError:
        logger.warning("System prompt file not found. Using default.")
        return """You are an Investment Portfolio Analysis Agent..."""
    except Exception as e:
        logger.error(f"Error loading system prompt: {str(e)}")
        return """You are an Investment Portfolio Analysis Agent..."""


def execute_tool_action(chosen_tool, args_str):
    vnstockquery_tool = VNStockQueryTool()

    if chosen_tool =="query_vnstock_data":
        try:
            result = vnstockquery_tool.query_vnstock_data(args_str)
            logger.info(f"Tool result for query '{args_str}': {result}")
            return result
        except Exception as e:
            logger.error(f"Error in query_vnstock_data: {e}")
            return f"Error running VNStock query: {e}"
    else:
        logger.error(f"Unknown tool: {chosen_tool}")
        return f"Error: Tool {chosen_tool} not recognized."


def agent_loop(max_iterations, system_prompt, query):
    """
    Execute agent interaction loop for portfolio analysis.

    Args:
        max_iterations (int): Maximum number of interaction iterations
        system_prompt (str): Initial system prompt for agent guidance
        query (str): Initial user query

    Returns:
        None: Prints analysis results
    """
    # Initialize Groq client
    api_key=os.getenv('GROQ_API_KEY')
    if not api_key:
        logger.error("GROQ_API_KEY is not set in environment variables.")
        return

    client = Groq(api_key=api_key)
    agent = Agent(client, system_prompt)

    next_prompt = query
    for iteration in range(max_iterations):
        result = agent(next_prompt)
        print(f"\n{'='*50}")
        print(f"Iteration {iteration + 1}:")
        print(result)   

        if "Answer" in result:
            break

        if "PAUSE" in result and "Action" in result:
            action_match = re.search(r"Action: ([a-z_]+): (.+)", result, re.IGNORECASE)
            if action_match:
                chosen_tool, args_str = action_match.groups()
                observation = execute_tool_action(chosen_tool, args_str)
                next_prompt = f"Observation: {observation}"             
                print(next_prompt)
                continue

def main():
    """
    Main execution function demonstrating investment analysis capabilities.
    """
    system_prompt = load_system_prompt('config/system_prompt.txt.txt')
    agent_loop(max_iterations=5, system_prompt=system_prompt, query="Giá đóng cửa cao nhất của Vietcombank từ ngày 15 tháng 3 năm 2024 đến ngày 20 tháng 3 năm 2024?")

if __name__ == "__main__":
    main()
