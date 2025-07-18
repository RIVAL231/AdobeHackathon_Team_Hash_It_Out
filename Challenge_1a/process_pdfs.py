import os
import json
import re
from pathlib import Path
import pdfplumber
from pypdf import PdfReader

def extract_title_from_metadata(pdf_path):
    """Extract document title from PDF metadata."""
    try:
        reader = PdfReader(pdf_path)
        if reader.metadata:
            title = reader.metadata.get('/Title', '').strip()
            if title:
                return title
    except:
        pass
    return None

def extract_title_from_content(pdf_path):
    """Extract document title from first page content."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 0:
                first_page = pdf.pages[0]
                
                # Get text with detailed information
                chars = first_page.chars
                if not chars:
                    return None
                
                # Group characters by font size and position
                font_sizes = {}
                for char in chars:
                    size = char.get('size', 0)
                    if size not in font_sizes:
                        font_sizes[size] = []
                    font_sizes[size].append(char)
                
                # Find the largest font size (likely title)
                if font_sizes:
                    largest_font = max(font_sizes.keys())
                    title_chars = font_sizes[largest_font]
                    
                    # Reconstruct text from characters
                    title_text = ''.join([char['text'] for char in title_chars]).strip()
                    
                    # Clean up the title
                    title_lines = title_text.split('\n')
                    for line in title_lines:
                        line = line.strip()
                        if len(line) > 5 and len(line) < 150:
                            return line
                
                # Fallback: use first meaningful line
                text = first_page.extract_text()
                if text:
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if len(line) > 5 and len(line) < 150:
                            return line
    except:
        pass
    return None

def extract_title(pdf_path):
    """Extract document title from PDF."""
    # Try metadata first
    title = extract_title_from_metadata(pdf_path)
    if title:
        return title
    
    # Try content extraction
    title = extract_title_from_content(pdf_path)
    if title:
        return title
    
    return "Untitled Document"

def is_potential_heading(text, font_size, avg_font_size, page_width):
    """Determine if text is likely a heading based on various factors."""
    text = text.strip()
    
    # Skip very short or very long text
    if len(text) < 3 or len(text) > 150:
        return False
    
    # Skip text that looks like body content
    if len(text) > 100 and not text.endswith((':',)):
        return False
    
    # Check for heading patterns
    heading_patterns = [
        r'^\d+\.?\s+',  # Numbered sections (1. or 1)
        r'^[A-Z][a-z]*\s+[A-Z]',  # Title Case
        r'^[A-Z\s]+$',  # ALL CAPS
        r'^\w+\.\d+',   # Section numbers like 2.1
    ]
    
    for pattern in heading_patterns:
        if re.match(pattern, text):
            return True
    
    # Check font size (should be larger than average)
    if font_size > avg_font_size * 1.1:
        return True
    
    return False

def get_heading_level(font_size, font_size_hierarchy):
    """Determine heading level based on font size hierarchy."""
    # Sort unique font sizes in descending order
    sorted_sizes = sorted(set(font_size_hierarchy), reverse=True)
    
    if len(sorted_sizes) <= 1:
        return "H1"
    
    # Map font sizes to heading levels (H1, H2, H3)
    try:
        index = sorted_sizes.index(font_size)
        return f"H{min(index + 1, 3)}"
    except ValueError:
        return "H3"

def extract_outline_from_bookmarks(pdf_path):
    """Extract outline from PDF bookmarks if available."""
    try:
        reader = PdfReader(pdf_path)
        if reader.outline:
            outline = []
            
            def process_bookmark(bookmark_item, level=1):
                if isinstance(bookmark_item, list):
                    for item in bookmark_item:
                        process_bookmark(item, level)
                else:
                    title = str(bookmark_item.title).strip()
                    if title and len(title) > 2:
                        # Get page number (approximate)
                        page_num = 1
                        if hasattr(bookmark_item, 'page'):
                            try:
                                page_num = reader.get_destination_page_number(bookmark_item) + 1
                            except:
                                pass
                        
                        outline.append({
                            "level": f"H{min(level, 3)}",
                            "text": title,
                            "page": page_num
                        })
                    
                    # Process children
                    if hasattr(bookmark_item, 'children') and bookmark_item.children:
                        for child in bookmark_item.children:
                            process_bookmark(child, level + 1)
            
            process_bookmark(reader.outline)
            return outline
    except:
        pass
    return []

def extract_outline_from_content(pdf_path):
    """Extract outline from PDF content analysis."""
    outline = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_font_sizes = []
            potential_headings = []
            
            # First pass: collect font size information
            for page_num, page in enumerate(pdf.pages):
                chars = page.chars
                for char in chars:
                    size = char.get('size', 0)
                    if size > 0:
                        all_font_sizes.append(size)
            
            if not all_font_sizes:
                return outline
            
            avg_font_size = sum(all_font_sizes) / len(all_font_sizes)
            
            # Second pass: identify potential headings
            for page_num, page in enumerate(pdf.pages):
                page_width = page.width
                
                # Extract text with formatting information
                chars = page.chars
                if not chars:
                    continue
                
                # Group characters by line
                lines = {}
                for char in chars:
                    y = char.get('y0', 0)
                    if y not in lines:
                        lines[y] = []
                    lines[y].append(char)
                
                # Process each line
                for y_pos in sorted(lines.keys(), reverse=True):
                    line_chars = sorted(lines[y_pos], key=lambda x: x.get('x0', 0))
                    line_text = ''.join([char['text'] for char in line_chars]).strip()
                    
                    if not line_text:
                        continue
                    
                    # Get the dominant font size for this line
                    font_sizes = [char.get('size', avg_font_size) for char in line_chars]
                    dominant_font_size = max(set(font_sizes), key=font_sizes.count)
                    
                    # Check if this line could be a heading
                    if is_potential_heading(line_text, dominant_font_size, avg_font_size, page_width):
                        potential_headings.append({
                            "text": line_text,
                            "page": page_num + 1,
                            "font_size": dominant_font_size
                        })
            
            # Remove duplicates and sort
            seen_texts = set()
            unique_headings = []
            
            for heading in potential_headings:
                text_key = heading["text"].lower().strip()
                if text_key not in seen_texts and len(text_key) > 2:
                    seen_texts.add(text_key)
                    unique_headings.append(heading)
            
            # Sort by page number
            unique_headings.sort(key=lambda x: (x["page"], -x["font_size"]))
            
            # Create final outline with heading levels
            font_size_hierarchy = [h["font_size"] for h in unique_headings]
            
            for heading in unique_headings:
                level = get_heading_level(heading["font_size"], font_size_hierarchy)
                outline.append({
                    "level": level,
                    "text": heading["text"],
                    "page": heading["page"]
                })
    
    except Exception as e:
        print(f"Error extracting outline from content: {str(e)}")
    
    return outline

def extract_outline(pdf_path):
    """Extract document outline/structure from PDF."""
    # Try bookmarks first
    outline = extract_outline_from_bookmarks(pdf_path)
    if outline:
        return outline
    
    # Fall back to content analysis
    return extract_outline_from_content(pdf_path)

def process_single_pdf(pdf_path):
    """Process a single PDF and extract title and outline."""
    try:
        # Extract title
        title = extract_title(pdf_path)
        
        # Extract outline
        outline = extract_outline(pdf_path)
        
        return {
            "title": title,
            "outline": outline
        }
    
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        # Return minimal valid structure on error
        return {
            "title": "Document",
            "outline": []
        }

def process_pdfs():
    """Main function to process all PDFs in the input directory."""
    # Get input and output directories
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in input directory")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        
        # Process the PDF
        result = process_single_pdf(pdf_file)
        
        # Create output JSON file
        output_file = output_dir / f"{pdf_file.stem}.json"
        
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            
            print(f"✓ Processed {pdf_file.name} -> {output_file.name}")
            print(f"  Title: {result['title']}")
            print(f"  Outline entries: {len(result['outline'])}")
            
        except Exception as e:
            print(f"✗ Error writing output for {pdf_file.name}: {str(e)}")

if __name__ == "__main__":
    print("Starting PDF processing...")
    process_pdfs()
    print("PDF processing completed.")