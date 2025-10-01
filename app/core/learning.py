import sqlite3
import json
from app.core.utils import db_connect
from app.features.ai import get_ai_response

def get_feedback_data():
    """Retrieves all feedback data from the database."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT response_id, user_gmail, rating, conversation_history FROM feedback")
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"[DB Error] {e}")
        return []
    finally:
        if conn:
            conn.close()

def process_negative_feedback():
    """Processes negative feedback and suggests improvements."""
    feedback_data = get_feedback_data()
    suggestions = []

    for response_id, user_gmail, rating, history_json in feedback_data:
        if rating == -1:
            try:
                history = json.loads(history_json)
                if not history:
                    continue

                # The last two messages are the user's query and the assistant's bad response
                user_query = history[-2]['content']
                bad_response = history[-1]['content']

                # Try to generate a better response
                prompt = f"""The user was not satisfied with the following response.
User Query: {user_query}
Bad Response: {bad_response}

Please generate a better, more helpful response to the user's query.
Better Response:"""
                
                # We need the AI brain context for this
                # I will assume a function to load it for now
                from app.core.agent import AIAgent
                # This is not ideal, but for now it will work
                agent = AIAgent(None)
                ai_brain = agent.load_ai_brain()

                good_response = get_ai_response(prompt, history, ai_brain)

                suggestion = {
                    "query": user_query,
                    "bad_response": bad_response,
                    "suggested_response": good_response,
                    "suggestion": f"Consider updating the AI brain to better handle queries like: '{user_query}'"
                }
                suggestions.append(suggestion)

            except Exception as e:
                print(f"[Learning Error] {e}")

    return suggestions

def run_learning_cycle():
    """Runs the full learning cycle and prints suggestions."""
    print("Starting learning cycle...")
    suggestions = process_negative_feedback()
    if suggestions:
        print("\n--- Learning Suggestions ---")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\nSuggestion {i}:")
            print(f"  Query: {suggestion['query']}")
            print(f"  Bad Response: {suggestion['bad_response']}")
            print(f"  Suggested Response: {suggestion['suggested_response']}")
            print(f"  Actionable Advice: {suggestion['suggestion']}")
        print("\n--- End of Suggestions ---")
    else:
        print("No negative feedback to process.")

if __name__ == "__main__":
    # This allows running the learning cycle manually
    run_learning_cycle()
