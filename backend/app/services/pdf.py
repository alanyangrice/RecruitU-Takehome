from io import BytesIO
from PyPDF2 import PdfReader


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    buffer = BytesIO(pdf_bytes)
    reader = PdfReader(buffer)
    texts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        texts.append(page_text)
    return "\n".join(texts).strip()
