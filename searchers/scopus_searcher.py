import os
import requests
from .base_searcher import BaseSearcher

class ScopusSearcher(BaseSearcher):
    """
    Searcher implementation for the Scopus (Elsevier) API.
    """
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("SCOPUS_API_KEY")

    def _format_query(self, query: str, subject_area: str = None) -> str:
        # Elsevier Scopus API specifies wrapping search parameters in field restrictors.
        # Use TITLE-ABS-KEY to search within Title, Abstract, and Keywords fields.
        # Scopus natively supports double-quoted loose phrases with asterisks (e.g. "model*").
        # The requests library will properly handle URL-encoding this string.
        formatted_query = f"TITLE-ABS-KEY({query})"
        
        # Add LIMIT-TO (SUBJAREA, ...) logic via standard query string concat
        if subject_area:
            formatted_query += f" AND SUBJAREA({subject_area})"
            
        print(f"Scopus formatted query: {formatted_query}")
        return formatted_query

    def search(self, query: str, max_results: int = 2000, subject_area: str = None):
        if not self.api_key or self.api_key == "your_scopus_api_key_here":
            print("Valid SCOPUS_API_KEY is missing. Cannot perform search.")
            return []

        url = "https://api.elsevier.com/content/search/scopus"
        self.results = []
        start = 0
        
        headers = {
            "Accept": "application/json",
            "X-ELS-APIKey": self.api_key
        }
        
        formatted_query = self._format_query(query, subject_area)
        
        while len(self.results) < max_results:
            fetch_size = min(25, max_results - len(self.results))
            
            params = {
                "query": formatted_query,
                "count": fetch_size,
                "start": start
            }
            
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                search_results = data.get('search-results', {})
                entries = search_results.get('entry', [])
                
                if not entries:
                    break
                    
                self.results.extend(entries)
                
                total_results_str = search_results.get('opensearch:totalResults', '0')
                total_results = int(total_results_str) if total_results_str.isdigit() else 0
                
                if len(self.results) >= total_results:
                    break
                    
                start += len(entries)
                
            except requests.exceptions.RequestException as e:
                print(f"Scopus API request failed: {e}")
                if response is not None:
                    print(response.text)
                break
                
        return self.results

    def save_results(self, filename: str):
        if not self.results:
            print("No Scopus results to save.")
            return

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Total number of results: {len(self.results)}\n\n")
            f.write("Titles of first 10 papers:\n")
            for i, r in enumerate(self.results[:10]):
                f.write(f"{i+1}. {r.get('dc:title', 'No Title')}\n")
            
            f.write("\n\nFull results details:\n")
            for i, r in enumerate(self.results):
                f.write(f"--- Paper {i+1} ---\n")
                f.write(f"Title: {r.get('dc:title', 'No Title')}\n")
                f.write(f"Authors: {r.get('dc:creator', 'Unknown')}\n")
                f.write(f"Published: {r.get('prism:coverDate', 'Unknown Date')}\n")
                f.write(f"Journal: {r.get('prism:publicationName', 'Unknown')}\n")
                f.write(f"DOI: {r.get('prism:doi', 'No DOI')}\n")
                
                # Scopus links exist as a list
                links = r.get('link', [])
                url = "No URL"
                if isinstance(links, list) and len(links) > 0:
                    for link in links:
                        # try to get the scopus generic link
                        if link.get('@ref') == 'scopus':
                            url = link.get('@href', url)
                            break
                            
                f.write(f"URL: {url}\n")
                f.write(f"Summary: {r.get('dc:description', 'No Summary provided in search results.')}\n\n")
