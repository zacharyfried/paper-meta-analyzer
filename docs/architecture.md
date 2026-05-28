# Architecture Notes

Paper Meta-Analyzer is organized as three command-line scripts that can be run independently or combined into a review workflow.

## Components

### `zotero_integration.py`

Connects to a Zotero group library, retrieves paper metadata, optionally downloads PDF attachments, and exports metadata to CSV.

Primary responsibilities:

- Load Zotero credentials from `config.ini` or environment variables.
- Retrieve papers from a full group library or a specific collection.
- Normalize common metadata fields such as title, authors, year, publication, DOI, URL, abstract, item type, and tags.
- Export metadata to CSV for inspection or downstream processing.

### `pdf_processor.py`

Extracts text from PDF files and reports whether a PDF appears to have readable embedded text.

Primary responsibilities:

- Try multiple extraction backends: `pdfplumber`, `PyPDF2`, and `PyMuPDF`.
- Clean extracted text by normalizing whitespace and common Unicode artifacts.
- Process a single PDF or a directory of PDFs.
- Identify likely image-based PDFs that need OCR outside this repo.

### `paper_analyzer.py`

Reads paper text from a MySQL table and evaluates each paper against structured review criteria using the OpenAI API.

Primary responsibilities:

- Load OpenAI and MySQL credentials.
- Read paper records from a configurable database table.
- Ask targeted screening questions about each paper.
- Short-circuit evaluation when exclusion criteria are met.
- Write screening decisions and reviewer notes to CSV.

## Data Flow

```text
1. Zotero metadata retrieval
   Zotero group/collection -> papers_metadata.csv

2. PDF extraction
   PDF files -> cleaned text

3. Database staging
   metadata + text -> MySQL papers table

4. GPT-assisted screening
   papers table -> evaluated_papers.csv
```

## Extension Points

- Replace the prompts in `ResearchPaperAnalyzer._initialize_questions()` for a new review protocol.
- Add additional extraction backends to `PDFProcessor.extraction_methods`.
- Add OCR preprocessing before `pdf_processor.py` for scanned PDFs.
- Swap the MySQL input layer for CSV, SQLite, or another datastore if the workflow no longer needs MySQL.
- Add human-review status columns for conflict resolution and final adjudication.

## Reliability Considerations

- Keep raw model outputs auditable by exporting notes alongside binary inclusion decisions.
- Validate a sample of GPT decisions manually before relying on batch outputs.
- Use small batches when changing prompts so reviewers can catch systematic prompt errors early.
- Store credentials outside the repository and keep generated logs, PDFs, and CSV exports out of git unless they are sanitized examples.
