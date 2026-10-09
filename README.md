# Vellum

<p align="center">
  <em>A Source-Grounded Document Knowledge Assistant & Editorial Studio</em>
  <br />
  <strong>"Don't just answer the student. Show them where the answer came from."</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Streamlit-1.65%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/Google%20Gemini-Flash%20%26%20Embedding-4285F4?style=flat-square&logo=google&logoColor=white" alt="Google Gemini" />
  <img src="https://img.shields.io/badge/ChromaDB-Vector%20Store-orange?style=flat-square" alt="ChromaDB" />
  <img src="https://img.shields.io/badge/Tests-43%20passed-success?style=flat-square" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="MIT License" />
</p>

---

## Overview

**Vellum** is an editorial, print-monograph inspired academic document intelligence workspace. Students and researchers upload their own PDF/TXT course materials, ask natural-language questions, and receive rigorous, grounded answers accompanied by verifiable document citations and visual page evidence.

---

## System Architecture

```text
  [PDF / TXT Course Materials]
               │
               ▼
   core/document_processor.py   ──► Page-aware extraction, noise/hyphenation cleanup, scanned page detection
               │
               ▼
   core/chunker.py              ──► Paragraph-aware chunking with overlap & page provenance
               │
               ▼
   core/embeddings.py           ──► gemini-embedding-001 (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY)
               │
               ▼
   core/vector_store.py         ──► ChromaDB persistent vector database with SHA-256 deduplication
               ▲
               │ (Vector Similarity Search)
               │
   core/retriever.py            ──► Top-K candidate extraction, hybrid lexical boost, MIN_RELEVANCE filtering
               ▲
               │
   core/llm.py (Rewriter)       ──► Conversational follow-up rewriting
               ▲
               │
        [User Question]
```

### RAG Flow & Explainability
1. **Document Processing & Scanned Detection:** PDFs are extracted page-by-page using PyMuPDF (`pymupdf`), preserving exact page coordinates and detecting scanned or unreadable pages (< 40 characters or low alphabetic density) with clear warnings.
2. **Chunking & Provenance:** Rather than arbitrary character slicing, the chunker prioritizes natural paragraph boundaries (`\n\n`), retaining rich metadata (`document_id`, `document_name`, `chunk_id`, `page_number`).
3. **Embeddings:** Vectorized using Google's `gemini-embedding-001` with explicit task types:
   - `task_type="RETRIEVAL_DOCUMENT"` for indexing chunk passages.
   - `task_type="RETRIEVAL_QUERY"` for semantic question searching.
4. **Vector Store:** ChromaDB persistent storage at `./storage/chroma` with cosine distance indexing and true vector deletion.
5. **Deterministic Refusal:** If retrieved candidates fail to pass `MIN_RELEVANCE`, the LLM call is bypassed entirely, returning a fixed refusal message:
   > *"I couldn't find enough information in your uploaded documents to answer this question."*
6. **Grounding & Citation Validation:** System prompts treat document text as untrusted material (defending against prompt injection). Post-processing code validates every `[n]` citation marker and strips any hallucinated citations.
7. **Visual Page Verification:** The Evidence panel allows the student to render the exact underlying PDF page as a high-resolution image using PyMuPDF's `page.get_pixmap()`.

---

## Key Features

- **Editorial 3-Column Workspace:** Clean desktop layout featuring **Knowledge Base** on the left, **Discussion** conversation in the center, and **Evidence** verification on the right.
- **Interactive Landing Cover:** Immersive paper-textured aesthetic with dynamic 3D leaf tilt physics and elegant typography.
- **State-Morphing Telemetry:** Uploaded files morph through *Reading → Splitting → Indexing → Ready* with real-time status reporting.
- **Context-Aware Query Rewriting:** Conversational follow-ups (e.g., *"Explain it in simpler terms"*) are rewritten into standalone search queries while preserving chat history.
- **Document Insights:** Automatic 2–3 line summary and 3 clickable starter study questions for every uploaded document.
- **Scope Control:** Query across *"All documents"* or scope search to specific selected documents.
- **Notes Export:** Download entire discussions with citations as formatted Markdown study notes.
- **LaTeX & KaTeX Support:** Native mathematical typesetting for formulas and academic notation.

