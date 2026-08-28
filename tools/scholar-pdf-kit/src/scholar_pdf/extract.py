import os
import re
import sys
from pathlib import Path
from typing import Optional


def _win32_longpath(path: Path) -> str:
    r"""Prefix path with \\?\ on Windows to bypass 260 char limit."""
    abs_path = os.path.abspath(str(path))
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path


class PyMuPDFEngine:
    """Fast, robust structured Markdown extractor using PyMuPDF (fitz)."""

    @staticmethod
    def extract_markdown(pdf_path: Path, output_dir: Path) -> Path:
        import fitz  # PyMuPDF

        output_dir.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(str(pdf_path))
        
        md_lines = []
        md_lines.append(f"# {pdf_path.stem.replace('_', ' ')}\n")

        for page_num in range(len(doc)):
            page = doc[page_num]
            # Extract text blocks with layout structure
            blocks = page.get_text("blocks")
            # blocks are tuples: (x0, y0, x1, y1, text, block_no, block_type)
            # Sort by vertical then horizontal position
            sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

            for b in sorted_blocks:
                text = b[4].strip()
                if not text:
                    continue

                # Header detection heuristics
                lines = text.split("\n")
                first_line = lines[0].strip()

                if re.match(r"^(Abstract|1\.?\s+|2\.?\s+|3\.?\s+|4\.?\s+|5\.?\s+|6\.?\s+|7\.?\s+|8\.?\s+|Introduction|Related Work|Methodology|Methods|Architecture|Experiments|Results|Discussion|Conclusion|References)", first_line, re.IGNORECASE) and len(first_line) < 80:
                    md_lines.append(f"\n## {first_line}\n")
                    remaining = "\n".join(lines[1:]).strip()
                    if remaining:
                        md_lines.append(remaining + "\n")
                elif re.match(r"^(\d\.\d|\d\.\d\.\d)\s+", first_line) and len(first_line) < 80:
                    md_lines.append(f"\n### {first_line}\n")
                    remaining = "\n".join(lines[1:]).strip()
                    if remaining:
                        md_lines.append(remaining + "\n")
                elif first_line.startswith("Table ") or first_line.startswith("Figure "):
                    md_lines.append(f"\n> **{first_line}**\n")
                    remaining = "\n".join(lines[1:]).strip()
                    if remaining:
                        md_lines.append(f"> {remaining}\n")
                else:
                    # Clean linebreaks within paragraphs
                    cleaned_paragraph = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
                    md_lines.append(f"{cleaned_paragraph}\n")

        markdown_content = "\n".join(md_lines)
        out_file = output_dir / f"{pdf_path.stem}.md"
        out_file.write_text(markdown_content, encoding="utf-8")
        return out_file


class DoclingEngine:
    @staticmethod
    def extract_markdown(pdf_path: Path, output_dir: Path) -> Path:
        """Runs Docling on a PDF and returns the path to the extracted Markdown file."""
        try:
            from docling.document_converter import DocumentConverter
            output_dir.mkdir(parents=True, exist_ok=True)
            converter = DocumentConverter()
            result = converter.convert(str(pdf_path))
            markdown_text = result.document.export_to_markdown()
            out_file = output_dir / f"{pdf_path.stem}.md"
            out_file.write_text(markdown_text, encoding="utf-8")
            return out_file
        except Exception:
            # Fallback to PyMuPDFEngine
            return PyMuPDFEngine.extract_markdown(pdf_path, output_dir)


class GrobidEngine:
    @staticmethod
    def extract_markdown(pdf_path: Path, output_dir: Path, grobid_url: str = "http://localhost:8070") -> Path:
        """Sends a PDF to Grobid, receives TEI XML, and saves it."""
        try:
            import requests
        except ImportError:
            raise ImportError("Grobid dependencies not installed. Please install scholar-pdf-kit[extract]")
            
        output_dir.mkdir(parents=True, exist_ok=True)
        url = f"{grobid_url.rstrip('/')}/api/processFulltextDocument"
        with open(pdf_path, 'rb') as f:
            files = {'input': (pdf_path.name, f, 'application/pdf')}
            response = requests.post(url, files=files, timeout=300)
            
        if response.status_code != 200:
            raise RuntimeError(f"Grobid failed with status {response.status_code}: {response.text}")
            
        tei_xml = response.content
        out_xml = output_dir / f"{pdf_path.stem}.tei.xml"
        out_xml.write_bytes(tei_xml)
        return out_xml
