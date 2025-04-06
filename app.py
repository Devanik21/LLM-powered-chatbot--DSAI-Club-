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
import tempfile
from PIL import Image

# Set modern theme with custom styling
st.set_page_config(
    page_title=" AI Docs", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced UI
st.markdown("""
<style>
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 2rem;
        background: linear-gradient(to right, #EEF2FF, #E0E7FF);
        border-radius: 10px;
    }
    .subheader {
        font-weight: 600;
        color: #3B82F6;
        border-left: 4px solid #3B82F6;
        padding-left: 10px;
    }
    .sidebar-header {
        font-weight: 600;
        color: #1E3A8A;
        margin-top: 1rem;
    }
    .stButton>button {
        background-color: #3B82F6;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #2563EB;
    }
    .stProgress .st-bo {
        background-color: #3B82F6;
    }
    .file-upload-container {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px dashed #CBD5E1;
    }
    .success-message {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .spinner-message {
        background-color: #EFF6FF;
        color: #1E40AF;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 1rem 0;
    }
    .response-container {
        background-color: #F9FAFB;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #3B82F6;
        margin-top: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# App Header with improved design
st.markdown('<div class="main-header"><h1>📑 Document Chat AI</h1><p>Intelligent document analysis powered by Gemini AI</p></div>', unsafe_allow_html=True)

# Sidebar for API Key and advanced options with improved styling
with st.sidebar:
    st.markdown('<div class="sidebar-header">🔑 API Configuration</div>', unsafe_allow_html=True)
    api_key = st.text_input("Enter Gemini API Key:", type="password", 
                          help="Your API key is stored only for this session and never saved")
    
    st.markdown('<div class="sidebar-header">⚙️ Advanced Options</div>', unsafe_allow_html=True)
    
    # Model Selection with improved UI
    model_option = st.selectbox(
        "Model Selection:", 
        ["gemini-2.0-flash","gemini-2.0-flash-lite","gemini-2.0-pro-exp-02-05",
        "gemini-2.0-flash-thinking-exp-01-21","gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-1.5-pro"]
    )
    
    # UI Improvements: Group related settings
    with st.expander("Generation Parameters", expanded=False):
        # Temperature Control
        temperature = st.slider("Temperature:", 0.0, 1.0, 0.7, 0.1,
                            help="Higher values make output more creative, lower values more deterministic")
        
        # Top-p Sampling
        top_p = st.slider("Top-p Sampling:", 0.1, 1.0, 0.9, 0.1,
                        help="Controls diversity of generated text")
    
    with st.expander("Document Processing", expanded=False):
        # Context Window Size
        context_chunks_limit = st.slider("Context Window Size:", 1, 20, 10,
                                      help="Number of document chunks to include in context")
        
        # Processing Method
        processing_method = st.radio(
            "Processing Method:",
            ["Process All Files", "Process Selected Files"],
            help="Choose whether to process all uploaded files or only selected ones"
        )
    
    with st.expander("Analysis Settings", expanded=True):
        # Document Analysis Mode
        analysis_mode = st.radio(
            "Document Analysis Mode:",
            ["Q&A", "Summary", "Key Points", "Comparison"],
            help="Choose how you want the AI to analyze your documents"
        )
        
        # Language Selection
        language = st.selectbox(
            "Response Language:",
            ["English", "Spanish", "French", "German", "Chinese", "Japanese"],
            help="Language for AI responses"
        )
        
        # Save Responses
        save_responses = st.checkbox("Save Responses to File", False,
                                  help="Automatically save responses to a text file")
        
        # Document Visualization
        enable_visualization = st.checkbox("Enable Document Visualization", False,
                                        help="Show charts with document statistics")

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

# Add new image extraction functions
def extract_text_from_jpg(uploaded_file):
    # For images, we just add a placeholder description since we can't extract text directly
    # In a real app, you might want to use OCR here
    return [f"[Image file: {uploaded_file.name}]"]

def extract_text_from_png(uploaded_file):
    # Same approach as JPG
    return [f"[Image file: {uploaded_file.name}]"]

# Enhanced file upload UI
st.markdown('<div class="subheader">📤 Upload Documents</div>', unsafe_allow_html=True)
st.markdown('<div class="file-upload-container">', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "Drag and drop or click to browse files", 
    type=["pdf", "docx", "txt", "csv", "json", "md", "pptx", "xlsx", "html", "epub", "jpg", "png"], 
    accept_multiple_files=True,
    help="Supported formats: PDF, DOCX, TXT, CSV, JSON, MD, PPTX, XLSX, HTML, EPUB, JPG, PNG"
)
st.markdown('</div>', unsafe_allow_html=True)

# For Feature 8: Process Selected Files with improved UI
if uploaded_files and processing_method == "Process Selected Files":
    st.markdown('<div class="subheader">🔍 Select Files to Process</div>', unsafe_allow_html=True)
    file_names = [file.name for file in uploaded_files]
    selected_files = st.multiselect("Select files to process:", file_names, default=file_names)
    uploaded_files = [file for file in uploaded_files if file.name in selected_files]

# Extract and store text with improved progress tracking
corpus_chunks = []
file_stats = {}
if uploaded_files:
    st.markdown('<div class="subheader">⏳ Processing Documents</div>', unsafe_allow_html=True)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        file_ext = uploaded_file.name.split(".")[-1].lower()
        supported_formats = ["pdf", "docx", "txt", "csv", "json", "md", "pptx", "xlsx", "html", "epub", "jpg", "png"]
        
        if file_ext in supported_formats:
            start_time = time.time()
            status_text.text(f"Processing: {uploaded_file.name}")
            
            # Handle image files specially
            if file_ext in ["jpg", "png"]:
                extract_func = globals()[f"extract_text_from_{file_ext}"]
            else:
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
    
    st.markdown(f'<div class="success-message">✅ {len(corpus_chunks)} document sections processed successfully!</div>', unsafe_allow_html=True)

# Feature 10: Document Visualization with improved design
if enable_visualization and file_stats:
    st.markdown('<div class="subheader">📊 Document Analysis</div>', unsafe_allow_html=True)
    
    # Set custom Seaborn style for better visualizations
    sns.set_style("whitegrid")
    sns.set_palette("Blues_d")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # File size chart
        fig, ax = plt.subplots(figsize=(5, 3))
        sizes = [stats["size"]/1024 for stats in file_stats.values()]
        bars = sns.barplot(x=list(file_stats.keys()), y=sizes, ax=ax)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Size (KB)")
        plt.title("Document Sizes")
        plt.tight_layout()
        
        # Add value labels to bars
        for bar in bars.patches:
            bars.text(
                bar.get_x() + bar.get_width()/2.,
                bar.get_height(),
                f'{int(bar.get_height())}',
                ha="center", va="bottom"
            )
            
        st.pyplot(fig)
    
    with col2:
        # Chunks per document
        fig, ax = plt.subplots(figsize=(5, 3))
        chunks = [stats["chunks"] for stats in file_stats.values()]
        bars = sns.barplot(x=list(file_stats.keys()), y=chunks, ax=ax)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Chunks")
        plt.title("Document Sections")
        plt.tight_layout()
        
        # Add value labels to bars
        for bar in bars.patches:
            bars.text(
                bar.get_x() + bar.get_width()/2.,
                bar.get_height(),
                f'{int(bar.get_height())}',
                ha="center", va="bottom"
            )
            
        st.pyplot(fig)

# User query or analysis mode prompt with improved UI
st.markdown('<div class="subheader">🤔 Ask Questions or Choose Analysis Mode</div>', unsafe_allow_html=True)

if analysis_mode == "Q&A":
    query = st.text_input("Ask a question about the documents:", placeholder="E.g., What are the main topics discussed?")
elif analysis_mode == "Summary":
    query = "Generate a comprehensive summary of these documents."
    st.info("The AI will create a detailed summary of all uploaded documents.")
elif analysis_mode == "Key Points":
    query = "Extract and organize the key points from these documents."
    st.info("The AI will identify and list the most important points from the documents.")
elif analysis_mode == "Comparison":
    query = "Compare and contrast the main ideas and information across these documents."
    st.info("The AI will analyze similarities and differences across all documents.")

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

# Generate response with improved UI
if st.button("Generate Response", key="generate_response", help="Click to analyze documents and generate a response"):
    if query and corpus_chunks and api_key:
        st.markdown('<div class="spinner-message">🔍 Analyzing documents and generating a detailed response...</div>', unsafe_allow_html=True)
        with st.spinner(""):
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
            
            st.markdown('<div class="subheader">💡 AI Response</div>', unsafe_allow_html=True)
            st.markdown('<div class="response-container">', unsafe_allow_html=True)
            st.write(response)
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 6])
            with col1:
                st.download_button(
                    label="📥 Download",
                    data=response_download,
                    file_name=f"ai_docs_response_{time.strftime('%Y%m%d-%H%M%S')}.txt",
                    mime="text/plain"
                )
    elif not api_key:
        st.error("Please enter your API key in the sidebar.")
    elif not corpus_chunks:
        st.warning("Please upload at least one document.")
    elif not query:
        st.warning("Please enter a question or select an analysis mode.")
        
# Add app footer
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; color: #6B7280; font-size: 0.8rem;">
    Document Chat AI • Powered by Gemini AI
</div>
""", unsafe_allow_html=True)
