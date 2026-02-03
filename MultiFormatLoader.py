import base64

from langchain_core.documents import Document
from langchain_community.document_loaders import (PyMuPDFLoader, TextLoader, CSVLoader)
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
import fitz
from PIL import Image
import pytesseract
import io
from pathlib import Path
from typing import List
import pandas as pd
import xml.etree.ElementTree as ET
import json
import re


def is_quality_text(text: str, min_length: int = 50, min_alpha_ratio: float = 0.6) -> bool:
    """
    Check if OCR text is high enough quality to be useful.

    Filters out:
    - Text that's too short (likely logos, icons)
    - Text with too few alphabetic characters (garbage OCR)
    - Text that's mostly symbols/numbers without context
    """
    if not text or not text.strip():
        return False

    cleaned = text.strip()

    # Must be at least min_length characters
    if len(cleaned) < min_length:
        return False

    # Count alphabetic characters
    alpha_chars = sum(1 for c in cleaned if c.isalpha())
    total_chars = len(cleaned.replace(" ", "").replace("\n", ""))

    if total_chars == 0:
        return False

    # Must have at least min_alpha_ratio alphabetic characters
    alpha_ratio = alpha_chars / total_chars
    if alpha_ratio < min_alpha_ratio:
        return False

    # Must have at least 3 words
    words = cleaned.split()
    if len(words) < 3:
        return False

    return True


class MultiFormatLoader:
    def __init__(self, directory_path: str):
        self.directory_path = directory_path
        self.documents: List[Document] = []

    def load_all(self) -> List[Document]:
        """Load all supported file types from directory"""

        for file_path in Path(self.directory_path).rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()

                try:
                    if ext == ".pdf":
                        self._load_pdf(str(file_path))
                    elif ext == ".txt":
                        self._load_txt(str(file_path))
                    elif ext == ".csv":
                        self._load_csv(str(file_path))
                    elif ext == ".xlsx":
                        self._load_xlsx(str(file_path))
                    elif ext == ".xml":
                        self._load_xml(str(file_path))
                    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"]:
                        self._load_image(str(file_path))
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")

        return self.documents

    def _load_pdf(self, file_path: str):
        """Load pdf with text and images"""
        loader = PyMuPDFLoader(file_path)
        docs = loader.load()

        # Track which pages have sufficient text
        pages_with_text = set()

        for doc in docs:
            doc.metadata['file_type'] = 'pdf'
            doc.metadata['source'] = file_path

            # If page has meaningful text, mark it
            if len(doc.page_content.strip()) > 100:
                pages_with_text.add(doc.metadata.get('page', 0))

        self.documents.extend(docs)

        # Only OCR images from pages that lack text (scanned pages)
        self._extract_pdf_images(file_path, skip_pages=pages_with_text)

    def _extract_pdf_images(self, file_path: str, skip_pages: set = None):
        """Extract and OCR images only from pages lacking text (scanned pages)."""
        if skip_pages is None:
            skip_pages = set()

        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            # Skip pages that already have text extracted
            if page_num in skip_pages:
                continue

            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]

                    image = Image.open(io.BytesIO(image_bytes))
                    text = pytesseract.image_to_string(image)

                    # Only add if text passes quality check
                    if is_quality_text(text):
                        self.documents.append(Document(
                            page_content=text,
                            metadata={
                                'file_type': 'pdf_image',
                                'source': file_path,
                                'page': page_num,
                                'image_index': img_index
                            }
                        ))
                except Exception as e:
                    print(f"Error extracting image: {e}")


    def _load_txt(self, file_path: str):
        """Load txt with text"""
        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()

        for doc in docs:
            doc.metadata['file_type'] = 'txt'

        self.documents.extend(docs)

    def _load_csv(self, file_path: str):
        """Load csv with text"""
        loader = CSVLoader(file_path)
        docs = loader.load()

        for doc in docs:
            doc.metadata['file_type'] = 'csv'

        self.documents.extend(docs)

    def _load_xlsx(self, file_path: str):
        """Load Excel file with Pandas for better control"""
        try:
            excel_file = pd.ExcelFile(file_path)

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)

                text = f"Sheet: {sheet_name}\n\n"

                self.documents.append(Document(
                    page_content=text,
                    metadata={
                        "file_type": "excel",
                        "source": file_path,
                        "sheet_name": sheet_name,
                        "rows": len(df),
                        "columns": len(df.columns),
                        "column_names": list(df.columns)
                    }
                ))
        except Exception as e:
            print(f"Error loading Excel {file_path}: {e}")

    def _load_xml(self, file_path: str):
        """Load xml files with structure preservation"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            def xml_to_dict(element):
                """Recursive function to convert xml to dictionary"""
                result = {}

                if element.attrib:
                    result["@attributes"] = element.attrib
                if element.text and element.text.strip():
                    result["text"] = element.text.strip()

                for child in element:
                    child_data = xml_to_dict(child)
                    if child.tag in result:
                        if not isinstance(result[child.tag], list):
                            result[child.tag] = [result[child.tag]]
                        result[child.tag].append(child_data)
                    else:
                        result[child.tag] = child_data
                return result

            xml_dict = {root.tag: xml_to_dict(root)}

            text = f"XML Root: {root.tag}\n\n"
            text += json.dumps(xml_dict, indent=2, ensure_ascii=False)

            def xml_to_text(element, level=0):
                """Convert xml to indented text"""

                indent = " " * level
                text_parts = [f"{indent}{element.tag}"]

                if element.attrib:
                    attrs = ", ".join([f"{k}={v}" for k, v in element.attrib.items()])
                    text_parts.append(f" ({attrs})")

                if element.text and element.text.strip():
                    text_parts.append(f": {element.text.strip()}")

                result = "".join(text_parts) + "\n"

                for child in element:
                    result += xml_to_text(child, level + 1)
                return result

            self.documents.append(Document(
                page_content=text,
                metadata={
                    "file_type": "xml",
                    "source": file_path,
                    "root_tag": root.tag,
                    "structured_data": json.dumps(xml_dict),
                    "num_children": len(list(root))
                }
            ))
        except Exception as e:
            print(f"Error loading XML {file_path}: {e}")

    def _load_image(self, file_path: str):
        """Load and OCR image files"""

        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)

            # Only add if text passes quality check
            if is_quality_text(text):
                self.documents.append(Document(
                    page_content=text,
                    metadata={
                        "file_type": "image",
                        "source": file_path,
                        "format": image.format
                    }
                ))
        except Exception as e:
            print(f"Error processing image {file_path}: {e}")









