import requests
from .base_searcher import BaseSearcher

class OpenAlexSearcher(BaseSearcher):
    """
    Searcher implementation for the OpenAlex API.
    """
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.openalex.org/works"

    def _format_query(self, query: str) -> str:
        # OpenAlex uses the 'search' parameter for full text / abstract / title search.
        # We replace any unsupported characters or just let the API handle the boolean query.
        return query

    def search(self, query: str, max_results: int = 2000):
        formatted_query = self._format_query(query)
        print(f"OpenAlex formatted query: {formatted_query}")
        
        self.results = []
        page = 1
        per_page = 100
        
        while len(self.results) < max_results:
            params = {
                "search": formatted_query,
                "per-page": per_page,
                "page": page,
                "mailto": "research_bot@example.com" # Be polite
            }
            
            try:
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                print(f"Fetched {len(results)} results on page {page}")
                if not results:
                    break
                    
                self.results.extend(results)
                
                meta = data.get("meta", {})
                total_results = meta.get("count", 0)
                print(f"Total results available: {total_results}")
                
                if len(self.results) >= total_results or len(self.results) >= max_results:
                    break
                    
                page += 1
            except requests.exceptions.RequestException as e:
                print(f"OpenAlex API request failed: {e}")
                break
                
        # Trim to max_results if we overshot
        self.results = self.results[:max_results]
        return self.results

    def _reconstruct_abstract(self, inverted_index):
        if not inverted_index:
            return "No Abstract"
        words = []
        for word, positions in inverted_index.items():
            for pos in positions:
                words.append((pos, word))
        words.sort()
        return " ".join(word for pos, word in words)

    def save_results(self, filename: str):
        if not self.results:
            print("No OpenAlex results to save.")
            return

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Total number of results: {len(self.results)}\n\n")
            f.write("Titles of first 10 papers:\n")
            for i, r in enumerate(self.results[:10]):
                title = r.get('title')
                if not title:
                    title = "No Title"
                # Strip newlines from title
                title = title.replace('\n', ' ')
                f.write(f"{i+1}. {title}\n")
            
            f.write("\n\nFull results details:\n")
            for i, r in enumerate(self.results):
                f.write(f"--- Paper {i+1} ---\n")
                
                title = r.get('title') or r.get('display_name') or 'No Title'
                title = title.replace('\n', ' ')
                f.write(f"Title: {title}\n")
                
                authors = [a.get('author', {}).get('display_name', '') for a in r.get('authorships', [])]
                f.write(f"Authors: {', '.join(authors) if authors else 'Unknown'}\n")
                
                f.write(f"Published: {r.get('publication_date', 'Unknown Date')}\n")
                
                url = r.get('doi') or r.get('id') or "No URL"
                f.write(f"URL: {url}\n")
                
                abstract_index = r.get('abstract_inverted_index', {})
                abstract = self._reconstruct_abstract(abstract_index)
                f.write(f"Summary: {abstract}\n\n")
