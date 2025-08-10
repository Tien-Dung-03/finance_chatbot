import streamlit as st
from src.run.run_agent import load_system_prompt, agent_loop
from PIL import Image
import os
from pathlib import Path
import json

# Streamlit app
st.title("Financial Chatbot")


# Sidebar for selecting task
task = st.sidebar.selectbox(
    "Select Task",
    ["VNStock Data Lookup"]
)

# Input query
query = st.text_input("Nhập câu hỏi của bạn:", 
                      placeholder="E.g., Giá đóng cửa của cổ phiếu Vietcombank vào ngày 15 tháng 3 năm 2024?")

# Button to submit query
if st.button("Submit"):
    if query:
        system_prompt = load_system_prompt()
        with st.spinner("Processing..."):
            result = agent_loop(max_iterations=1, system_prompt=system_prompt, query=query)    
        st.write("**Result:**")
        # st.write(result)
        st.markdown(result)
    else:
        st.error("Please enter a query.")

# Display log file
if st.sidebar.button("View Log"):
    log_file = "log/finance_chatbot.log"
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        st.text_area("Log File", log_content, height=300)
    except FileNotFoundError:
        st.error("Log file not found.")