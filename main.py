import os
from dotenv import load_dotenv
from searchers import ArxivSearcher, IEEESearcher, ScopusSearcher, WosSearcher, PubmedSearcher, OpenAlexSearcher

def main():
    load_dotenv()
    
    # Define the search query
    query_str = '''("scientific paper*" OR "research paper*" OR "scholarly article*" OR "preprint*" OR "manuscript*" OR "executable paper*" OR "research artifact*") AND ("large language model*" OR "LLM*" OR "generative AI" OR "autonomous*" OR "automatic*" OR "fully automated" OR "automat*" OR "AI agent*" OR "agentic workflow*" OR "reproducib*" OR "replicab*" OR "reproduction" OR "replication" OR "Paper2code") AND ("executable code" OR "environment synthesis" OR "dependency resolution" OR "containerization" OR "Docker*" OR "sandboxing" OR "execution platform*" OR "reproduction package*")'''
    
    # Base output directory
    base_output_dir = "Search Query Results"
    os.makedirs(base_output_dir, exist_ok=True)
    
    # Determine the next query directory
    existing_dirs = [d for d in os.listdir(base_output_dir) if os.path.isdir(os.path.join(base_output_dir, d)) and d.startswith("Query_")]
    max_num = 0
    for d in existing_dirs:
        try:
            num = int(d.split("_")[1])
            if num > max_num:
                max_num = num
        except ValueError:
            pass
            
    query_num = max_num + 1
    output_dir = os.path.join(base_output_dir, f"Query_{query_num}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the query used to summary.txt inside the new folder
    summary_file = os.path.join(output_dir, "summary.txt")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("Search Query Used:\n")
        f.write("-" * 50 + "\n")
        f.write(query_str + "\n")
        f.write("-" * 50 + "\n\n")
    
    # We can add more searchers here in the future
    searchers = [
        ArxivSearcher(),
        # IEEESearcher(),  ---- api key is waiting status
        ScopusSearcher(), 
        # WosSearcher(),   ---- missing api key. it is paid
        PubmedSearcher(),
        OpenAlexSearcher()
    ]
    
    for searcher in searchers:
        print(f"\n--- Running search using {searcher.__class__.__name__} ---")
        
        try:
            # Search the database
            results = searcher.search(query=query_str)
            print(f"{searcher.__class__.__name__} Total results found: {len(results)}")
            
            # Write total count to summary.txt
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write(f"{searcher.__class__.__name__} Results: {len(results)}\n")
            
            # Define output filename based on the searcher class name, inside the new folder
            filename = os.path.join(output_dir, f"{searcher.__class__.__name__.lower()}_results.txt")
            
            # Save results to a text file
            searcher.save_results(filename)
            print(f"Finished writing results to {filename}")
        except Exception as e:
            print(f"Error running {searcher.__class__.__name__}: {e}")
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write(f"{searcher.__class__.__name__} Results: Error ({e})\n")

if __name__ == "__main__":
    main()
