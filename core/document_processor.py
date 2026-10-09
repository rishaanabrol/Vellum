import re
import hashlib
import logging
from collections import Counter
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF
from config import settings

logger = logging.getLogger(__name__)

class ProcessedPage:
    def __init__(self, page_number: int, text: str, is_scanned: bool = False):
        self.page_number = page_number
        self.text = text
        self.is_scanned = is_scanned

class DocumentProcessor:
    """
    Handles PDF and TXT file extraction, page preservation, whitespace normalization,
    header/footer noise filtering, line-break hyphenation repair, and scanned page detection.
    """

    @staticmethod
    def compute_sha256(file_bytes: bytes) -> str:
        """Compute SHA-256 hash of raw file bytes for immutable content-based deduplication."""
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        return hasher.hexdigest()

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Normalize whitespace, fix broken hyphenated words at line breaks,
        and remove non-printable control characters while preserving math/symbols.
        """
        if not text:
            return ""

        # Repair hyphenation at line breaks: e.g. "compu-\ntation" -> "computation"
        text = re.sub(r'(\b\w+)-\n\s*(\w+\b)', r'\1\2', text)

        # Replace carriage returns and weird unicode line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Replace multiple horizontal spaces/tabs with a single space
        text = re.sub(r'[ \t]+', ' ', text)

        # Collapse excessive newlines (more than 2) into 2 newlines (paragraph boundary)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    @classmethod
    def _strip_repeated_headers_footers(cls, pages: List[ProcessedPage]) -> List[ProcessedPage]:
        """Drop first/last lines that repeat across most pages (running headers/footers)."""
        if len(pages) < 3:
            return pages

        first_lines: List[str] = []
        last_lines: List[str] = []
        for page in pages:
            lines = [ln.strip() for ln in page.text.splitlines() if ln.strip()]
            if not lines:
                continue
            first_lines.append(lines[0])
            last_lines.append(lines[-1])

        def repeated(seq: List[str]) -> str:
            if len(seq) < 3:
                return ""
            line, count = Counter(seq).most_common(1)[0]
            if count >= max(3, int(0.6 * len(seq))) and 3 <= len(line) < 90:
                return line
            return ""

        header = repeated(first_lines)
        footer = repeated(last_lines)
        if not header and not footer:
            return pages

        cleaned_pages: List[ProcessedPage] = []
        for page in pages:
            kept = []
            for ln in page.text.splitlines():
                stripped = ln.strip()
                if header and stripped == header:
                    continue
                if footer and stripped == footer:
                    continue
                kept.append(ln)
            cleaned_pages.append(ProcessedPage(
                page_number=page.page_number,
                text=cls.clean_text("\n".join(kept)),
                is_scanned=page.is_scanned,
            ))
        return cleaned_pages

    @staticmethod
    def _words_to_text(words) -> str:
        """Rebuild page text from PyMuPDF word boxes so math PDFs keep reading order."""
        if not words:
            return ""
        lines: dict = {}
        for item in words:
            if len(item) < 8:
                continue
            x0, _y0, _x1, _y1, token, block_no, line_no, _word_no = item[:8]
            key = (int(block_no), int(line_no))
            lines.setdefault(key, []).append((float(x0), str(token)))
        assembled: List[str] = []
        last_block = None
        for key in sorted(lines.keys()):
            block_no = key[0]
            if last_block is not None and block_no != last_block:
                assembled.append("")
            tokens = [tok for _x, tok in sorted(lines[key], key=lambda t: t[0])]
            assembled.append(" ".join(tokens))
            last_block = block_no
        return "\n".join(assembled)

    @staticmethod
    def _join_glyph_runs(text: str) -> str:
        """If a page is mostly 1–2 character lines (common in math PDFs), rejoin them."""
        lines = text.splitlines()
        nonempty = [ln for ln in lines if ln.strip()]
        if not nonempty:
            return text
        short = sum(1 for ln in nonempty if len(ln.strip()) <= 2)
        if short / len(nonempty) < 0.40:
            return text

        rebuilt: List[str] = []
        buf: List[str] = []

        def flush():
            if not buf:
                return
            token = "".join(buf)
            rebuilt.append(token)
            buf.clear()

        for line in lines:
            raw = line.rstrip()
            s = raw.strip()
            if not s:
                flush()
                rebuilt.append("")
                continue
            if len(s) <= 2:
                buf.append(s)
            else:
                flush()
                rebuilt.append(s)
        flush()
        return "\n".join(rebuilt)

    @classmethod
    def extract_pdf_page_text(cls, page) -> str:
        """
        Prefer the extraction that yields the most real words.
        `sort=True` fixes some reading-order issues; dict/span joining keeps
        in-line math fragments together.
        """
        candidates: List[str] = []
        try:
            words = page.get_text("words") or []
            reconstructed = cls._words_to_text(words)
            if reconstructed.strip():
                candidates.append(reconstructed)
        except Exception as e:
            logger.debug("PDF words extract failed: %s", e)
        try:
            candidates.append(page.get_text("text", sort=True) or "")
        except Exception as e:
            logger.debug("PDF sort text extract failed: %s", e)
        try:
            candidates.append(page.get_text("text") or "")
        except Exception as e:
            logger.debug("PDF text extract failed: %s", e)
        try:
            data = page.get_text("dict", sort=True)
            assembled: List[str] = []
            for block in data.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                    assembled.append(line_text)
                assembled.append("")
            candidates.append("\n".join(assembled))
        except Exception as e:
            logger.debug("PDF dict extract failed: %s", e)

        def word_score(blob: str) -> Tuple[int, int]:
            words = re.findall(r"[A-Za-z]{3,}", blob)
            return (len(words), len(blob))

        best = max(candidates, key=word_score) if candidates else ""
        return cls._join_glyph_runs(best)

    @classmethod
    def process_pdf(cls, file_bytes: bytes, filename: str) -> Tuple[List[ProcessedPage], List[int]]:
        """
        Extracts PDF text page by page.
        Returns:
            processed_pages: List of ProcessedPage objects with valid readable text
            scanned_pages: List of 1-indexed page numbers detected as scanned/unreadable
        """
        processed_pages: List[ProcessedPage] = []
        scanned_pages: List[int] = []

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Corrupt or unreadable PDF document '{filename}': {str(e)}")

        if len(doc) == 0:
            raise ValueError(f"PDF document '{filename}' contains 0 pages.")

        for idx, page in enumerate(doc):
            page_num = idx + 1
            raw_text = cls.extract_pdf_page_text(page)
            cleaned = cls.clean_text(raw_text)

            # Scanned detection heuristic:
            # If cleaned text has fewer than 40 characters or fewer than 10 alphabetic letters,
            # but page has drawing or image objects, it is likely scanned.
            alpha_count = sum(1 for c in cleaned if c.isalpha())
            is_scanned = (len(cleaned) < 40) or (alpha_count < 15)

            if is_scanned:
                scanned_pages.append(page_num)
            else:
                processed_pages.append(ProcessedPage(page_number=page_num, text=cleaned, is_scanned=False))

        doc.close()
        processed_pages = cls._strip_repeated_headers_footers(processed_pages)
        return processed_pages, scanned_pages

    @classmethod
    def process_txt(cls, file_bytes: bytes, filename: str) -> Tuple[List[ProcessedPage], List[int]]:
        """
        Processes TXT files with safe UTF-8 decoding and fallback encodings.
        TXT files are treated as a single page (Page 1) or split logically by page breaks.
        """
        decoded_text = ""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        success = False

        for enc in encodings:
            try:
                decoded_text = file_bytes.decode(enc)
                success = True
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if not success:
            decoded_text = file_bytes.decode('utf-8', errors='replace')

        cleaned = cls.clean_text(decoded_text)
        if not cleaned:
            raise ValueError(f"Text file '{filename}' is empty or contains only whitespace.")

        # Check for explicit form feed page breaks '\x0c'
        raw_pages = cleaned.split('\x0c')
        processed_pages = []
        for idx, p in enumerate(raw_pages):
            p_clean = p.strip()
            if p_clean:
                processed_pages.append(ProcessedPage(page_number=idx + 1, text=p_clean, is_scanned=False))

        if not processed_pages:
            processed_pages.append(ProcessedPage(page_number=1, text=cleaned, is_scanned=False))

        return processed_pages, []

    @classmethod
    def process_file(cls, file_bytes: bytes, filename: str) -> Tuple[str, List[ProcessedPage], List[int]]:
        """
        Dispatches to appropriate extractor based on extension and returns (doc_id, pages, scanned_pages).
        """
        if not file_bytes:
            raise ValueError(f"File '{filename}' is empty.")
        if len(file_bytes) > settings.MAX_UPLOAD_BYTES:
            raise ValueError(
                f"'{filename}' exceeds the {settings.MAX_UPLOAD_MB} MB upload limit."
            )

        doc_id = cls.compute_sha256(file_bytes)
        ext = Path(filename).suffix.lower()

        if ext == '.pdf':
            pages, scanned = cls.process_pdf(file_bytes, filename)
        elif ext in ['.txt', '.md']:
            pages, scanned = cls.process_txt(file_bytes, filename)
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Only .pdf and .txt files are supported.")

        return doc_id, pages, scanned
