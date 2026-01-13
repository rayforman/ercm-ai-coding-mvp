import pandas as pd
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os

def initialize_vector_store():
    """
    Builds a persistent Chroma DB from g_codes.csv.
    Organizes codes into clusters for hierarchical retrieval, 
    with a manual injection for the missing G00 header.
    """
    csv_path = "data/g_codes.csv"
    df = pd.read_csv(csv_path)
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    persist_dir = "data/chroma_db"
    
    # 1. Individual Codes for "Codes Collection"
    code_docs = []
    for _, row in df.iterrows():
        code = str(row['icd_code'])
        cluster_id = code[:3]
        
        doc = Document(
            page_content=row['long_description'],
            metadata={
                "code": code,
                "cluster_id": cluster_id,
                "type": "specific_code"
            }
        )
        code_docs.append(doc)

    # 2. Cluster-Level Descriptions (The "Headers")
    # We use a dictionary for manual overrides where the CSV is missing a parent row
    manual_headers = {
        "G00": "Bacterial meningitis, not elsewhere classified", # first section is missing header, designed to scale
    }
    
    cluster_summaries = df.groupby(df['icd_code'].str[:3]).first().reset_index()
    cluster_docs = []
    
    for _, row in cluster_summaries.iterrows():
        cluster_id = row['icd_code'][:3]
        
        # Check if we have a manual override, otherwise use the first description found
        description = manual_headers.get(cluster_id, row['long_description'])
        
        doc = Document(
            page_content=f"Category {cluster_id}: {description}",
            metadata={
                "cluster_id": cluster_id,
                "type": "cluster_header"
            }
        )
        cluster_docs.append(doc)

    # 3. Initialize and Persist - Chroma does everything
    vector_db = Chroma.from_documents(
        documents=code_docs + cluster_docs,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    
    return vector_db