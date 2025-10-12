#!/usr/bin/env python
"""
Research Paper Meta-Analysis Tool
Analyzes academic papers for specific research criteria using OpenAI GPT models.

Author: Zachary Fried
"""

import pandas as pd
import sqlalchemy
from openai import OpenAI
import configparser
import os
import time
from tqdm import tqdm
import argparse


class ResearchPaperAnalyzer:
    """
    Analyzes research papers to determine if they meet specific inclusion criteria
    for meta-analysis studies.
    """

    def __init__(self, database_name, port_number=3306):
        """
        Initialize the analyzer with database configuration.

        Args:
            database_name: Name of the MySQL database
            port_number: Port for MySQL connection (default: 3306)
        """
        self.database_name = database_name
        self.port_number = port_number
        self.questions = self._initialize_questions()

    def _initialize_questions(self):
        """Define the research questions for paper evaluation."""
        return [
            {"main": "Placeholder for 0 index, do not use me.", "follow_up": None},
            {
                "main": "Does this paper focus on studies or experiments involving human adults who are, either explicitly stated or likely, aged 18 or older? Respond with '1' for yes and '0' for no.",
                "follow_up": "State the demographics of the human subjects in this paper briefly."
            },
            {
                "main": "Based on the study described in the paper, determine if it is an empirical study. If it is an empirical study, respond with '1'. If it is not an empirical study, respond with '0'.",
                "follow_up": None
            },
            {
                "main": "Respond with just a '0' if the study/methods in this paper are purely qualitative, respond with a '1' if the study/methods in this paper are quantitative, respond with just a '2' if the study/methods in this paper include a mix between quantitative and qualitative methods.",
                "follow_up": None
            },
            {
                "main": "Considering measures such as the UCLA Loneliness Scale, De-Jong Giervald Scale, single questions about loneliness, and perceptions of social isolation, does this paper specifically focus on variables directly related to loneliness? Respond with '1' for yes and '0' for no.",
                "follow_up": "List the specific loneliness-related variables or measures mentioned in the paper, such as the UCLA Loneliness Scale, De-Jong Giervald Scale, or others. Use bullet points for each item."
            },
            {
                "main": "Does this paper include any variables or measures related to alcohol use? Respond with '1' for yes and '0' for no.",
                "follow_up": "List the specific alcohol use-related variables or measures mentioned in the paper, such as AUDIT, RAPI, TLFB, biological tests, or other variables/measures of alcohol use. Use bullet points for each item."
            },
            {
                "main": "Does the paper specifically examine the relationship between loneliness and alcohol use? Respond with '1' for yes and '0' for no.",
                "follow_up": "Briefly describe the nature of the relationship(s) between loneliness and alcohol use as examined in the paper."
            }
        ]

    def read_configurations(self):
        """
        Read database and OpenAI configuration from config files.

        Returns:
            Tuple of (mysql_config, openai_config) dictionaries
        """
        config = configparser.ConfigParser()

        # Read MySQL configuration (expects ~/.my.cnf file)
        config.read(os.path.expanduser('~/.my.cnf'))
        mysql_config = {
            'username': config.get('client', 'user', fallback='root'),
            'password': config.get('client', 'password', fallback=''),
            'host': config.get('client', 'host', fallback='localhost')
        }

        # Read OpenAI configuration (expects config.ini in current directory)
        config.read('config.ini')
        if 'openai' in config:
            openai_config = {'api_key': config['openai']['key']}
        else:
            # Allow environment variable as fallback
            openai_config = {'api_key': os.getenv('OPENAI_API_KEY', '')}

        return mysql_config, openai_config

    def connect_to_database(self, mysql_config):
        """
        Establish connection to MySQL database.

        Args:
            mysql_config: Dictionary with database credentials

        Returns:
            SQLAlchemy engine object
        """
        connection_string = (
            f"mysql+pymysql://{mysql_config['username']}:{mysql_config['password']}"
            f"@{mysql_config['host']}:{self.port_number}/{self.database_name}"
        )
        return sqlalchemy.create_engine(connection_string)

    def ask_gpt(self, client, question, paper_text, max_tokens=100):
        """
        Query GPT model with a question about a paper.

        Args:
            client: OpenAI client instance
            question: The question to ask
            paper_text: The paper content
            max_tokens: Maximum tokens in response

        Returns:
            String response from GPT
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert in analyzing and summarizing academic research papers. Pay close attention to the age, methodology, and subject matter of the studies."},
                    {"role": "user", "content": paper_text},
                    {"role": "user", "content": question}
                ],
                temperature=0.3,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error querying GPT: {e}")
            return "Error"

    def evaluate_paper(self, client, paper_content):
        """
        Evaluate a single paper against all criteria.

        Args:
            client: OpenAI client instance
            paper_content: Text content of the paper

        Returns:
            Dictionary with evaluation results
        """
        results = {
            'included_in_final_decision': 'No',
            'reason_excluded': '',
            'q1_human_subjects': '',
            'q1_notes': '',
            'q2_empirical_study': '',
            'q3_qualitative': '',
            'q4_loneliness_variables': '',
            'q4_notes': '',
            'q5_alcohol_variables': '',
            'q5_notes': '',
            'q6_loneliness_alcohol_relationship': '',
            'q6_notes': ''
        }

        # Q1: Human adult subjects
        response = self.ask_gpt(client, self.questions[1]["main"], paper_content, max_tokens=20)
        if '1' in response:
            results['q1_human_subjects'] = 'Yes'
            follow_up = self.ask_gpt(client, self.questions[1]["follow_up"], paper_content)
            results['q1_notes'] = follow_up
        elif '0' in response:
            results['q1_human_subjects'] = 'No'
            results['reason_excluded'] = 'Subjects not human adults'
            return results

        # Q2: Empirical study
        response = self.ask_gpt(client, self.questions[2]["main"], paper_content, max_tokens=20)
        if '1' in response:
            results['q2_empirical_study'] = 'Yes'
        elif '0' in response:
            results['q2_empirical_study'] = 'No'
            results['reason_excluded'] = 'Not an empirical study'
            return results

        # Q3: Study type
        response = self.ask_gpt(client, self.questions[3]["main"], paper_content, max_tokens=20)
        if '2' in response:
            results['q3_qualitative'] = 'Mixed methods'
        elif '1' in response:
            results['q3_qualitative'] = 'Quantitative'
        elif '0' in response:
            results['q3_qualitative'] = 'Purely qualitative'
            results['reason_excluded'] = 'Study is purely qualitative'
            return results

        # Q4: Loneliness variables
        response = self.ask_gpt(client, self.questions[4]["main"], paper_content, max_tokens=20)
        if '1' in response:
            results['q4_loneliness_variables'] = 'Yes'
            follow_up = self.ask_gpt(client, self.questions[4]["follow_up"], paper_content)
            results['q4_notes'] = follow_up
        elif '0' in response:
            results['q4_loneliness_variables'] = 'No'
            results['reason_excluded'] = 'No loneliness variables'
            return results

        # Q5: Alcohol variables
        response = self.ask_gpt(client, self.questions[5]["main"], paper_content, max_tokens=20)
        if '1' in response:
            results['q5_alcohol_variables'] = 'Yes'
            follow_up = self.ask_gpt(client, self.questions[5]["follow_up"], paper_content)
            results['q5_notes'] = follow_up
        elif '0' in response:
            results['q5_alcohol_variables'] = 'No'
            results['reason_excluded'] = 'No alcohol variables'
            return results

        # Q6: Loneliness-alcohol relationship
        response = self.ask_gpt(client, self.questions[6]["main"], paper_content, max_tokens=20)
        if '1' in response:
            results['q6_loneliness_alcohol_relationship'] = 'Yes'
            follow_up = self.ask_gpt(client, self.questions[6]["follow_up"], paper_content)
            results['q6_notes'] = follow_up
            results['included_in_final_decision'] = 'Yes'
            results['reason_excluded'] = ''
        elif '0' in response:
            results['q6_loneliness_alcohol_relationship'] = 'No'
            results['reason_excluded'] = 'No loneliness-alcohol relationship examined'

        return results

    def process_papers(self, engine, client, table_name='papers'):
        """
        Process all papers in the database.

        Args:
            engine: SQLAlchemy database engine
            client: OpenAI client instance
            table_name: Name of the table containing papers

        Returns:
            DataFrame with evaluation results
        """
        # Fetch papers from database
        papers = pd.read_sql(f"SELECT * FROM {table_name}", engine)

        # Initialize results columns
        question_columns = [
            'included_in_final_decision', 'reason_excluded',
            'q1_human_subjects', 'q1_notes', 'q2_empirical_study',
            'q3_qualitative', 'q4_loneliness_variables', 'q4_notes',
            'q5_alcohol_variables', 'q5_notes',
            'q6_loneliness_alcohol_relationship', 'q6_notes'
        ]

        for column in question_columns:
            papers[column] = ''

        # Process each paper
        for index, paper in tqdm(papers.iterrows(), total=papers.shape[0], desc="Processing papers"):
            print(f"Analyzing: {paper.get('title', 'Unknown Title')}")

            # Get paper content (assuming it's in a column called 'content' or 'pdf_content')
            content = paper.get('content', paper.get('pdf_content', ''))

            if not content:
                papers.at[index, 'reason_excluded'] = 'No content available'
                continue

            # Evaluate the paper
            results = self.evaluate_paper(client, content)

            # Update dataframe with results
            for key, value in results.items():
                papers.at[index, key] = value

            # Rate limiting to avoid API throttling
            time.sleep(1)

        return papers


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Analyze research papers for meta-analysis inclusion criteria.'
    )
    parser.add_argument(
        '--database',
        required=True,
        help='MySQL database name'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=3306,
        help='MySQL port number (default: 3306)'
    )
    parser.add_argument(
        '--output',
        default='evaluated_papers.csv',
        help='Output CSV filename (default: evaluated_papers.csv)'
    )
    parser.add_argument(
        '--table',
        default='papers',
        help='Database table name (default: papers)'
    )

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = ResearchPaperAnalyzer(args.database, args.port)

    # Read configurations
    mysql_config, openai_config = analyzer.read_configurations()

    if not openai_config.get('api_key'):
        print("Error: OpenAI API key not found in config.ini or environment variables")
        return

    # Connect to database
    try:
        engine = analyzer.connect_to_database(mysql_config)
        print(f"Connected to database: {args.database}")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return

    # Initialize OpenAI client
    client = OpenAI(api_key=openai_config['api_key'])

    # Process papers
    results_df = analyzer.process_papers(engine, client, args.table)

    # Save results
    results_df.to_csv(args.output, index=False)
    print(f"Results saved to: {args.output}")

    # Print summary
    included = results_df[results_df['included_in_final_decision'] == 'Yes'].shape[0]
    excluded = results_df[results_df['included_in_final_decision'] == 'No'].shape[0]
    print(f"\nSummary:")
    print(f"  Papers included: {included}")
    print(f"  Papers excluded: {excluded}")
    print(f"  Total processed: {included + excluded}")


if __name__ == "__main__":
    main()