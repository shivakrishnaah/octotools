import os
import requests
from bs4 import BeautifulSoup
import time

from octotools.tools.base import BaseTool

class AWS_Documentation_Fetcher_Tool(BaseTool):
    def __init__(self):
        super().__init__(
            tool_name="AWS_Documentation_Fetcher_Tool",
            tool_description=(
                "A tool that takes a technology keyword, retrieves AWS documentation, "
                "and suggests equivalent AWS services that can replace the given technology."
            ),
            tool_version="1.0.0",
            input_types={
                "technology": "str - The technology or AWS service to fetch documentation for.",
                "num_pages": "int - The number of documentation pages to fetch (default: 5)."
            },
            output_type="list - A list of dictionaries containing key concepts from AWS documentation.",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(technology="machine learning", num_pages=3)',
                    "description": "Fetch AWS documentation related to machine learning, extracting concepts from up to 3 pages."
                },
            ],
        )
        self.base_url = "https://proxy.search.docs.aws.amazon.com/search"

    def fetch_page(self, technology):
        """
        Fetches a single search result page from AWS documentation.
        """
        request_body = {
            "textQuery":
                {"input":technology},
                "contextAttributes":
                [{"key":"domain","value":"docs.aws.amazon.com"}],
                "acceptSuggestionBody":"RawText","locales":["en_us"]
                }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.post(self.base_url, json=request_body, headers=headers)
        response.raise_for_status()
        return response.json()

    def parse_articles(self, json_response, pages_count):
        """
        Parses the JSON response and extracts key documentation links and descriptions.
        """
        articles = []
        
        for suggestion in json_response.get("suggestions", [])[:pages_count]:
            suggestion_data = suggestion.get("textExcerptSuggestion", {})
            title = suggestion_data.get("title", "No title found")
            url = suggestion_data.get("link", "No URL found")
            description = suggestion_data.get("summary", "No description available")
            
            articles.append({
                'title': title,
                'url': url,
                'description': description
            })
        
        return articles

    def execute(self, technology, num_pages=5):
        """
        Fetches AWS documentation related to the given technology.
        """
        all_articles = []
        
        try:
            json_response = self.fetch_page(technology)
            page_articles = self.parse_articles(json_response, num_pages)
            return page_articles
        except Exception as e:
            return [{"error": str(e)}]

    def get_metadata(self):
        """
        Returns the metadata for AWS_Documentation_Fetcher_Tool.
        """
        metadata = super().get_metadata()
        return metadata

if __name__ == "__main__":
    tool = AWS_Documentation_Fetcher_Tool()
    metadata = tool.get_metadata()
    print(metadata)

    import json
    
    try:
        execution = tool.execute(technology="serverless", num_pages=5)
        print(json.dumps(execution, indent=4))
    except Exception as e:
        print(f"Execution failed: {e}")

    print("Done!")
