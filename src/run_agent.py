import os
import re
import logging
from typing import Dict, List, Any
from pathlib import Path
import json
import asyncio

from src.tools.vnstockquery_tool import VNStockQueryTool
from src.tools.serperdev_tool import SerperDevToolAsync

from src.history.sqlite_memory import SQLiteAutoSummaryMemory
from src.history.summarizer_groq import summarizer_fn

memory = SQLiteAutoSummaryMemory(db_path="data/memory/chat_memory.db", summarizer_fn=summarizer_fn, max_turns=6)

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
        logging.FileHandler('log/finance_chatbot.log', mode='a', encoding='utf-8'),
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
    serperdev_tool = SerperDevToolAsync(api_key=os.getenv('SERPER_API_KEY'))

    if chosen_tool == "query_vnstock_data":
        try:
            result = vnstockquery_tool.query_vnstock_data(args_str)
            logger.info(f"Tool result for query '{args_str}': {result}")
            return result
        except Exception as e:
            logger.error(f"Error in query_vnstock_data: {e}")
            return f"Error running VNStock query: {e}"
    elif chosen_tool == "serperdev_tool":
        try:
            # args_str có thể là JSON string như: { "query": "Khái niệm về chỉ số roe" }
            search_params = json.loads(args_str) if isinstance(args_str, str) else args_str
            search_query = search_params.get("query")
            if not search_query:
                return "Error: Missing 'query' parameter for serperdev_tool"
            logger.info(f"Calling SerperDevToolAsync with query: {search_query}")

            # Luôn chạy trong context async an toàn
            result = asyncio.run(serperdev_tool.run(search_query=search_query, n_results=5))
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error in serperdev_tool: {e}")
            return f"Error running Serper Tool {e}"
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
    full_trace = []
    observations = []
    final_answer = ""
    
    for iteration in range(max_iterations):
        result = agent(next_prompt)
        full_trace.append(f"Iteration {iteration+1}:\n{result}")

        # Kiểm tra Answer
        ans_match = re.search(r'(?:\*\*Answer\*\*|Answer)\s*:\s*(.*)', result, re.DOTALL | re.IGNORECASE)
        if ans_match:
            final_answer = ans_match.group(1).strip()
            break

        # Lấy Observation
        obs_match = re.search(r'Observation\s*:\s*(.*)', result, re.DOTALL | re.IGNORECASE)
        if obs_match:
            observation = obs_match.group(1).strip()
            observations.append(observation)

        # Tool Action
        if "PAUSE" in result and "Action" in result:
            action_match = re.search(r"Action: ([a-z_]+): (.+)", result, re.IGNORECASE)
            if action_match:
                chosen_tool, args_str = action_match.groups()
                observation = execute_tool_action(chosen_tool, args_str)
                next_prompt = f"Observation: {observation}"
                continue

    return final_answer, observations, "\n".join(full_trace)
            
def ask_agent(user_id: str, user_input: str, system_prompt: str = None, recent_limit: int = 4, conversation_id: int = None):
    """
    Lưu message -> build context (summary + recent) -> gọi agent_loop (1 iteration) -> lưu reply
    """
    if conversation_id is None:
        conversation_id = memory.create_conversation(user_id, title=user_input[:50])
        
    # 1) save user message
    memory.add_message(user_id, "user", user_input, conversation_id)

    summary = memory.get_summary(conversation_id)
    recent = memory.get_recent_messages(conversation_id, limit=recent_limit)

    context_parts = []
    if summary:
        context_parts.append(f"[Tóm tắt trước đó]: {summary}")
    for role, content in recent:
        context_parts.append(f"{role.capitalize()}: {content}")
    # add the new user message at end (explicit)
    context_parts.append(f"User: {user_input}")

    full_context = "\n".join(context_parts)

    # 3) call agent_loop for single iteration (agent_loop prints output; we capture if needed)
    # use provided system_prompt if given, otherwise load default
    sp = system_prompt if system_prompt is not None else load_system_prompt()

    # Because your agent_loop expects (max_iterations, system_prompt, query), pass 1 iteration
    final_answer, observations, trace = agent_loop(max_iterations=5, system_prompt=sp, query=full_context)

    memory.add_message(user_id, "assistant", final_answer, conversation_id)
    return final_answer, observations, trace, conversation_id

def main():
    """
    Main execution function demonstrating investment analysis capabilities.
    """
    system_prompt = load_system_prompt('config/system_prompt.txt.txt')
    agent_loop(max_iterations=5, system_prompt=system_prompt, query="Giá đóng cửa cao nhất của Vietcombank từ ngày 15 tháng 3 năm 2024 đến ngày 20 tháng 3 năm 2024?")

if __name__ == "__main__":
    main()
