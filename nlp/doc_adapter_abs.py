from abc import ABC, abstractmethod
from typing import List, Dict, Any
from rag_config import RAGConfig

"""
A robust RAG ingestion pipeline requires an adapter pattern to handle diverse document types (PDFs, Markdown, text) consistently. Using Python's abc module, we can define a standardized interface that all format-specific processors must follow.
This Abstract Adapter Base Class defines the required "contract" for any document loader. It ensures every adapter has a load and process method, allowing our main ingestion pipeline to handle them interchangeably.

Following this pattern, we would create concrete subclasses for each format:
1. PDFAdapter: Inherits from DocumentAdapter and uses modern tools like pymupdf4llm to extract Markdown-formatted text to preserve hierarchy.
2. MarkdownAdapter: Inherits from DocumentAdapter and might focus on segmenting text specifically by existing header levels (#, ##).
3. TextAdapter: A simple implementation for plain .txt or .logs files.

Benefits of this Pattern
1. Interchangeability: Our main ingestion function can accept any DocumentAdapter subclass and call .process() without needing to know the specific file type.
2. Enforced Standards: Developers adding support for new formats (like Excel or HTML) are forced to implement the same methods, preventing "garbage in, garbage out" scenarios in your vector database.
3. Metadata Consistency: We can mandate that the process method always returns a specific metadata schema (e.g., source file, page number, timestamp) which is critical for accurate RAG citations.

"""

class DocumentAdapter(ABC):
    """
    Abstract Base Class for document processing adapters.
    Ensures a consistent interface for different file formats in the RAG pipeline.
    """

    def __init__(self, config: RAGConfig):
        self.config = config

    @abstractmethod
    def load(self, source: str) -> str:
        """Extract raw text or structural data from the source file."""
        pass

    @abstractmethod
    def process(self, raw_data: str) -> List[Dict[str, Any]]:
        """
        Clean, structure, and convert data into a list of RAG-ready documents.
        Returns: List of dicts with 'text' and 'metadata'.
        """
        pass
