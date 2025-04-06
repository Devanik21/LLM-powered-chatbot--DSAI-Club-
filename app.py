import streamlit as st
import google.generativeai as genai
import os
import PyPDF2
from docx import Document
import json
import pandas as pd
from pptx import Presentation
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
import zipfile
import io
import time
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO

# Initialize Streamlit app
st.set_page_config(page_title="📑 AI Docs", page_icon="📝", layout="wide")
st.title("📑 Document Chat AI")

# Sidebar for API Key and advanced options
with st.sidebar:
    st.header("🔑 API Configuration")
    api_key = st.text_input("Enter Gemini API Key:", type="password")
    
    st.header("⚙️ Advanced Options")
    
    # Feature 1: Model Selection
    # Feature 1: Model Selection
    model_option = st.selectbox(
        "Model Selection:", 
        ["gemini-2.0-flash","gemini-2.0-flash-lite","gemini-2.0-pro-exp-02-05",
"gemini-2.0-flash-thinking-exp-01-21","gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-1.5-pro"]
    )

    
    # Feature 3: Temperature Control
    temperature = st.slider("Temperature:", 0.0, 1.0, 0.7, 0.1)
    
    # Feature 4: Top-p Sampling
    top_p = st.slider("Top-p Sampling:", 0.1, 1.0, 0.9, 0.1)
    
    # Feature 5: Save Responses
    save_responses = st.checkbox("Save Responses to File", False)
    
    # Feature 6: Context Window Size
    context_chunks_limit = st.slider("Context Window Size:", 1, 20, 10)
    
    # Feature 7: Document Analysis Mode
    analysis_mode = st.radio(
        "Document Analysis Mode:",
        ["Q&A", "Summary", "Key Points", "Comparison"]
    )
    
    # Feature 8: Processing Method
    processing_method = st.radio(
        "Processing Method:",
        ["Process All Files", "Process Selected Files"]
    )
    
    # Feature 9: Language Selection
    language = st.selectbox(
        "Response Language:",
        ["English", "Spanish", "French", "German", "Chinese", "Japanese"]
    )
    
    # Feature 10: Document Visualization
    enable_visualization = st.checkbox("Enable Document Visualization", False)

# Increase file upload limit (1GB)
st.session_state["max_upload_size"] = 1 * 1024 * 1024 * 1024  # 1GB

# Text extraction functions
def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    return [page.extract_text() for page in reader.pages if page.extract_text()]

def extract_text_from_docx(uploaded_file):
    doc = Document(uploaded_file)
    return [para.text for para in doc.paragraphs if para.text]

def extract_text_from_txt(uploaded_file):
    return uploaded_file.read().decode("utf-8").split("\n\n")

def extract_text_from_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    return df.astype(str).apply(lambda x: " ".join(x), axis=1).tolist()

def extract_text_from_json(uploaded_file):
    return [json.dumps(json.load(uploaded_file), indent=2)]

def extract_text_from_md(uploaded_file):
    return uploaded_file.read().decode("utf-8").split("\n\n")

def extract_text_from_pptx(uploaded_file):
    presentation = Presentation(uploaded_file)
    return [shape.text for slide in presentation.slides for shape in slide.shapes if hasattr(shape, "text") and shape.text]

def extract_text_from_xlsx(uploaded_file):
    df = pd.read_excel(uploaded_file)
    return df.astype(str).apply(lambda x: " ".join(x), axis=1).tolist()

def extract_text_from_html(uploaded_file):
    return [BeautifulSoup(uploaded_file.read(), "html.parser").get_text()]

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import io
import tempfile

def extract_text_from_epub(uploaded_file):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as temp_file:
        temp_file.write(uploaded_file.getvalue())  # Write uploaded file data to temp file
        temp_file_path = temp_file.name  # Get file path

    # Read the EPUB file from the temporary file
    book = epub.read_epub(temp_file_path)

    # Extract text from the EPUB file
    text_content = [
        BeautifulSoup(item.content, "html.parser").get_text()
        for item in book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT
    ]

    return text_content

# File upload
uploaded_files = st.file_uploader(
    "Upload Documents (PDF, DOCX, TXT, CSV, JSON, MD, PPTX, XLSX, HTML, EPUB)", 
    type=["pdf", "docx", "txt", "csv", "json", "md", "pptx", "xlsx", "html", "epub"], 
    accept_multiple_files=True
)

