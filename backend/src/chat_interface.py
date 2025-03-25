import streamlit as st
from src.retriever import retrieve_similar_docs
from src.llm_chain import ask_llm

def launch_chat_ui():
    st.set_page_config(page_title="Student Advisor Chatbot")
    st.title("🎓 Student Advisor Chatbot")

    query = st.text_input("Ask a question about your university, courses, policies, etc.")

    if query:
        with st.spinner("Thinking..."):
            context = "\n".join(retrieve_similar_docs(query))
            answer = ask_llm(query, context)
            st.markdown(f"**Answer:** {answer}")
