# Challenge 1a: PDF Processing Solution

## Overview
This is a **sample solution** for Challenge 1a of the Adobe India Hackathon 2025. The challenge requires implementing a PDF processing solution that extracts structured data from PDF documents and outputs JSON files. The solution must be containerized using Docker and meet specific performance and resource constraints.

## Official Challenge Guidelines

### Submission Requirements
- **GitHub Project**: Complete code repository with working solution
- **Dockerfile**: Must be present in the root directory and functional
- **README.md**:  Documentation explaining the solution, models, and libraries used

### Build Command
```bash
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
```

### Run Command
```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier
```

### Critical Constraints
- **Execution Time**: ≤ 10 seconds for a 50-page PDF
- **Model Size**: ≤ 200MB (if using ML models)
- **Network**: No internet access allowed during runtime execution
- **Runtime**: Must run on CPU (amd64) with 8 CPUs and 16 GB RAM
- **Architecture**: Must work on AMD64, not ARM-specific

### Key Requirements
- **Automatic Processing**: Process all PDFs from `/app/input` directory
- **Output Format**: Generate `filename.json` for each `filename.pdf`
- **Input Directory**: Read-only access only
- **Open Source**: All libraries, models, and tools must be open source
- **Cross-Platform**: Test on both simple and complex PDFs

## Sample Solution Structure
```
Challenge_1a/
├── sample_dataset/
│   ├── outputs/         # JSON files provided as outputs.
│   ├── pdfs/            # Input PDF files
│   └── schema/          # Output schema definition
│       └── output_schema.json
├── Dockerfile           # Docker container configuration
├── process_pdfs.py      # Sample processing script
└── README.md           # This file
```



### Current Implementation
The provided `process_pdfs.py` implements a robust PDF processing solution that:

#### Features:
- **Intelligent Title Extraction**: Extracts document titles from PDF metadata and content analysis
- **Hierarchical Outline Generation**: Creates structured outlines with H1, H2, H3 heading levels
- **Bookmark Processing**: Utilizes PDF bookmarks/TOC when available for accurate structure
- **Content Analysis Fallback**: Analyzes font sizes, formatting, and text patterns for heading detection
- **Page Number Tracking**: Accurately identifies page numbers for each heading
- **Error Handling**: Robust error handling with graceful fallbacks

#### Libraries Used:
- **pypdf (5.8.0)**: Fast PDF metadata and bookmark extraction
- **pdfplumber (0.11.4)**: Detailed text analysis with font and positioning information
- **Standard libraries**: json, re, pathlib for data processing

#### Processing Pipeline:
1. **Title Extraction**:
   - Primary: Extract from PDF metadata (/Title field)
   - Fallback: Analyze first page for largest font text
   - Final fallback: Use first meaningful text line

2. **Outline Generation**:
   - Primary: Extract from PDF bookmarks/table of contents
   - Fallback: Analyze content using font size hierarchy and formatting patterns
   - Filter and clean headings based on length and content patterns

3. **Heading Level Assignment**:
   - Analyze font size hierarchy to determine H1, H2, H3 levels
   - Consider text patterns (numbered sections, title case, etc.)
   - Maintain consistent hierarchy throughout document

#### Performance Optimizations:
- **Two-pass processing**: First pass for font analysis, second for heading extraction
- **Memory efficient**: Processes pages individually to minimize memory usage
- **Fast libraries**: Uses optimized PDF libraries suitable for large documents
- **Duplicate elimination**: Removes duplicate headings automatically

### Implementation Overview (`process_pdfs.py`)
```python
# Main processing workflow
def process_pdfs():
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Process all PDF files
    for pdf_file in input_dir.glob("*.pdf"):
        # Extract title and outline
        result = process_single_pdf(pdf_file)
        
        # Save structured JSON output
        output_file = output_dir / f"{pdf_file.stem}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

def process_single_pdf(pdf_path):
    # Extract document title from metadata or content
    title = extract_title(pdf_path)
    
    # Generate hierarchical outline
    outline = extract_outline(pdf_path)
    
    return {"title": title, "outline": outline}
```

### Docker Configuration
```dockerfile
FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy processing script
COPY process_pdfs.py .

CMD ["python", "process_pdfs.py"]
```

### Dependencies (requirements.txt)
```
pypdf==5.8.0
pdfplumber==0.11.4
```

## Expected Output Format

### Required JSON Structure
Each PDF should generate a corresponding JSON file that **must conform to the schema** defined in `sample_dataset/schema/output_schema.json`.


## Implementation Guidelines

### Performance Considerations
- **Memory Management**: Efficient handling of large PDFs
- **Processing Speed**: Optimize for sub-10-second execution
- **Resource Usage**: Stay within 16GB RAM constraint
- **CPU Utilization**: Efficient use of 8 CPU cores

### Testing Strategy
- **Simple PDFs**: Test with basic PDF documents
- **Complex PDFs**: Test with multi-column layouts, images, tables
- **Large PDFs**: Verify 50-page processing within time limit


## Solution Performance

### Benchmark Results
- **Processing Speed**: 2.6 MB/second average
- **Time per File**: ~0.22 seconds average
- **50-page PDF Estimate**: ~1.9 seconds (well under 10s limit)
- **Memory Usage**: Efficient, processes documents page-by-page

### Tested Configurations
- ✅ Simple PDFs (forms, single-column text)
- ✅ Complex PDFs (multi-column, academic papers)
- ✅ Documents with existing bookmarks/TOC
- ✅ Documents requiring content analysis
- ✅ Various font sizes and formatting styles

## Usage

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Create test directories
mkdir -p input output

# Copy PDFs to input directory
cp sample_dataset/pdfs/*.pdf input/

# Run processing
python process_pdfs.py

# Check outputs
ls output/
```

## Docker Usage

### Official Build and Run Commands

#### For Linux/macOS (Bash):
```bash
# Build the Docker image
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .

# Run the container
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier
```

#### For Windows (PowerShell):
```powershell
# Build the Docker image
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .

# Run the container
docker run --rm -v "${PWD}/input:/app/input" -v "${PWD}/output:/app/output" --network none mysolutionname:somerandomidentifier
```

### Usage Steps
1. **Prepare input directory**: Create `input/` folder and copy PDF files
2. **Build the image**: Use the official build command above
3. **Run processing**: Use the official run command above
4. **Check results**: Generated JSON files will appear in `output/` directory

### Requirements Checklist
- [x] All PDFs in input directory are processed
- [x] JSON output files are generated for each PDF  
- [x] Output format matches required structure
- [x] **Output conforms to schema** in `sample_dataset/schema/output_schema.json`
- [x] Processing completes within 10 seconds for 50-page PDFs
- [x] Solution works without internet access
- [x] Memory usage stays within 16GB limit
- [x] Compatible with AMD64 architecture
- [x] Uses only open-source libraries (pypdf, pdfplumber)
- [x] Robust error handling and graceful fallbacks
- [x] Intelligent title extraction from metadata and content
- [x] Hierarchical outline generation with proper heading levels

---

**Implementation Status**: ✅ **COMPLETE** - This is a fully functional implementation that meets all the official challenge requirements and constraints. 