# For Feature 8: Process Selected Files
if uploaded_files and processing_method == "Process Selected Files":
    file_names = [file.name for file in uploaded_files]
    selected_files = st.multiselect("Select files to process:", file_names, default=file_names)
    uploaded_files = [file for file in uploaded_files if file.name in selected_files]

# Extract and store text
corpus_chunks = []
file_stats = {}
if uploaded_files:
    progress_bar = st.progress(0)
    for i, uploaded_file in enumerate(uploaded_files):
        file_ext = uploaded_file.name.split(".")[-1].lower()
        if file_ext in ["pdf", "docx", "txt", "csv", "json", "md", "pptx", "xlsx", "html", "epub"]:
            start_time = time.time()
            extract_func = globals()[f"extract_text_from_{file_ext}"]
            extracted_chunks = extract_func(uploaded_file)
            corpus_chunks.extend(extracted_chunks)
            
            # Collect stats for visualization
            file_stats[uploaded_file.name] = {
                "size": uploaded_file.size,
                "chunks": len(extracted_chunks),
                "processing_time": time.time() - start_time
            }
        
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    st.success(f"✅ {len(corpus_chunks)} document sections processed successfully!")

# Feature 10: Document Visualization
if enable_visualization and file_stats:
    st.subheader("📊 Document Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # File size chart
        fig, ax = plt.subplots(figsize=(5, 3))
        sizes = [stats["size"]/1024 for stats in file_stats.values()]
        sns.barplot(x=list(file_stats.keys()), y=sizes, ax=ax)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Size (KB)")
        plt.title("Document Sizes")
        plt.tight_layout()
        st.pyplot(fig)
    
    with col2:
        # Chunks per document
        fig, ax = plt.subplots(figsize=(5, 3))
        chunks = [stats["chunks"] for stats in file_stats.values()]
        sns.barplot(x=list(file_stats.keys()), y=chunks, ax=ax)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Chunks")
        plt.title("Document Sections")
        plt.tight_layout()
        st.pyplot(fig)

# User query or analysis mode prompt
if analysis_mode == "Q&A":
    query = st.text_input("Ask a question about the documents:")
elif analysis_mode == "Summary":
    query = "Generate a comprehensive summary of these documents."
elif analysis_mode == "Key Points":
    query = "Extract and organize the key points from these documents."
elif analysis_mode == "Comparison":
    query = "Compare and contrast the main ideas and information across these documents."

# Function to call Gemini API
def query_gemini_rag(query, context_chunks, api_key, model, temp, top_p_val, max_tokens, lang, mode):
    if not api_key:
        return "❌ API key is required."
    
    genai.configure(api_key=api_key)
    model_instance = genai.GenerativeModel(model)
    
    # Different prompts based on analysis mode
    mode_prompts = {
        "Q&A": f"Answer the following question based on the documents: {query}",
        "Summary": "Generate a detailed and structured summary of these documents.",
        "Key Points": "Extract and organize the key points from these documents.",
        "Comparison": "Compare and contrast the main ideas across these documents."
    }
    
    prompt = f"Provide a detailed response in {lang} based on the following document excerpts:\n\n"
    for chunk in context_chunks[:context_chunks_limit]:
        prompt += f"- {chunk[:2000]}\n\n"
    prompt += f"\n\n{mode_prompts[mode]}"
    
    response = model_instance.generate_content(
        prompt, 
        generation_config={
            "temperature": temp,
            "top_p": top_p_val,
            "max_output_tokens": max_tokens
        }
    )
    
    # Save response if option enabled
    if save_responses:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        with open(f"response_{timestamp}.txt", "w") as f:
            f.write(response.text)
    
    return response.text

# Generate response
if query and corpus_chunks and api_key:
    with st.spinner("🔍 Analyzing documents and generating a detailed response..."):
        max_tokens = 8192  # Fixed maximum output length
        response = query_gemini_rag(
            query, 
            corpus_chunks, 
            api_key, 
            model_option,
            temperature, 
            top_p, 
            max_tokens,
            language,
            analysis_mode
        )
        
        # Create downloadable response
        response_download = BytesIO()
        response_download.write(response.encode())
        response_download.seek(0)
        
        st.subheader("💡 AI Response:")
        st.write(response)
        
        st.download_button(
            label="Download Response",
            data=response_download,
            file_name=f"quantum_docs_response_{time.strftime('%Y%m%d-%H%M%S')}.txt",
            mime="text/plain"
        )
