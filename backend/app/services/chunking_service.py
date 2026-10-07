import re
from typing import List, Dict, Any
from backend.app.core.config import settings
from backend.app.core.logging import logger

class ChunkingService:
    @staticmethod
    def create_section_aware_chunks(
        document_id: str,
        document_name: str,
        version: str,
        pages_data: List[Dict[str, Any]],
        project: str = "ADAS Control System",
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Creates section-aware chunks while strictly preserving page numbers, section titles,
        and document metadata for accurate citations.
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        chunks = []

        chunk_counter = 0

        for page in pages_data:
            page_num = page["page_number"]
            section = page["section"]
            text = page["content"]

            if not text.strip():
                continue

            # Split text by paragraphs first
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

            current_chunk_text = ""

            for para in paragraphs:
                if len(current_chunk_text) + len(para) + 1 <= chunk_size:
                    if current_chunk_text:
                        current_chunk_text += "\n\n" + para
                    else:
                        current_chunk_text = para
                else:
                    if current_chunk_text:
                        chunk_counter += 1
                        chunk_id = f"{document_id}_p{page_num}_c{chunk_counter}"
                        chunks.append({
                            "chunk_id": chunk_id,
                            "document_id": document_id,
                            "document_name": document_name,
                            "project": project,
                            "version": version,
                            "page_number": page_num,
                            "section": section,
                            "content": current_chunk_text.strip()
                        })
                        # Retain overlap from end of previous chunk if possible
                        words = current_chunk_text.split()
                        overlap_words = words[-max(1, chunk_overlap // 6):] if len(words) > 10 else []
                        overlap_text = " ".join(overlap_words)
                        current_chunk_text = (overlap_text + "\n\n" + para).strip() if overlap_text else para
                    else:
                        # Paragraph itself exceeds chunk_size, split by sentences or slice
                        para_sentences = re.split(r'(?<=[.!?])\s+', para)
                        sub_chunk = ""
                        for sent in para_sentences:
                            if len(sub_chunk) + len(sent) + 1 <= chunk_size:
                                sub_chunk = (sub_chunk + " " + sent).strip()
                            else:
                                if sub_chunk:
                                    chunk_counter += 1
                                    chunk_id = f"{document_id}_p{page_num}_c{chunk_counter}"
                                    chunks.append({
                                        "chunk_id": chunk_id,
                                        "document_id": document_id,
                                        "document_name": document_name,
                                        "project": project,
                                        "version": version,
                                        "page_number": page_num,
                                        "section": section,
                                        "content": sub_chunk.strip()
                                    })
                                sub_chunk = sent
                        current_chunk_text = sub_chunk

            if current_chunk_text:
                chunk_counter += 1
                chunk_id = f"{document_id}_p{page_num}_c{chunk_counter}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "document_name": document_name,
                    "project": project,
                    "version": version,
                    "page_number": page_num,
                    "section": section,
                    "content": current_chunk_text.strip()
                })

        logger.info(f"Chunked document {document_name}: {len(chunks)} section-aware chunks generated.")
        return chunks
