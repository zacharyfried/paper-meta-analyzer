#!/usr/bin/env python
"""
Zotero Integration for Research Paper Retrieval
Connects to Zotero library to fetch academic papers for analysis.

Author: Zachary Fried
"""

from pyzotero import zotero
import requests
import os
import csv
import logging
from datetime import datetime
import configparser


class ZoteroConnector:
    """
    Manages connection to Zotero library and paper retrieval.
    """

    def __init__(self, config_file='config.ini'):
        """
        Initialize Zotero connector with configuration.

        Args:
            config_file: Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.setup_logging()
        self.zot = None

    def _load_config(self, config_file):
        """
        Load configuration from file.

        Args:
            config_file: Path to config file

        Returns:
            Dictionary with configuration values
        """
        config = configparser.ConfigParser()

        # Set defaults
        zotero_config = {
            'api_key': os.getenv('ZOTERO_API_KEY', ''),
            'group_id': os.getenv('ZOTERO_GROUP_ID', ''),
            'collection_id': os.getenv('ZOTERO_COLLECTION_ID', '')
        }

        # Try to read from config file
        if os.path.exists(config_file):
            config.read(config_file)
            if 'zotero' in config:
                zotero_config.update({
                    'api_key': config['zotero'].get('api_key', zotero_config['api_key']),
                    'group_id': config['zotero'].get('group_id', zotero_config['group_id']),
                    'collection_id': config['zotero'].get('collection_id', zotero_config['collection_id'])
                })

        return zotero_config

    def setup_logging(self):
        """Set up logging for paper retrieval process."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('zotero_retrieval.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """
        Establish connection to Zotero library.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not all([self.config['api_key'], self.config['group_id']]):
                self.logger.error("Missing Zotero credentials in configuration")
                return False

            self.zot = zotero.Zotero(
                self.config['group_id'],
                'group',
                self.config['api_key']
            )
            self.logger.info("Successfully connected to Zotero")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Zotero: {e}")
            return False

    def retrieve_papers(self, collection_id=None, limit=None):
        """
        Retrieve papers from Zotero collection.

        Args:
            collection_id: Specific collection ID (optional)
            limit: Maximum number of papers to retrieve

        Returns:
            List of paper metadata dictionaries
        """
        if not self.zot:
            self.logger.error("Not connected to Zotero")
            return []

        papers = []
        collection_id = collection_id or self.config.get('collection_id')

        try:
            if collection_id:
                items = self.zot.collection_items(collection_id, limit=limit)
            else:
                items = self.zot.items(limit=limit)

            for item in items:
                # Skip attachments
                if item['data']['itemType'] == 'attachment':
                    continue

                paper_info = self._extract_paper_info(item)
                papers.append(paper_info)
                self.logger.info(f"Retrieved: {paper_info['title']}")

        except Exception as e:
            self.logger.error(f"Error retrieving papers: {e}")

        return papers

    def _extract_paper_info(self, item):
        """
        Extract relevant information from Zotero item.

        Args:
            item: Zotero item dictionary

        Returns:
            Dictionary with paper metadata
        """
        data = item['data']

        # Extract authors
        authors = []
        for creator in data.get('creators', []):
            if 'lastName' in creator:
                name = creator.get('lastName', '')
                if creator.get('firstName'):
                    name = f"{creator['firstName']} {name}"
                authors.append(name)

        return {
            'key': data.get('key', ''),
            'title': data.get('title', 'Untitled'),
            'authors': authors,
            'year': self._extract_year(data.get('date', '')),
            'publication': data.get('publicationTitle', ''),
            'doi': data.get('DOI', ''),
            'url': data.get('url', ''),
            'abstract': data.get('abstractNote', ''),
            'item_type': data.get('itemType', ''),
            'tags': [tag['tag'] for tag in data.get('tags', [])]
        }

    def _extract_year(self, date_string):
        """
        Extract year from date string.

        Args:
            date_string: Date in various formats

        Returns:
            Year as string or 'Unknown'
        """
        if not date_string:
            return 'Unknown'

        try:
            # Try to parse year from common formats
            if len(date_string) >= 4:
                return date_string[:4]
        except:
            pass

        return 'Unknown'

    def download_pdf(self, item_key, output_dir='pdfs'):
        """
        Download PDF attachment for a paper.

        Args:
            item_key: Zotero item key
            output_dir: Directory to save PDFs

        Returns:
            Path to downloaded PDF or None
        """
        if not self.zot:
            self.logger.error("Not connected to Zotero")
            return None

        os.makedirs(output_dir, exist_ok=True)

        try:
            # Get attachments for the item
            attachments = self.zot.children(item_key, item_type='attachment')

            for attachment in attachments:
                if attachment['data']['contentType'] == 'application/pdf':
                    # Download PDF content
                    pdf_content = self.zot.file(attachment['key'])

                    # Save to file
                    filename = f"{item_key}_{attachment['data'].get('filename', 'paper.pdf')}"
                    filepath = os.path.join(output_dir, filename)

                    with open(filepath, 'wb') as f:
                        f.write(pdf_content)

                    self.logger.info(f"Downloaded PDF: {filepath}")
                    return filepath

        except Exception as e:
            self.logger.error(f"Error downloading PDF for {item_key}: {e}")

        return None

    def export_to_csv(self, papers, filename='papers_metadata.csv'):
        """
        Export paper metadata to CSV file.

        Args:
            papers: List of paper dictionaries
            filename: Output CSV filename
        """
        if not papers:
            self.logger.warning("No papers to export")
            return

        # Get all unique keys from papers
        all_keys = set()
        for paper in papers:
            all_keys.update(paper.keys())

        # Write to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(all_keys))
            writer.writeheader()
            for paper in papers:
                # Convert lists to strings for CSV
                paper_copy = paper.copy()
                if 'authors' in paper_copy:
                    paper_copy['authors'] = '; '.join(paper_copy['authors'])
                if 'tags' in paper_copy:
                    paper_copy['tags'] = '; '.join(paper_copy['tags'])
                writer.writerow(paper_copy)

        self.logger.info(f"Exported {len(papers)} papers to {filename}")


def main():
    """Example usage of ZoteroConnector."""
    import argparse

    parser = argparse.ArgumentParser(description='Retrieve papers from Zotero library')
    parser.add_argument('--collection', help='Collection ID to retrieve from')
    parser.add_argument('--limit', type=int, help='Maximum number of papers to retrieve')
    parser.add_argument('--download-pdfs', action='store_true', help='Download PDF attachments')
    parser.add_argument('--output', default='papers_metadata.csv', help='Output CSV filename')

    args = parser.parse_args()

    # Initialize connector
    connector = ZoteroConnector()

    # Connect to Zotero
    if not connector.connect():
        print("Failed to connect to Zotero. Please check your configuration.")
        return

    # Retrieve papers
    print("Retrieving papers from Zotero...")
    papers = connector.retrieve_papers(
        collection_id=args.collection,
        limit=args.limit
    )

    print(f"Retrieved {len(papers)} papers")

    # Download PDFs if requested
    if args.download_pdfs:
        print("Downloading PDFs...")
        for paper in papers:
            connector.download_pdf(paper['key'])

    # Export to CSV
    connector.export_to_csv(papers, args.output)
    print(f"Metadata exported to {args.output}")


if __name__ == "__main__":
    main()