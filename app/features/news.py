import requests

# TODO: Replace with your NewsAPI.org API key
NEWS_API_KEY = "YOUR_NEWS_API_KEY"

def get_news(topic):
    """Get news articles on a specific topic."""
    if NEWS_API_KEY == "YOUR_NEWS_API_KEY":
        return "Please replace the placeholder NewsAPI key in app/features/news.py"

    url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        articles = data.get("articles", [])
        if not articles:
            return f"I couldn't find any news articles on {topic}."

        # Format the news articles for display
        formatted_articles = []
        for article in articles[:5]:  # Return the top 5 articles
            formatted_articles.append(
                f"- {article['title']}\n  {article['url']}"
            )
        return "\n".join(formatted_articles)

    except requests.exceptions.RequestException as e:
        print(f"[News API Error] {e}")
        return "I encountered an error while trying to fetch the news."
