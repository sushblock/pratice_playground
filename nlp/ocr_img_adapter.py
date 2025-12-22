import cv2
from PIL import Image
import numpy as np
from docling.document_converter import DocumentConverter
from typing import List, Dict, Any
from markdown_adapter import MarkdownAdapter
from doc_adapter_abs import DocumentAdapter
from rag_config import RAGConfig



"""
Processing scanned documents or standalone images (like photos of whiteboards or receipts) for RAG requires an OCR-capable adapter.
While older pipelines used basic Tesseract, the modern standard is to use Docling (from IBM) or Unstructured. These libraries don't just "read text"; they perform Layout Analysis to identify if a block of text is a title, a paragraph, or a table.
1. Image/Scanned PDF Adapter
This adapter uses Docling, which is highly efficient for converting scanned images into structured Markdown—the preferred format for RAG.

Key Improvements in 2025 OCR Pipelines
1. Multimodal Advantage: Modern adapters like Docling or Unstructured can export tables from images into clean HTML or Markdown tables. This prevents the "scrambled text" issue common in older OCR tools where columns would merge into a single line.
2. Document Intelligence: Tools like Surya or DocTR can now identify handwritten notes and checkbox states in scanned forms, which was difficult for Tesseract.
3. Hierarchical Retrieval: By converting the OCR output to Markdown, your RAG system can still "see" headers that were once just bold text in an image. This metadata makes the retrieval step much more precise. 

Recommended Libraries (2025)
1. Docling: Excellent for speed and Markdown-ready OCR.
2. Unstructured: Best for "high-res" layout partitioning when you need to know exactly where elements are on a page.
3. EasyOCR: Best for "natural scene" images, like signs or labels, rather than just documents. 
"""

class OCRAdapter(DocumentAdapter):
    """
    Adapter for scanned files. It 'has-a' MarkdownAdapter 
    to handle the final processing stage.
    """
    def __init__(self, config: 'RAGConfig'):
        # Pass config to the base class
        super().__init__(config)
        self.converter = DocumentConverter()
        
        # Share the SAME config with the internal processor
        self.md_processor = MarkdownAdapter(config=self.config)

    def binarize_image(self, image_path, output_path, threshold=180):
        """Converts a color image to a high-contrast black and white image."""
        img = Image.open(image_path).convert('L') # Convert to grayscale
        img_np = np.array(img)
        
        # Apply a simple threshold: anything darker than 'threshold' becomes black (0), otherwise white (255)
        img_np = (img_np > threshold) * 255
        
        # Save the processed image
        Image.fromarray(img_np.astype(np.uint8)).save(output_path)

    def deskew_image(self, image_path, output_path):
        """Detects and corrects the skew angle of an image using OpenCV."""
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bitwise_not(gray) # Invert for finding contours correctly

        # Detect contours to find the dominant text orientation
        coords = np.column_stack(np.where(gray > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        # Correct the angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Rotate the image back to horizontal
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        # Save the deskewed image (convert back to BGR for standard viewing)
        cv2.imwrite(output_path, cv2.cvtColor(rotated, cv2.COLOR_GRAY2BGR))

    def load(self, source: str) -> str:
        """
        Applies binarization AND deskewing for high accuracy OCR.
        """
        temp_binarized_path = source + ".binarized.png"
        temp_deskewed_path = source + ".deskewed.png"

        self.binarize_image(source, temp_binarized_path) # Use the previous function
        self.deskew_image(temp_binarized_path, temp_deskewed_path) # Add this step

        # Convert the final, clean image
        result = self.converter.convert(temp_deskewed_path)
        return result.document.export_to_markdown()

    def process(self, raw_data: str) -> List[Dict[str, Any]]:
        """
        Delegate the final processing to the MarkdownAdapter.
        This keeps your chunking logic consistent across all adapters.
        """
        # Call the MarkdownAdapter's process method on the OCR output
        chunks = self.md_processor.process(raw_data)
        
        # Optionally tag these chunks so you know they came from an image
        for chunk in chunks:
            chunk["metadata"]["source_type"] = "scanned_image"
            
        return chunks
