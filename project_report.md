# Project Report: Vellum — Source-Grounded Document Knowledge Assistant

---

### Student Details
- **Name:** Rishaan Abrol
- **Registration Number:** [Enter Your Registration Number Here]
- **Email ID:** rishaan.abrol15@gmail.com
- **Repository URL:** [https://github.com/rishaanabrol/Vellum](https://github.com/rishaanabrol/Vellum)

---

## 1. Problem Statement

Modern students and researchers increasingly rely on Generative AI and Large Language Models (LLMs) to understand dense academic materials, course handouts, problem sets, and textbooks. However, standard LLM chat interfaces suffer from three critical shortcomings:

1. **Hallucination & Lack of Verifiability:** General-purpose AI models routinely produce plausible-sounding but factually inaccurate statements without providing verifiable page-level evidence or provenance citations.
2. **Context Loss & Prompt Injection Vulnerability:** General models fail to isolate untrusted user documents from core instructions, making them prone to syllabus confusion or adversarial document injection.
3. **The Speculation Trap (Lack of Refusal Cutoff):** Standard chatbots almost never admit when an answer is absent from the provided course syllabus, opting instead to speculate from general pre-training data, leading students to memorize incorrect or off-syllabus information.

---

## 2. Why This Problem Statement Was Chosen

Education demands accountability: **"Don't just answer the student; show them exactly where the answer came from."**

1. **Academic Rigor:** In university coursework (such as physics, mathematics, and engineering), trusting an ungrounded AI summary can lead to academic errors. Students need to verify the exact page, formula, or problem statement directly from their instructor's provided material.
2. **Pedagogical Needs:** Students don't just need static summaries; they need interactive study aids—clickable starter questions, follow-up query rewriting, mathematical typesetting ($LaTeX$ equations), and visual proof of source pages.
3. **Closing the Trust Gap:** By pairing an editorial, print-monograph reading aesthetic with a deterministic Retrieval-Augmented Generation (RAG) architecture, **Vellum** transforms the reading and studying experience into an interactive dialogue backed by verifiable evidence.

---

## 3. Visual Interface & Screenshots

### Interactive Landing Experience
The entry point of Vellum provides a paper-crafted editorial aesthetic featuring interactive 3D leaf tilt physics and typographic elegance, greeting the student before entering the workspace:

![Vellum Landing Page Experience](C:/Users/Rishaan/.gemini/antigravity/brain/43b9cd10-bb62-4e4f-89ad-57dc69811c21/.user_uploaded/media_1791571862983_83385869.png)

---

### The 3-Column Document Intelligence Workspace
Upon entering the workspace, students are provided an organized desktop layout with distinct zones for document management, conversation, and visual evidence:

![Vellum 3-Column Knowledge Workspace](C:/Users/Rishaan/.gemini/antigravity/brain/43b9cd10-bb62-4e4f-89ad-57dc69811c21/.user_uploaded/media_1791571862998_e0ae6f5d.png)

- **Left (Knowledge Base):** Upload local lecture notes/PDFs with real-time state morphing (*Reading → Splitting → Indexing → Ready*), document summaries, and suggested questions.
- **Center (Discussion):** Grounded conversational timeline with inline citation chips `[1]`, `[2]`, step-by-step problem-solving, and native $LaTeX$ rendering.
- **Right (Evidence Panel):** Extracted snippets with highlighted key sentences and high-resolution visual PDF page rendering.

---

## 4. Approach / Proposed Solution

Vellum implements an end-to-end, production-grade **Retrieval-Augmented Generation (RAG)** pipeline designed around strict provenance and explainability:

```text
  [PDF / TXT Course Materials]
               │
               ▼
   core/document_processor.py   ──► Page-aware extraction, noise cleanup, scanned page detection
               │
               ▼
   core/chunker.py              ──► Paragraph-aware chunking with overlap & page provenance
               │
               ▼
   core/embeddings.py           ──► Google gemini-embedding-001 (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY)
               │
               ▼
   core/vector_store.py         ──► ChromaDB persistent vector database with SHA-256 deduplication
               ▲
               │ (Vector Similarity Search)
               │
   core/retriever.py            ──► Top-K candidate extraction, hybrid lexical boost, thresholding
               ▲
               │
   core/llm.py (Rewriter)       ──► Conversational follow-up rewriting (gemini-3.5-flash-lite)
               ▲
               │
        [User Question]
```

### Architectural Highlights:
1. **Page-Aware Processing:** PyMuPDF (`fitz`) extracts text page-by-page while tracking character counts to detect scanned/unreadable pages.
2. **Paragraph-Aware Chunking:** Text is split cleanly along natural paragraph boundaries (`\n\n`) rather than arbitrary character cuts, preserving full page provenance.
3. **Hybrid Retrieval:** Blends dense vector search with lexical BM25/keyword overlap. Conceptual queries (e.g. *theorems, formulas, problem sets*) preserve true semantic similarity, while unrelated off-topic queries are strictly rejected.
4. **Deterministic Refusal:** If retrieved candidates fail to pass the relevance threshold (`MIN_RELEVANCE = 0.65`), the LLM call is bypassed entirely, returning an honest refusal without wasting quota.
5. **Post-Processing Citation Validation:** Regex post-processors parse bracketed citations (`[1]`, `[2]`) in real-time, stripping any hallucinated citation references before displaying text to the student.
6. **Visual Proof Rendering:** Users can render and inspect the original rasterized PDF page image directly inside the Evidence panel.

---

## 5. Technologies & Tools Used

| Layer / Component | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Frontend & UI** | **Streamlit (v1.65+)** | Three-column desktop interface, reactive chat timeline, state management |
| **Typography & Styling** | **CSS3, HTML5, Cormorant Garamond, Manrope** | Print-monograph parchment styling, custom CSS bridge, flex layout |
| **Language Model** | **Google Gemini (`gemini-3.5-flash-lite`)** | High-throughput query rewriting, document insights, and grounded response generation |
| **Embedding Engine** | **Google `gemini-embedding-001`** | High-dimensional semantic text embeddings with task-specific modes |
| **Vector Database** | **ChromaDB** | Persistent vector index with cosine distance calculation, metadata filtering |
| **PDF Extraction & Rendering** | **PyMuPDF (`pymupdf` / `fitz`)** | Page-level text extraction, scanned page detection, and high-DPI page rendering |
| **Configuration & Secrets** | **Python-Dotenv & Streamlit Secrets** | Environment variable management supporting local `.env` and Streamlit Cloud Secrets |
| **Testing & Quality Assurance**| **PyTest** | Automated test suite comprising **43 unit and integration tests** |

---

## 6. Key Features & Functionalities

1. **Editorial Academic Workspace:** A unified 3-column layout keeping document library, discussion, and source proof visible simultaneously.
2. **State-Morphing Ingestion Telemetry:** Files dynamically transition through *Reading → Splitting → Indexing → Ready* with real-time feedback.
3. **Automated Document Insights:** On document ingestion, the system generates a concise 2–3 line summary and 3 clickable starter study questions.
4. **Context-Aware Query Rewriting:** Conversational follow-ups (e.g., *"Explain that formula in simpler terms"*) are rewritten into standalone search queries using past chat context.
5. **Step-by-Step Problem Solving:** Accurately extracts problem parameters, matrices, and variables to explain step-by-step mathematical procedures with $LaTeX$ formulas.
6. **Scope-Filtered Retrieval:** Search across all uploaded lecture notes or isolate queries to specific selected documents.
7. **Study Notes Export:** One-click download of the complete chat session and cited sources as formatted Markdown.
8. **Cloud-Ready & Secure:** Seamless deployment on Streamlit Community Cloud with encrypted secrets management and automated model fallbacks.
