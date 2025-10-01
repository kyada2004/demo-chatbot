from googlesearch import search
import requests
from bs4 import BeautifulSoup
# import your AI/ChatGPT model (example using g4f)

# client = Client()

def handle_query(query):
    query_lower = query.lower()

    # --- Case 1: Google Search ---
    if "google search" in query_lower or "search google for" in query_lower or query_lower.startswith("google "):
        return handle_google_search(query)

    # --- Case 2: Normal ChatGPT-like Answer ---
    else:
        # If you have g4f or OpenAI, call it here:
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[{"role": "user", "content": query}]
        # )
        # return {"results": [{"title": "AI Assistant", "link": "#", "snippet": response.choices[0].message.content}]}

        # Fallback: simple dummy answer (replace with AI model in your project)
        return {"results": [{"title": "AI Assistant", "link": "#", "snippet": f"I think you asked: '{query}'. Here is my reasoning-based response."}]}

def handle_google_search(query):
    # Clean query
    search_query = (
        query.lower()
        .replace("google search", "")
        .replace("search google for", "")
        .replace("google", "")
        .strip()
    )

    if not search_query:
        return {"results": []}

    results = []
    try:
        # Fetch top 5 search results
        for url in search(search_query, num_results=5):
            snippet = ""
            try:
                # Fetch page content for snippet
                page = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(page.text, "html.parser")
                snippet = soup.get_text().strip().split("\n")[0][:200]
            except:
                snippet = "No snippet available."

            results.append({
                "title": url.split("//")[-1].split("/")[0],  # Domain as title
                "link": url,
                "snippet": snippet
            })

    except Exception as e:
        results.append({"title": "Error", "link": "#", "snippet": str(e)})

    return {"results": results}
