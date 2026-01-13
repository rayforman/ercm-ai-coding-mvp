import os
import time
from dotenv import load_dotenv
import pandas as pd
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Finds .env file in the root and loads OpenAI API Key
load_dotenv()

def initialize_vector_store():
    """
    Builds a persistent Chroma DB from g_codes.csv.
    Organizes codes into clusters for hierarchical retrieval.
    """
    csv_path = "data/g_codes.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    print(f"--- Loading data from {csv_path} ---")
    df = pd.read_csv(csv_path)
    print(f"Successfully loaded {len(df)} rows.")
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    persist_dir = "data/chroma_db"
    
    # 1. Prepare Individual Codes
    print("Preparing individual code documents...")
    code_docs = []
    for _, row in df.iterrows():
        code = str(row['icd_code'])
        cluster_id = code[:3]
        doc = Document(
            page_content=row['long_description'],
            metadata={"code": code, "cluster_id": cluster_id, "type": "specific_code"}
        )
        code_docs.append(doc)
    print(f"Created {len(code_docs)} specific code documents.")

    # 2. Prepare Cluster Headers
    print("Generating cluster headers...")
    manual_headers = {"G00": "Bacterial meningitis, not elsewhere classified"}
    
    # Group by a calculated series and name it 'cluster_id' to avoid naming conflicts
    cluster_summaries = df.groupby(df['icd_code'].str[:3]).first()
    cluster_summaries.index.name = 'cluster_id'
    cluster_summaries = cluster_summaries.reset_index()
    
    cluster_docs = []
    for _, row in cluster_summaries.iterrows():
        # Using the now-clean 'cluster_id' column
        cluster_id = row['cluster_id']
        description = manual_headers.get(cluster_id, row['long_description'])
        doc = Document(
            page_content=f"Category {cluster_id}: {description}",
            metadata={"cluster_id": cluster_id, "type": "cluster_header"}
        )
        cluster_docs.append(doc)
    print(f"Created {len(cluster_docs)} cluster header documents.")

    all_docs = code_docs + cluster_docs
    total_docs = len(all_docs)
    print(f"\n--- Starting ingestion for {total_docs} total documents ---")

    # 3. Initialize and Persist in BATCHES
    batch_size = 100
    start_time = time.time()
    
    # Create the initial collection with the first batch
    print(f"Initializing ChromaDB with first batch (0-{batch_size})...")
    vector_db = Chroma.from_documents(
        documents=all_docs[:batch_size],
        embedding=embeddings,
        persist_directory=persist_dir
    )

    # Add remaining batches
    for i in range(batch_size, total_docs, batch_size):
        batch = all_docs[i : i + batch_size]
        vector_db.add_documents(batch)
        
        # Calculate progress percentage
        current_count = min(i + batch_size, total_docs)
        percent = (current_count / total_docs) * 100
        print(f"Progress: {current_count}/{total_docs} ({percent:.1f}%) ingested...")

    end_time = time.time()
    duration = end_time - start_time
    
    print("-" * 30)
    print(f"Done! Vector store is saved in {persist_dir}")
    print(f"Total time elapsed: {duration:.2f} seconds")
    print("-" * 30)
    
    return vector_db

def main():
    print("Main")
    main_start = time.time()
    initialize_vector_store()
    print(f"Script finished in {time.time() - main_start:.2f} seconds.")

if __name__ == "__main__":
    main()