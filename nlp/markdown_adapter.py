from typing import List, Dict, Any
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from doc_adapter_abs import DocumentAdapter
from rag_config import RAGConfig


"""
The MarkdownAdapter is highly valued because Markdown is often the "Gold Standard" for LLM ingestion; it is already structured with headers, lists, and tables.
Unlike the PDF adapter, which has to guess the structure, the Markdown adapter can use Semantic Splitters to break the document at logical hierarchy levels (e.g., #, ##), ensuring that a sub-section is never separated from its parent heading.

Key Features for RAG Ingestion:
1. Header Metadata: If a chunk comes from a section titled ## Installation Instructions, that title is automatically added to the metadata of that chunk. During retrieval, the LLM knows exactly which section it is looking at.
2. Table Preservation: Markdown tables are natively preserved as text. RAG systems in 2025 prefer this because modern LLMs (like GPT-4o or Claude 3.5) are excellent at parsing Markdown table syntax without specialized table-extraction logic.
3. Recursive Splitting: If a single section (e.g., a "Terms of Service" section) is 5,000 words long, the RecursiveCharacterTextSplitter ensures it is broken down into 1,000-character chunks while respecting paragraph and sentence boundaries.
"""

class MarkdownAdapter(DocumentAdapter):
    """
    Adapter specifically for native Markdown files. 
    Uses structural headers to maintain contextual integrity for RAG.
    """

    def __init__(self, config: 'RAGConfig'):

        # Pass config to the base class
        super().__init__(config)
        # Define the hierarchy for structural splitting
        self.headers_to_split_on = [
            ("#", "Header_1"),
            ("##", "Header_2"),
            ("###", "Header_3"),
        ]

    def load(self, source: str) -> str:
        """Reads the Markdown file directly as a string."""
        with open(source, 'r', encoding='utf-8') as f:
            return f.read()

    def process(self, raw_data: str) -> List[Dict[str, Any]]:
        """
        Processes Markdown by splitting on headers first to preserve context,
        then recursively splitting by character to fit token limits.
        """
        # 1. Structural Splitting: Splits by headers and moves header text into metadata
        md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False # Keep headers in the text for the LLM to see hierarchy
        )
        header_splits = md_splitter.split_text(raw_data)

        # 2. Size-based Splitting: Ensures individual sections don't exceed the chunk size
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        final_docs = text_splitter.split_documents(header_splits)
        
        # 3. Format for Vector Database
        return [
            {
                "text": doc.page_content, 
                "metadata": {
                    **doc.metadata,
                    "format": "markdown"
                }
            } 
            for doc in final_docs
        ]