---

## Directory Structure

```text
Vellum/
├── core/                       # Core RAG engine & processing
│   ├── api_errors.py           # User-facing error formatting
│   ├── chunker.py              # Paragraph-aware text chunking
│   ├── document_processor.py   # PDF & text extraction, scanned page checks
│   ├── embeddings.py           # Gemini embedding client with mock fallback
│   ├── hybrid.py               # Lexical + dense hybrid scoring
│   ├── ingest.py               # Ingestion orchestrator & deduplication
│   ├── llm.py                  # Gemini LLM streaming & query rewriting
│   ├── models.py               # Domain schemas & dataclasses
│   ├── page_renderer.py        # PDF page rasterizer for visual proof
│   ├── rag.py                  # End-to-end RAG pipeline
│   ├── retriever.py            # Candidate search & relevance filtering
│   └── vector_store.py         # ChromaDB persistence interface
├── ui/                         # Streamlit user interface
│   ├── chat.py                 # Chat timeline & citation chips
│   ├── components.py           # Empty states & reusable widgets
│   ├── cover.py                # Landing cover page & interactions
│   ├── sidebar.py              # Knowledge base, scope & document list
│   ├── sources.py              # Evidence panel & snippet highlights
│   └── styles.py               # Parchment design tokens & CSS
├── eval/                       # Evaluation harness & benchmarks
│   ├── eval_report.json        # Evaluation output
│   ├── questions.json          # Benchmark evaluation questions
│   └── run_eval.py             # Evaluation runner script
├── sample_documents/           # Sample physics & lab course material
│   ├── generate_samples.py     # Script to generate mock PDF fixtures
│   ├── Lab_Safety_Protocol.txt
│   ├── Physics_Module_1.pdf
│   └── Physics_Module_2.pdf
├── static/                     # Static assets & specimens
│   └── specimens/              # Typographic specimens
├── tests/                      # Automated test suite (43 unit & integration tests)
├── .env.example                # Template environment variables
├── .gitignore                  # Git ignore rules
├── app.py                      # Main Streamlit application entrypoint
├── config.py                   # Pydantic application settings
├── LICENSE                     # MIT License
├── preseed.py                  # Pre-seed utility for demo documents
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Pinned Python package dependencies
└── smoke_rag.py                # Standalone smoke test utility
```

---

## Benchmark Evaluation Results

Running `python eval/run_eval.py` indexes sample documents into an isolated test store, evaluates all 15 benchmark questions in `eval/questions.json`, and records performance:

| Metric | Result | Target | Status |
| :--- | :---: | :---: | :---: |
| **Top-5 Retrieval Hit Rate** | **100.0% (12/12)** | > 85% | PASS |
| **Out-of-Domain Refusal Accuracy** | **100.0% (3/3)** | 100% | PASS |
| **Citation Hallucination Rate** | **0.0% (all validated)** | 0% | PASS |
| **Prompt Injection Resistance** | **Defended** | 100% | PASS |

**Threshold Design (`MIN_RELEVANCE = 0.65`):**
```text
on-topic expected chunks   0.738 – 0.932   (worst-case on-topic = 0.738)
off-topic best chunk       0.527           (worst-case off-topic = 0.527)
→ threshold 0.65 cleanly clears off-topic queries by 0.12 margin
```

---

## Getting Started

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Google Gemini API key ([Google AI Studio](https://aistudio.google.com/))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rishaanabrol/Vellum.git
   cd Vellum
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your `GEMINI_API_KEY`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   LLM_MODEL=gemini-2.5-flash
   EMBEDDING_MODEL=gemini-embedding-001
   ```

5. **(Optional) Pre-seed sample documents:**
   ```bash
   python preseed.py
   ```

6. **Launch the application:**
   ```bash
   streamlit run app.py
   ```

The application will open at `http://localhost:8501`.

---

## Testing & Quality Assurance

Run the comprehensive test suite:
```bash
python -m pytest -v
```

Execute headless smoke testing against vector search:
```bash
python smoke_rag.py
```

Run retrieval evaluation benchmarks:
```bash
python eval/run_eval.py
```

---

## License

This project is licensed under the terms of the [MIT License](LICENSE).
