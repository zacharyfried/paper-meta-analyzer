# Research Paper Meta-Analysis Tool

A Python-based automated system for conducting meta-analyses of academic research papers, specifically designed to analyze relationships between variables in empirical studies.

## Author
**Zachary Fried**

## Project Overview

This project automates the systematic review process for academic research papers by:
- Retrieving papers from reference management systems (Zotero)
- Extracting text content from PDF files
- Using OpenAI's GPT models to analyze papers against specific research criteria
- Storing and exporting results for meta-analysis

### Background

This tool was developed as a research component to streamline the systematic review process for meta-analyses. It addresses the time-intensive nature of manually reviewing large numbers of academic papers by automating the initial screening and data extraction phases.

### Key Features
- **Automated Paper Retrieval**: Integration with Zotero reference management system
- **Multi-Method PDF Processing**: Robust text extraction using multiple libraries
- **AI-Powered Analysis**: Leverages GPT-4 for intelligent paper evaluation
- **Systematic Evaluation**: Structured assessment against predefined research criteria
- **Database Integration**: MySQL support for large-scale data management
- **Batch Processing**: Efficient handling of large paper collections

## Use Case Example

This system was originally developed to analyze the relationship between loneliness and alcohol use in adults, evaluating papers based on:
- Subject demographics (human adults 18+)
- Study methodology (empirical, quantitative/mixed methods)
- Presence of relevant variables (loneliness measures, alcohol use measures)
- Examination of variable relationships

The framework can be adapted for any systematic review requiring consistent evaluation criteria.

## Installation

### Prerequisites
- Python 3.8 or higher
- MySQL (optional, for database storage)
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone https://github.com/zacharyfried/paper-meta-analyzer.git
cd paper-meta-analyzer
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Configure credentials:

Create a `config.ini` file:
```ini
[openai]
key = your_openai_api_key_here

[zotero]
api_key = your_zotero_api_key_here
group_id = your_group_id
collection_id = your_collection_id
```

Alternatively, set environment variables:
```bash
export OPENAI_API_KEY="your_key_here"
export ZOTERO_API_KEY="your_key_here"
export ZOTERO_GROUP_ID="your_group_id"
export ZOTERO_COLLECTION_ID="your_collection_id"
```

4. (Optional) Configure MySQL:

Create `~/.my.cnf`:
```ini
[client]
user = your_mysql_user
password = your_mysql_password
host = localhost
```

## Usage

### 1. Paper Analysis (Main Script)

Analyze papers from a database:
```bash
python paper_analyzer.py --database mydb --output results.csv
```

Options:
- `--database`: MySQL database name (required)
- `--port`: MySQL port (default: 3306)
- `--output`: Output CSV file (default: evaluated_papers.csv)
- `--table`: Database table name (default: papers)

### 2. Zotero Integration

Retrieve papers from Zotero:
```bash
python zotero_integration.py --limit 50 --download-pdfs
```

Options:
- `--collection`: Specific collection ID
- `--limit`: Maximum papers to retrieve
- `--download-pdfs`: Download PDF attachments
- `--output`: Output CSV file

### 3. PDF Processing

Extract text from PDFs:
```bash
python pdf_processor.py /path/to/paper.pdf --output extracted.txt
```

Check PDF readability:
```bash
python pdf_processor.py /path/to/pdfs/ --check
```

Options:
- `--method`: Extraction method (auto/pdfplumber/pypdf2/pymupdf)
- `--check`: Check readability without full extraction
- `--output`: Save extracted text to file

## Project Structure

```
research-paper-meta-analysis/
│
├── paper_analyzer.py        # Main analysis engine
├── zotero_integration.py    # Zotero library connector
├── pdf_processor.py         # PDF text extraction utilities
├── requirements.txt         # Python dependencies
├── config.ini.example       # Example configuration file
└── README.md               # Documentation
```

## Customization

### Modifying Evaluation Criteria

Edit the questions in `paper_analyzer.py`:

```python
def _initialize_questions(self):
    return [
        {
            "main": "Your primary question here",
            "follow_up": "Optional follow-up for details"
        },
        # Add more questions...
    ]
```

### Adapting for Different Research Topics

1. Modify the evaluation questions to match your research criteria
2. Update the `evaluate_paper()` method logic
3. Adjust output columns in the results dataframe

## Technical Details

### PDF Processing Methods
- **pdfplumber**: Best for complex layouts and tables
- **PyPDF2**: Fast basic extraction
- **PyMuPDF (fitz)**: Balanced speed and accuracy

### Database Schema
Expected database table structure:
```sql
CREATE TABLE papers (
    id INT PRIMARY KEY,
    title VARCHAR(500),
    authors TEXT,
    year INT,
    content TEXT,  -- or pdf_content
    -- additional metadata fields
);
```

## Troubleshooting

### Common Issues

1. **PDF extraction fails**: Try different extraction methods or check if PDF is image-based
2. **API rate limits**: Increase delays between API calls
3. **Memory issues with large PDFs**: Process in smaller batches
4. **Database connection errors**: Verify MySQL credentials and permissions

### Logging
All components generate detailed logs:
- `zotero_retrieval.log`: Paper retrieval process
- `pdf_processing.log`: PDF extraction details
- Console output for real-time monitoring

## License

MIT License - See LICENSE file for details
