# AI Medical Coding MVP - Earnest RCM

## Overview

This repository contains a Minimum Viable Product (MVP) for an automated medical coding service. The system processes raw medical charts, organizes them into a relational database, and utilizes a two-layer Retrieval-Augmented Generation (RAG) pipeline to ascribe ICD-10 (Category G) diagnosis codes with high precision.

## System Architecture

The application consists of three primary components:

1.  **Django API**: Manages the ingestion and storage of medical charts and notes using a SQLite backend.
2.  **AI Coding Service**: A hierarchical semantic search engine built with **LangChain** and **Chroma DB**.
3.  **Validation Suite**: A comprehensive Python script to test API integrity and coding accuracy.

---

## Design Choices

### 1. Relational Schema (SQLite)

I implemented a hierarchical schema in `models.py` consisting of four models:

- **MedicalChart**: Stores visit-level metadata and a unique external ID.
- **Note**: Stores individual clinical sections (HPI, ROS, Exam) linked via ForeignKey to the parent chart.
- **ICD10Code**: Stores the standardized codes and descriptions used as the "ground truth" for coding.
- **CodeAssignment**: A join table that links Notes to ICD10Codes, storing the `similarity_score` and `assigned_at` timestamp for auditability.

**Justification:** This normalized structure mirrors the reality of clinical workflows. By deconstructing a chart into a one-note-per-row schema, we prevent "semantic dilution"—the loss of specific diagnostic details that occurs when embedding large, multi-topic text blobs. This granularity ensures that a single specific finding (like a neurological exam result) has its own distinct vector, leading to significantly higher precision during the RAG process. It also creates a clear audit trail, allowing reviewers to verify exactly which clinical observation justified a specific code.

### 2. Two-Layer Semantic Search (RAG)

To maximize accuracy and handle clinical nuance, the system employs a two-layer search using OpenAI's `text-embedding-3-large`:

- **Layer 1 (Cluster Mapping)**: The note is compared against high-level category clusters to identify the clinical "neighborhood" (e.g., G40 for Epilepsy).
- **Layer 2 (Granular Search)**: A second cosine similarity search is performed strictly _within_ that identified cluster to find the most specific code ($k=1$).

**Justification:** This hierarchical approach significantly reduces "semantic noise" and the risk of hallucinations. In a flat search space of 2,000+ codes, a note mentioning "headaches" might accidentally pull a code from the Inflammatory Diseases or Vascular Syndromes blocks due to overlapping terminology. By first anchoring the search in a clinically coherent 3-character "neighborhood," we effectively prune irrelevant branches of the ICD-10 tree. This ensures the final $k=1$ retrieval is limited to the most clinically appropriate candidates, ensuring both high precision and auditability.

---

## Clustering Methodology

### The 3-Character "Sweet Spot"

Through researching and examining the csv, I noticed each additional character in the ICD-10 code indicated additional specificity. After iterative testing, I identified that the **3-character ICD-10 prefix** is the most effective grouping:

- **2-Character**: Too broad; considerably different conditions were mixed together.
- **Official Blocks (e.g., G00-G09)**: Often too diverse for precise targeting.
- **✓ 3-Character (e.g., G40, G43)**: Balanced category sizes with clinically coherent groupings (e.g., G43 always equals Migraines).
- **4+ Characters**: Too granular; created hundreds of tiny categories, resulting in "lost-in-the-middle" retrieval issues and fragmented semantic clusters.

### Category Title Discovery & Manual Overrides

The system identifies cluster headers by grouping the ICD-10 dataset by the 3-character prefix and selecting the first available description for that group. Examining the csv, I noticed that the first row of a each section made for a good category heading, almost certainly by design. With the exception of the first section, which appears to have been cut off.

- **Manual Injection**: The `G00` (Bacterial Meningitis) section was missing its primary header row in the raw data. I added a manual override in the ingestion script to ensure Layer 1 search integrity for this category. In the event of additional gaps, additional manual headers can be added.

---

## Setup and Usage

1.  **Sync Environment**: `uv sync`
2.  **Configure Environment Variables**:
    - Locate the `.env.example` file in the root directory.
    - Duplicate it and rename the copy to `.env`.
    - Open `.env` and add your valid `OPENAI_API_KEY`.
3.  **Initialize Database**: `python manage.py migrate`
4.  **Build Vector Store**:
    - I created a custom service in `ai_coding_app/app/vector_service.py`.
    - Run: `python ai_coding_app/app/vector_service.py`
    - This parses the CSV, applies 3-character clustering, and persists the **Chroma DB** locally using OpenAI embeddings.
5.  **Run Server**: `task run-local`
6.  **Execute Tests**: `task test-api`

---

## API Endpoints Summary

### Ingestion

- `GET /app/chart-schema`: Returns the DB structure.
- `POST /app/upload-chart`: Idempotently uploads a chart to SQLite.
- `GET /app/charts`: Lists all stored charts.

### Coding

- `POST /app/code-chart`: Performs hierarchical semantic search.
  - **Input:** `{"external_chart_id": "case12", "save": true}`
  - **Output:** A list of `note_id`, `icd_code`, and `similarity_score`.

---

## Future Production Considerations

### Selective Coding

In this MVP, an ICD-10 code is ascribed to every note to maintain a strict 1:1 mapping for verification and evaluation. In a production environment, non-clinical sections (e.g., `METADATA`, `CHART_INFO`, administrative headers) would be explicitly filtered out prior to semantic processing, as code assignments for these sections are not clinically meaningful.

### Confidence Scoring

In a production system, a confidence-based gating mechanism would be introduced. Only code assignments exceeding a predefined similarity threshold would be automatically accepted. Low-confidence matches would be flagged for manual human review, enabling a human-in-the-loop workflow that balances automation with clinical accuracy and auditability.
