import io
import fitz  # PyMuPDF
from typing import Optional

class PDFPageRenderer:
    """
    Renders verifiable PDF page images directly from uploaded byte streams.
    Returns PNG bytes so Streamlit can display them without Pillow.
    """

    @staticmethod
    def render_page_image(file_bytes: bytes, page_number: int, dpi: int = 150) -> Optional[bytes]:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            if page_number < 1 or page_number > len(doc):
                doc.close()
                return None

            page = doc[page_number - 1]
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            png_bytes = pix.tobytes("png")
            doc.close()
            return png_bytes
        except Exception as e:
            print(f"Error rendering PDF page {page_number}: {e}")
            return None
