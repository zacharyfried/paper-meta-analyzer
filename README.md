# Paper Meta-Analyzer

Python tooling for screening academic papers for systematic reviews and meta-analysis workflows.

## Overview

Paper Meta-Analyzer helps automate the first-pass review of academic papers by combining Zotero metadata retrieval, PDF text extraction, structured GPT-based evaluation, and CSV export for downstream review.

The project was originally developed for a research workflow that screened papers for study population, methodology, relevant variables, and whether specific variable relationships were examined. The public version uses generic example criteria so the repository demonstrates the workflow without exposing a private review protocol.

## What I Built

- A Zotero connector for retrieving paper metadata and optional PDF attachments from a group library.
- A PDF processing utility with multiple extraction backends and readability checks.
- A GPT-assisted screening engine that evaluates papers against structured inclusion criteria.
- CSV export paths for metadata and evaluated paper decisions.
- Configuration support through `config.ini`, environment variables, and MySQL client settings.

## Workflow

```text
Zotero library
    |
    v
zotero_integration.py
    |
    v
paper metadata + optional PDFs
    |
    v
pdf_processor.py
    |
    v
extracted paper text
    |
    v
paper_analyzer.py
    |
    v
screening decisions + notes CSV
```

## Repository Contents

```text
.
|-- paper_analyzer.py            # GPT-assisted paper screening
|-- zotero_integration.py        # Zotero metadata/PDF retrieval
|-- pdf_processor.py             # PDF text extraction utilities
|-- config.ini.example           # Example credentials/config file
|-- examples/
|   `-- sample_evaluated_papers.csv
|-- docs/
|   `-- architecture.md
|-- requirements.txt
|-- LICENSE
`-- README.md
```

## Installation

Requirements:

- Python 3.8+
- OpenAI API key
- Zotero API key for Zotero retrieval
- MySQL database for `paper_analyzer.py`

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy the example config and fill in local credentials:

```bash
cp config.ini.example config.ini
```

The OpenAI and Zotero keys can also be set with environment variables:

```bash
export OPENAI_API_KEY="your_key_here"
export ZOTERO_API_KEY="your_key_here"
export ZOTERO_GROUP_ID="your_group_id"
export ZOTERO_COLLECTION_ID="your_collection_id"
```

MySQL credentials are read from `~/.my.cnf` by default:

```ini
[client]
user = your_mysql_user
password = your_mysql_password
host = localhost
```

## Usage

Retrieve metadata from Zotero:

```bash
python zotero_integration.py --limit 50 --output papers_metadata.csv
```

Retrieve metadata and download PDF attachments:

```bash
python zotero_integration.py --limit 50 --download-pdfs --output papers_metadata.csv
```

Extract text from a single PDF:

```bash
python pdf_processor.py /path/to/paper.pdf --output extracted.txt
```

Check whether PDFs have extractable text:

```bash
python pdf_processor.py /path/to/pdfs --check
```

Run GPT-assisted screening against a MySQL table:

```bash
python paper_analyzer.py --database research_papers --table papers --output evaluated_papers.csv
```

See [examples/sample_evaluated_papers.csv](examples/sample_evaluated_papers.csv) for the expected output shape.

## Expected Database Shape

`paper_analyzer.py` expects a MySQL table with paper metadata and extracted text. At minimum, the table should provide a content field:

```sql
CREATE TABLE papers (
    id INT PRIMARY KEY,
    title VARCHAR(500),
    authors TEXT,
    year INT,
    content TEXT
);
```

The analyzer also accepts `pdf_content` as a fallback text column if `content` is missing.

## Customization

The screening criteria live in `ResearchPaperAnalyzer._initialize_questions()` inside `paper_analyzer.py`.

To adapt the project for another systematic review:

1. Replace the question prompts with the target inclusion/exclusion criteria.
2. Update the result column names in `evaluate_paper()`.
3. Adjust the final inclusion logic to match the review protocol.
4. Update the CSV output documentation so reviewers understand each column.

## Limitations

- The current scripts are research workflow tools, not a packaged Python library.
- GPT responses should be treated as screening support, not final scientific judgment.
- PDF extraction quality depends on the source PDF; scanned/image-only PDFs may require OCR outside this repo.
- The analyzer currently uses a fixed prompt set and assumes a MySQL-backed paper table.

## More Detail

See [docs/architecture.md](docs/architecture.md) for component responsibilities, data flow, and extension points.

## License

MIT License. See [LICENSE](LICENSE).
