import streamlit as st
from src.run_agent import load_system_prompt, agent_loop
from pathlib import Path
import logging
from typing import Dict
import re

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/portfolio_optimization.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_output(max_iterations: int, system_prompt: str, query: str) -> Dict[str, str]:
    """
    Chạy agent_loop và thu kết quả đầy đủ + câu trả lời cuối cùng.
    
    Args:
        max_iterations (int): Số vòng lặp tối đa của agent.
        system_prompt (str): Prompt hệ thống cho agent.
        query (str): Câu hỏi từ người dùng.

    Returns:
        Dict[str, str]: Gồm 'full_output', 'final_answer', 'observations'
    """
    import io
    import sys

    output_buffer = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = output_buffer

    try:
        logger.info(f"Running agent with query: {query}")

        # Chạy agent
        agent_loop(max_iterations, system_prompt, query)

        # Lấy output từ agent
        full_output = output_buffer.getvalue()

        # Regex lấy Answer
        answer_match = re.search(
            r'(?:\*\*Answer\*\*|Answer)\s*:\s*(.*)',
            full_output,
            re.DOTALL | re.IGNORECASE
        )
        final_answer = answer_match.group(1).strip() if answer_match else "No specific answer found."

        # Regex lấy tất cả Observation
        observations = re.findall(
            r'Observation\s*:\s*(.*?)(?=\n(?:Thought|Answer|\Z))',
            full_output,
            re.DOTALL | re.IGNORECASE
        )

        return {
            'full_output': full_output.strip(),
            'final_answer': final_answer,
            'observations': [obs.strip() for obs in observations if obs.strip()]
        }

    except Exception as e:
        logger.error(f"Error in capture_output: {str(e)}", exc_info=True)
        return {
            'full_output': f"Error: {str(e)}",
            'final_answer': f"Error processing query: {str(e)}",
            'observations': []
        }
    finally:
        sys.stdout = original_stdout


def main():
    st.set_page_config(
        page_title="Portfolio Optimization AI Assistant", 
        page_icon="📈", 
        layout="wide"
    )

    st.title("🤖 Portfolio Optimization ReAct AI Agent")

    # system_prompt = load_system_prompt()
    @st.cache_data
    def get_system_prompt():
        return load_system_prompt()
    system_prompt = get_system_prompt()

    st.markdown("### Example Queries")
    st.markdown("Select a predefined query or enter your own below:")

    example_queries = [
        "",
        "Lấy giá đóng cửa và khối lượng giao dịch của VCB vào ngày 15/03/2024",
        "Giá mở cửa của Công ty Cổ phần Tập đoàn Yeah1 vào ngày 10/04/2024",
        "Danh sách cổ phiếu có P/E nhỏ hơn 10 và ROE lớn hơn 15%",
        "Giá cao nhất và P/B của Vietcombank trong tháng 3/2024"   
    ]

    selected_query = st.selectbox("Choose an example query:", [""] + example_queries)

    query = st.text_input(
        "Enter your query or use the selected example above:", 
        value=selected_query,
        placeholder="E.g., Giá đóng cửa cao nhất của Vietcombank từ ngày 15 tháng 3 năm 2024 đến ngày 20 tháng 3 năm 2024?"
    )

    if st.button("Get info🔍"):
        if not query:
            st.error("Please select an example query or enter your own")
            return

        with st.spinner('Generating ⚙️...'):
            try:
                # Capture and display output
                output = capture_output(
                    max_iterations=5,
                    system_prompt=system_prompt,
                    query=query
                )

                st.markdown("### Key Insights 🎯")
                st.text_area("Answer", output['final_answer'], height=200)


                if output['observations']:
                    st.markdown("### 🗂 SQL Query Results")
                    for i, obs in enumerate(output['observations'], 1):
                        st.code(obs, language='sql')

                st.markdown("### 🧠 Full Agent Trace")
                st.code(output['full_output'], language='text')

            except Exception as e:
                logger.error(f"Error in main function: {str(e)}")
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()