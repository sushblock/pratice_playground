import magic
import mimetypes
from typing import Dict, Type
from doc_adapter_abs import DocumentAdapter
from pdf_adapter import GenericPDFAdapter
from markdown_adapter import MarkdownAdapter
from text_adapter import TextAdapter
from ocr_img_adapter import OCRAdapter
from rag_config import RAGConfig
import os


"""
The most reliable way to automate document ingestion is to combine MIME-type detection with a Registry-based Factory Pattern.
While simple extension checks (e.g., .pdf) are common, using the python-magic library is the best practice for production RAG pipelines because it identifies files by their "magic numbers" (internal byte structure), making it robust against incorrectly named files.

Benefits:
1. Security & Reliability: Using python-magic prevents the system from crashing if a user renames a .txt file to .pdf.
2. Decoupled Logic: The factory doesn't need to know how to parse a PDF; it only needs to know which class is responsible for it.
3. Extensibility: To support a new format (like .docx or .csv), we simply create a new adapter subclass and add one line to the _adapters registry.
4. Automatic Meta-Tagging: During the get_adapter step, we can automatically inject metadata (like file_type or encoding) into the resulting chunks for better RAG filtering later. 

The IngestionFactory class is the one responsible for distributing the configuration to the adapters it creates.

Why this is essential?
1. A/B Testing: We can run two versions of our pipeline with different chunk_size values (e.g., 512 vs 1024) to see which provides better retrieval accuracy for our specific dataset.
2. Scaling: In 2025, modern embedding models (like those from OpenAI or Cohere) support much larger context windows. We may want to increase chunk_size for complex technical documents while keeping it small for simple FAQs.
3. Environment Injection: We can populate the RAGConfig from a .yaml file or os.getenv(), making our code "Twelve-Factor App" compliant for cloud deployment.
"""


class IngestionFactory:
    """
    Automates file type detection and adapter selection.
    """
    def __init__(self, config: RAGConfig = None):
        # Use provided config or a default instance
        self.config = config or RAGConfig()

        # Registry mapping MIME types to their specific Adapter classes
        self._adapters: Dict[str, Type[DocumentAdapter]] = {
            "application/pdf": GenericPDFAdapter,
            "text/markdown": MarkdownAdapter,
            "text/x-markdown": MarkdownAdapter,
            "text/plain": TextAdapter,
            "image/png": OCRAdapter,             # For images
            "image/jpeg": OCRAdapter,            # For images
            # Add more as needed (e.g., application/vnd.openxmlformats-officedocument.wordprocessingml.document for .docx)
        }

    def get_adapter(self, file_path: str) -> DocumentAdapter:
        """
        Detects file type and returns the corresponding adapter instance.
        """
        # Detect MIME type based on file content (magic numbers)
        # 1. Try content-based detection first
        mime_type = magic.from_file(file_path, mime=True)
        
        # 2. Windows Fallback: If magic fails (octet-stream), guess by extension
        if mime_type == "application/octet-stream":
            guessed_type, _ = mimetypes.guess_type(file_path)
            if guessed_type:
                mime_type = guessed_type
                
        # 3. Final Fallback: Default to text/plain if it's a known text extension
        if mime_type == "application/octet-stream" and file_path.endswith('.txt'):
            mime_type = "text/plain"
        
        adapter_class = self._adapters.get(mime_type)
        
        if not adapter_class:
            raise ValueError(f"No adapter found for file type: {mime_type}")
            
        # Pass the global config into the specific adapter instance
        return adapter_class(config=self.config)

    def process_file(self, file_path: str):
        """Standard entry point for all file processing."""
        adapter = self.get_adapter(file_path)
        raw_data = adapter.load(file_path)
        return adapter.process(raw_data)