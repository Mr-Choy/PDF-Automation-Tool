# PDF Automation Tool 🚀

A powerful PDF automation tool built with Streamlit and PyMuPDF.

## Features
- **Cover Interaction Patch**: Create interactive buttons/hotspots on PDF covers.
- **Table of Contents (TOC) Extraction**: Automatically extract bookmarks or use visual OCR/Regex to detect TOC from PDF content.
- **Visual TOC Debugger**: Visualize how the engine detects TOC items on the page.

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   streamlit run app.py
   ```

## Dependencies
- `streamlit`
- `pymupdf`
- `pandas`
