import streamlit as st
from utils.parser import extract_from_pdf, extract_from_excel
from utils.qa import ask_ollama

st.set_page_config(page_title="Financial QA App", layout="wide")

st.title("📊 Financial Document Question Answering")
st.write("Upload your financial PDF/Excel file and ask questions!")

uploaded_file = st.file_uploader("Upload PDF or Excel", type=["pdf", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        context = extract_from_pdf(uploaded_file)
    else:
        context = extract_from_excel(uploaded_file)

    st.success("✅ Document processed successfully!")

    # Chat interface
    user_question = st.text_input("Ask a question about the document:")

    if user_question:
        with st.spinner("Thinking..."):
            answer = ask_ollama(context, user_question)
        st.subheader("💡 Answer:")
        st.write(answer)
