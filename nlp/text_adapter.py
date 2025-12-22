from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from doc_adapter_abs import DocumentAdapter


"""
The TextAdapter serves as the "catch-all" for unstructured data like logs, plain .txt files, or READMEs.
Unlike the PDF or Markdown adapters, there is no inherent hierarchy (headers) to split on. Therefore, the goal is to split the text based on semantic density—prioritizing paragraphs and sentences to ensure that a single "thought" is kept together in one chunk for the RAG system.

Key Considerations for Plain Text:
1. Separator Hierarchy: Notice the separators list. It starts with \n\n (double newline). This ensures that if your text has distinct paragraphs, they are treated as separate units. It only breaks a paragraph into smaller pieces if that paragraph exceeds the chunk_size.
2. Encoding Resilience: Text files often come in varied encodings (UTF-8, Latin-1). The load method includes a basic try-except block to prevent the ingestion pipeline from crashing on older text documents.
3. Semantic Overlap: The chunk_overlap (100 characters) is critical for plain text. Since there are no headers to provide context, the overlap ensures that a search query matching the end of "Chunk A" can still "see" the beginning of the context in "Chunk B."
"""

class TextAdapter(DocumentAdapter):
    """
    Adapter for plain text files.
    Uses recursive splitting to preserve semantic boundaries (paragraphs/sentences).
    """

    def load(self, source: str) -> str:
        """Reads the plain text file with fallback encoding handling."""
        try:
            with open(source, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback for legacy text files (e.g., Windows-1252)
            with open(source, 'r', encoding='latin-1') as f:
                return f.read()

    def process(self, raw_data: str) -> List[Dict[str, Any]]:
        """
        Splits text based on a hierarchy of separators to keep 
        related sentences together.
        """
        # Recursive splitter tries to split by the first separator, 
        # moving to the next if the chunk is still too large.
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size, 
            chunk_overlap=self.config.chunk_overlap,
            # Priority: Paragraphs > Sentences > Words
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
        )
        
        chunks = text_splitter.split_text(raw_data)
        
        return [
            {
                "text": chunk, 
                "metadata": {
                    "format": "plain_text",
                    "character_count": len(chunk)
                }
            } 
            for chunk in chunks
        ]
