import streamlit as st
from agent.investment_portfolio import load_system_prompt, agent_loop
from PIL import Image
import os
from pathlib import Path

# Streamlit app
st.title("Financial Analysis")

file_name = "image/chart_output.png"

# Sidebar for selecting task
task = st.sidebar.selectbox(
    "Select Task",
    ["Stock Price Lookup"]
)

# Input query
query = st.text_input("Enter your query:", 
                      placeholder="E.g., What was the closing price of Microsoft on March 15, 2024?")


# Button to submit query
if st.button("Submit"):
    if query:
        system_prompt = load_system_prompt()
        with st.spinner("Processing..."):
            result = agent_loop(max_iterations=1, system_prompt=system_prompt, query=query)
        st.write("**Result:**")
        # st.write(result)
        st.markdown(result)
        current_dir = Path(__file__).parent
        image_path = current_dir / file_name
        if os.path.exists(image_path):
            st.image(Image.open(image_path), caption="Generated Chart", use_column_width=True)
            os.remove(image_path)
        else:
            st.warning("Chart image not found.")
    else:
        st.error("Please enter a query.")

# Display log file
if st.sidebar.button("View Log"):
    log_file = "log/investment_portfolio.log"
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        st.text_area("Log File", log_content, height=300)
    except FileNotFoundError:
        st.error("Log file not found.")