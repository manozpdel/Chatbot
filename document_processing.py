
#Importing the dependencies
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Split text into smaller chunks
from langchain.schema import Document                               # Define a schema for documents
from langchain_ollama import OllamaLLM, OllamaEmbeddings            # Importing Ollama LLM and embedding classes for language model operations
from langchain_chroma import Chroma                                 # Importing Chroma for vector storage and retrieval
from langchain_community.document_loaders import PyPDFDirectoryLoader  # Importing PDF loader to extract documents from a directory containing PDFs
import streamlit as st                                              # Importing streamlit for UI

# Constants for paths used in the application
CHROMA_PATH = "chroma"  # Path for Chroma vector store
DATA_PATH = "bigdata"   # Path for the PDF document directory

# Embedding function to retrieve embeddings from Ollama
def get_embedding_function():
    # Initialize OllamaEmbeddings with a specified model
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings

# Helper function to process documents (load, split, and store)
def process_documents():
    # Load documents, split them into chunks, and add them to Chroma vector store
    documents = load_documents()  # Load the documents
    chunks = split_documents(documents)  # Split the documents into smaller chunks
    add_to_chroma(chunks)  # Add the processed chunks to Chroma

# Function to load documents from a specified directory
def load_documents():
    document_loader = PyPDFDirectoryLoader(DATA_PATH)  # Initialize PDF loader
    return document_loader.load()  # Load documents from the directory

# Function to split documents into smaller chunks for easier processing
def split_documents(documents: list[Document]):
    # Initialize text splitter with defined chunk size and overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Max size of each chunk
        chunk_overlap=80,  # Overlap between consecutive chunks
        length_function=len,  # Function to calculate chunk length
    )
    return text_splitter.split_documents(documents)  # Split documents into chunks

# Function to add processed chunks to Chroma vector store
def add_to_chroma(chunks: list[Document]):
    # Initialize Chroma database with embedding function
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )

    # Calculate chunk IDs and filter out already existing chunks in the database
    chunks_with_ids = calculate_chunk_ids(chunks)  # Assign IDs to chunks
    existing_items = db.get(include=[])  # Retrieve existing items in the database
    existing_ids = set(existing_items["ids"])  # Set of existing document IDs
    st.write(f"Number of existing documents in DB: {len(existing_ids)}")  # Display number of existing documents

    # Filter out chunks that already exist in the database
    new_chunks = [chunk for chunk in chunks_with_ids if chunk.metadata["id"] not in existing_ids]

    # Add new chunks to the database if any
    if new_chunks:
        st.write(f"Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]  # List of new chunk IDs
        db.add_documents(new_chunks, ids=new_chunk_ids)  # Add new chunks to Chroma
        db.persist()  # Persist changes to the database
    else:
        st.write("No new documents to add")  # No new documents to add

# Function to calculate unique IDs for each chunk based on its source and page
def calculate_chunk_ids(chunks: list[Document]):
    last_page_id = None  # Keep track of the last processed page
    current_chunk_index = 0  # Initialize the index for the current chunk

    # Iterate over each chunk and assign a unique ID
    for chunk in chunks:
        source = chunk.metadata.get("source")  # Get the source of the document
        page = chunk.metadata.get("page")  # Get the page number
        current_page_id = f"{source}:{page}"  # Generate a unique page ID

        # If the page ID is the same as the last one, increment the chunk index
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0  # Reset the chunk index for a new page

        # Generate a unique chunk ID based on the page and chunk index
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id  # Update the last page ID

        # Assign the calculated ID to the chunk metadata
        chunk.metadata["id"] = chunk_id

    return chunks  # Return the chunks with the assigned IDs
