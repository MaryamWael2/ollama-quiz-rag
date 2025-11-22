# -*- coding: utf-8 -*-
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings

def prep_documents(file_paths):
    all_chunks = []

    for file_path in file_paths:
        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4096,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )

        chunks = text_splitter.split_documents(pages)
        all_chunks.extend(chunks)

    embedding = FastEmbedEmbeddings()
    Chroma.from_documents(
        documents=all_chunks,
        embedding=embedding,
        persist_directory="./sql_chroma_db"
    )
