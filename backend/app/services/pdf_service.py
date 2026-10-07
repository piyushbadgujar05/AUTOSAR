import pymupdf as fitz
import re
from typing import List, Dict, Any, Tuple
from backend.app.core.logging import logger

class PDFService:
    @staticmethod
    def extract_text_and_sections(file_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extract text, detect headings and sections from a PDF file page by page using PyMuPDF.
        Returns:
            (pages_data, metadata)
        """
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            logger.error(f"Failed to open PDF {file_path}: {str(e)}")
            raise ValueError(f"Unable to read PDF file: {str(e)}")

        if len(doc) == 0:
            doc.close()
            raise ValueError("The provided PDF is completely empty (0 pages).")

        metadata = {
            "title": doc.metadata.get("title") or "",
            "author": doc.metadata.get("author") or "",
            "subject": doc.metadata.get("subject") or "",
            "page_count": len(doc)
        }

        pages_data = []
        current_section = "General / Introduction"
        total_text_length = 0

        # Regex heuristics for automotive HLD section headers
        heading_patterns = [
            r"^(?:\d+\.?\s+)+([A-Z][A-Za-z0-9\s\-_/]+)",  # "1.0 Architecture Overview", "2.1 Software Components"
            r"^(?:SECTION|CHAPTER)\s+\d+[:\-]?\s*(.+)",
            r"^([A-Z][A-Z0-9\s\-_/]{4,})$"  # "COMPONENT SPECIFICATION"
        ]

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc[page_idx]
            
            # Extract plain text
            text = page.get_text("text").strip()
            total_text_length += len(text)

            # Detect headings from text blocks
            blocks = page.get_text("blocks")
            for block in blocks:
                block_text = block[4].strip()
                lines = block_text.splitlines()
                if lines:
                    first_line = lines[0].strip()
                    for pattern in heading_patterns:
                        match = re.search(pattern, first_line, re.IGNORECASE)
                        if match and len(first_line) < 80:
                            current_section = first_line
                            break

            pages_data.append({
                "page_number": page_num,
                "section": current_section,
                "content": text
            })

        if total_text_length < 50:
            logger.warning(f"Low extractable text ({total_text_length} chars) detected for {file_path}. Checking for scanned PDF / OCR fallback...")
            ocr_text_found = False
            # Attempt OCR with PyMuPDF OCR or pytesseract if available
            try:
                # Try PyMuPDF built-in OCR if Tesseract library is installed in environment
                for page_idx in range(len(doc)):
                    page = doc[page_idx]
                    try:
                        tp = page.get_textpage_ocr(language="eng", dpi=150)
                        ocr_txt = page.get_text("text", textpage=tp).strip()
                        if len(ocr_txt) > 20:
                            pages_data[page_idx]["content"] = ocr_txt
                            ocr_text_found = True
                    except Exception:
                        pass
            except Exception as ocr_err:
                logger.info(f"PyMuPDF OCR unavailable: {ocr_err}")

            if not ocr_text_found:
                try:
                    import pytesseract
                    from PIL import Image
                    import io
                    for page_idx in range(len(doc)):
                        page = doc[page_idx]
                        pix = page.get_pixmap()
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        ocr_txt = pytesseract.image_to_string(img).strip()
                        if len(ocr_txt) > 20:
                            pages_data[page_idx]["content"] = ocr_txt
                            ocr_text_found = True
                except Exception as pytess_err:
                    logger.info(f"pytesseract fallback unavailable: {pytess_err}")

            if not ocr_text_found:
                doc.close()
                raise ValueError(
                    "This document appears to be scanned. OCR dependency is not configured. "
                    "To enable OCR: install tesseract-ocr on your operating system and install pytesseract."
                )

        doc.close()
        return pages_data, metadata
