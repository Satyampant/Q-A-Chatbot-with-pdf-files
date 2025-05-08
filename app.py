import streamlit as st
import os
import time
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader

# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize LLM
llm = ChatGroq(api_key=groq_api_key, model="Llama3-8b-8192")

# Prompt template
prompt = ChatPromptTemplate.from_template("""
Answer the following questions based on the provided context only.
Please provide the most accurate response based on the question.
<context>
{context}
<context>
Question: {input}
""")

# Create embeddings and vectorstore
def create_vector_embeddings():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    loader = PyPDFDirectoryLoader("research papers")
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    final_documents = text_splitter.split_documents(docs[:50])

    vectorstore = FAISS.from_documents(final_documents, embeddings)
    return vectorstore

# Streamlit UI
st.title("PDF QA using Groq + HuggingFace Embeddings")

if "vectors" not in st.session_state:
    if st.button("Create Document Embedding"):
        with st.spinner("Creating embeddings and vector store..."):
            st.session_state.vectors = create_vector_embeddings()
            st.success("Vector database is ready.")

if "vectors" in st.session_state:
    user_prompt = st.text_input("Enter your query based on the uploaded PDFs:")

    if user_prompt:
        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = st.session_state.vectors.as_retriever()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        start = time.process_time()
        response = retrieval_chain.invoke({'input': user_prompt})
        st.write(f"Response time: {time.process_time() - start:.2f}s")

        st.subheader("Answer")
        st.write(response['answer'])

        with st.expander("Retrieved Context Documents"):
            for i, doc in enumerate(response['context']):
                st.markdown(f"**Document {i+1}**")
                st.write(doc.page_content)
                st.write("---")
