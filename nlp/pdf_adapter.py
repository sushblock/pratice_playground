from unstructured.partition.pdf import partition_pdf
from typing import List, Dict, Any
from doc_adapter_abs import DocumentAdapter

"""
A truly "generic" and robust PDFAdapter doesn't just treat the file as a text stream; it uses Document Layout Analysis (DLA) to identify objects like titles, narrative text, tables, and images. 
The most effective tool for this is Unstructured, which classifies every part of a PDF into "elements". This allows our adapter to handle any PDF—whether it's a multi-column academic paper, a financial report with complex tables, or a simple text document—by dynamically identifying its structure. 

This implementation uses Unstructured's hi_res strategy, which employs a computer vision model to detect layout objects. 

Why this is "Generic":
1. Layout Awareness: It handles multi-column layouts correctly by reading in "human" order rather than just scanning top-to-bottom.
2. Object Identification: It distinguishes between a Title (high-importance for search) and NarrativeText.
3. Table Precision: Instead of converting a table into a garbled string, it can provide the LLM with an HTML representation, which is significantly better for RAG reasoning.
4. Strategy Flexibility: We can swap the strategy to fast for simple text-heavy PDFs or ocr_only for scanned images within the same adapter. 
"""

class GenericPDFAdapter(DocumentAdapter):
    """
    A layout-aware adapter that identifies objects (Tables, Titles, Text) 
    using Computer Vision (Unstructured) for generic PDF processing.
    """

    def load(self, source: str) -> List[Any]:
        """
        Partitions the PDF into structural elements.
        - 'hi_res' strategy uses layout detection models.
        - 'infer_table_structure' extracts tables as HTML for LLMs.
        """
        return partition_pdf(
            filename=source,
            strategy="hi_res",          # Uses vision models to find objects
            infer_table_structure=True, # Preserves table rows/cols as HTML
            chunking_strategy="by_title", # Automatically groups text under its heading
            max_characters=self.config.chunk_size, 
            overlap=self.config.chunk_overlap
        )

    def process(self, elements: List[Any]) -> List[Dict[str, Any]]:
        """
        Iterates through identified objects and handles them based on type.
        """
        processed_chunks = []
        
        for el in elements:
            # Map elements to a standard RAG format
            chunk = {
                "text": el.text,
                "metadata": {
                    "type": el.category,  # e.g., 'Title', 'Table', 'NarrativeText'
                    "page_number": el.metadata.page_number,
                    "file_name": el.metadata.filename
                }
            }
            
            # Special handling for tables: Use HTML representation if available
            if el.category == "Table" and hasattr(el.metadata, "text_as_html"):
                chunk["text"] = el.metadata.text_as_html
            
            processed_chunks.append(chunk)
            
        return processed_chunks
