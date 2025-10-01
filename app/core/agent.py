import asyncio
import re
import datetime
import tkinter as tk
import webbrowser
import os
import spacy
from langdetect import detect
from deep_translator import GoogleTranslator
from transformers import pipeline

from app.features.weather import handle_weather_query
from app.features.ai import get_ai_response
from app.features.image_generate import generate_image

from app.features.greetme import greetMe
from app.features.google_search import handle_google_search
from app.features.rag import RAG

from app.features.calendar import set_reminder, show_reminders, delete_reminder
from app.features.trip_planner import plan_trip
from app.features.news import get_news
from app.features.stock import get_stock_price
from app.database.preferences import get_user_preference, set_user_preference
from app.database.goals import add_goal, get_active_goals, update_goal_status
from app.database.tasks import add_task, get_pending_tasks, update_task_status
from app.database.chat_history import add_last_query, get_last_queries
from app.core.planner import PlanningEngine
from app.core.safety import is_content_safe
from app.features.web_research import scrape_and_store_url, query_web_content

class AIAgent:
    def __init__(self, app, rag_instance: RAG):
        self.app = app
        self.rag = rag_instance
        self.nlp = spacy.load("en_core_web_sm")
        self.ai_brain_context = self.load_ai_brain()
        self.planner = PlanningEngine(self)
        self.trip_plan_details = {}
        self.user_preferences = {}
        self.conversation_context = None
        self.intent_routes = {
            "greet": {
                "handler": self.handle_greet,
                "description": "Responds to user greetings.",
                "args": {}
            },
            "get_time": {
                "handler": self.handle_get_time,
                "description": "Gets the current time.",
                "args": {}
            },
            "reset_chat": {
                "handler": self.handle_reset_chat,
                "description": "Resets the chat history.",
                "args": {}
            },
            "stop_speech": {
                "handler": self.handle_stop_speech,
                "description": "Stops the text-to-speech output.",
                "args": {}
            },
            "weather": {
                "handler": self.handle_weather,
                "description": "Gets the weather for a specified city.",
                "args": {"city": "The city to get the weather for."}
            },
            "google_search": {
                "handler": self.handle_google_search,
                "description": "Performs a Google search for a given query.",
                "args": {"query": "The search query."}
            },
            "show_reminders": {
                "handler": self.handle_show_reminders,
                "description": "Shows all active reminders.",
                "args": {}
            },
            "get_news": {
                "handler": self.handle_get_news,
                "description": "Gets news about a specific topic.",
                "args": {"topic": "The topic to get news about."}
            },
            "get_stock_price": {
                "handler": self.handle_get_stock_price,
                "description": "Gets the stock price for a given symbol.",
                "args": {"symbol": "The stock symbol."}
            },
            "file_query": {
                "handler": self.handle_file_query,
                "description": "Queries the content of an uploaded file.",
                "args": {"query": "The query to ask the file."}
            },
            "research_and_summarize": {
                "handler": self.handle_research_and_summarize,
                "description": "Researches a topic online and provides a summary.",
                "args": {"topic": "The topic to research."}
            },
            "research_webpage": {
                "handler": self.handle_research_webpage,
                "description": "Scrapes and stores the content of a webpage.",
                "args": {"url": "The URL of the webpage to research."}
            },
            "show_goals": {
                "handler": self.handle_show_goals,
                "description": "Shows the user's active goals.",
                "args": {}
            },
            "get_user_details": {
                "handler": self.handle_get_user_details,
                "description": "Gets the current user's details.",
                "args": {}
            },
            "show_tasks": {
                "handler": self.handle_show_tasks,
                "description": "Shows the user's pending tasks.",
                "args": {}
            },
            "generate_image": {
                "handler": self.handle_image_generation,
                "description": "Generates an image based on a prompt.",
                "args": {"prompt": "The prompt for image generation."}
            },
            "open_website": {
                "handler": self.handle_open_website,
                "description": "Opens a website in the default browser.",
                "args": {"url": "The URL of the website to open."}
            },
            "close_website": {
                "handler": self.handle_close_website,
                "description": "Closes the browser.",
                "args": {}
            },
            "set_reminder": {
                "handler": self.handle_set_reminder,
                "description": "Sets a reminder for the user.",
                "args": {"message": "The reminder message.", "time": "The time for the reminder."}
            },
            "delete_reminder": {
                "handler": self.handle_delete_reminder,
                "description": "Deletes a reminder by its ID.",
                "args": {"reminder_id": "The ID of the reminder to delete."}
            },
            "plan_trip": {
                "handler": self.handle_plan_trip,
                "description": "Plans a trip for the user.",
                "args": {}
            },
            "set_language": {
                "handler": self.handle_set_language,
                "description": "Sets the user's preferred language.",
                "args": {"language": "The language to set."}
            },
            "set_tone": {
                "handler": self.handle_set_tone,
                "description": "Sets the user's preferred tone.",
                "args": {"tone": "The tone to set."}
            },
            "set_default_city": {
                "handler": self.handle_set_default_city,
                "description": "Sets the user's default city for weather forecasts.",
                "args": {"city": "The default city."}
            },
            "set_interests": {
                "handler": self.handle_set_interests,
                "description": "Sets the user's interests.",
                "args": {"interests": "The user's interests."}
            },
            "set_goal": {
                "handler": self.handle_set_goal,
                "description": "Sets a new goal for the user.",
                "args": {"goal_description": "The description of the goal."}
            },
            "complete_goal": {
                "handler": self.handle_complete_goal,
                "description": "Marks a goal as complete.",
                "args": {"goal_id": "The ID of the goal to complete."}
            },
            "abandon_goal": {
                "handler": self.handle_abandon_goal,
                "description": "Abandons a goal.",
                "args": {"goal_id": "The ID of the goal to abandon."}
            },
            "send_email": {
                "handler": self.handle_send_email,
                "description": "Sends an email to a recipient.",
                "args": {"recipient": "The email recipient."}
            },
            "add_task": {
                "handler": self.handle_add_task,
                "description": "Adds a new task.",
                "args": {"task_description": "The description of the task."}
            },
            "complete_task": {
                "handler": self.handle_complete_task,
                "description": "Marks a task as complete.",
                "args": {"task_id": "The ID of the task to complete."}
            }
        }

    def load_ai_brain(self):
        try:
            with open("ai_brain.md", "r") as f:
                return f.read()
        except FileNotFoundError:
            print("[Warning] ai_brain.md not found.")
            return "You are a helpful AI assistant named Jenny."

    async def process_query(self, query, response_queue):
        query = query.strip()
        safe, message = is_content_safe(query)
        if not safe:
            response_queue.put(message)
            response_queue.put(None)
            return

        if self.app.current_user:
            add_last_query(self.app.current_user['gmail'], query)

        await self.planner.execute_plan(query, response_queue)
    
    def handle_send_email(self, entities):
        # Placeholder for sending email
        recipient = entities.get("recipient")
        if not recipient:
            return "Please specify a recipient for the email."
        return f"I will send an email to {recipient}. What should be the subject and body?"

    def handle_get_stock_price(self, entities):
        symbol = entities.get("symbol")
        if not symbol:
            return "Please specify a stock symbol to get the price for."
        return get_stock_price(symbol)

    def handle_get_news(self, entities):
        topic = entities.get("topic")
        if not topic:
            return "Please specify a topic to get news about."
        return get_news(topic)

    def handle_set_language(self, entities):
        language = entities.get("language")
        if not self.app.current_user:
            return "Please login to set your language."
        if language:
            set_user_preference(self.app.current_user['gmail'], 'language', language)
            self.user_preferences['language'] = language
            return f"Your language has been set to {language}."
        return "I didn't understand the language. Please try again."

    def handle_set_tone(self, entities):
        tone = entities.get("tone")
        if not self.app.current_user:
            return "Please login to set your tone."
        if tone:
            set_user_preference(self.app.current_user['gmail'], 'tone', tone)
            self.user_preferences['tone'] = tone
            return f"Your tone has been set to {tone}."
        return "I didn't understand the tone. Please try again."

    def handle_greet(self, entities):
        return greetMe()

    def handle_get_time(self, entities):
        time_str = f"The time is {datetime.datetime.now().strftime('%H:%M:%S')}"
        return time_str

    def handle_reset_chat(self, entities):
        self.app.chat_area.configure(state="normal")
        self.app.chat_area.delete("1.0", tk.END)
        self.app.chat_area.configure(state="disabled")
        self.app.message_history = []
        return "Chat has been reset."

    def handle_stop_speech(self, entities):
        self.app.stop_speech()
        return "Speech stopped."

    def handle_weather(self, entities):
        city = entities.get("city")
        if not city and self.app.current_user:
            city = get_user_preference(self.app.current_user['gmail'], 'default_city')

        if not city:
            self.conversation_context = "AWAITING_CITY_FOR_WEATHER"
            return "Which city would you like the weather for?"

        weather_response = handle_weather_query(f"weather in {city}")
        return weather_response

    def handle_image_generation(self, entities):
        prompt = entities.get("prompt")
        if not prompt:
            return "Please specify what you want to generate."
        return self.app.handle_image_generation(prompt)

    def handle_open_website(self, entities):
        url = entities.get("url")
        if not url:
            return "Please specify a website to open."
        if '.' not in url:
            url = f"https://www.{url}.com"
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        webbrowser.open(url)
        return f"Opening {url}"

    def handle_close_website(self, entities):
        os.system("taskkill /f /im chrome.exe")
        return "All browser windows closed."

    async def handle_file_query(self, entities, response_queue):
        query = entities.get("query")
        if not query:
            response_queue.put("Please specify what you want to ask about the file.")
            response_queue.put(None)
            return
        
        retrieved_chunks = self.rag.retrieve_context(query)
        if retrieved_chunks:
            context = "\n\n".join(retrieved_chunks)
            rag_context = f"Context from uploaded files:\n{context}"
            response_generator = get_ai_response(query, self.app.message_history, self.ai_brain_context, stream=True, rag_context=rag_context)
            async for chunk in response_generator:
                response_queue.put(chunk)
            response_queue.put(None)
        else:
            response_queue.put("I couldn't find any relevant information in the uploaded files.")
            response_queue.put(None)

    async def handle_google_search(self, entities, response_queue):
        query = entities.get("query")
        if not query:
            response_queue.put("Please specify what you want to search for.")
            response_queue.put(None)
            return
        
        search_results = handle_google_search(query)
        
        prompt = f"Based on the following search results, please answer the user's query: '{query}'\n\nSearch Results:\n{search_results}"
        
        response_generator = get_ai_response(prompt, self.app.message_history, self.ai_brain_context, stream=True)
        async for chunk in response_generator:
            response_queue.put(chunk)
        response_queue.put(None)

    def handle_set_reminder(self, entities):
        message = entities.get("message")
        time_str = entities.get("time")
        if message and time_str:
            return set_reminder(message, time_str)
        return "Please provide the reminder message and time."

    def handle_show_reminders(self, entities):
        return show_reminders()

    def handle_delete_reminder(self, entities):
        reminder_id = entities.get("reminder_id")
        if reminder_id:
            return delete_reminder(reminder_id)
        return "Please provide the reminder ID to delete."

    async def handle_research_and_summarize(self, entities, response_queue):
        topic = entities.get("topic")
        if not topic:
            response_queue.put("Please specify a topic to research and summarize.")
            response_queue.put(None)
            return

        self.app.respond(f"Researching and summarizing: {topic}...")

        try:
            # Step 1: Google Search
            search_results = handle_google_search(query=topic)
            
            if not search_results or not search_results.get('results'):
                response_queue.put("I couldn't find any information on that topic.")
                response_queue.put(None)
                return

            # Step 2: Scrape and store the top result
            top_result_url = search_results['results'][0]['link']
            scrape_result = scrape_and_store_url(top_result_url)
            self.app.respond(scrape_result) # Inform the user about the scraping result

            # Step 3: Query the scraped content
            retrieved_content = query_web_content(topic)
            
            summary_prompt = ""
            if "Error" in retrieved_content or "couldn't find" in retrieved_content:
                # Fallback to summarizing the original search result if scraping failed or no content found
                summary_prompt = f"Summarize the content of the page {top_result_url}"
            else:
                # Summarize the retrieved content from our vector store
                summary_prompt = f"Summarize the following text:\n{retrieved_content}"
            
            summary_response = await get_ai_response(summary_prompt, self.app.message_history, self.ai_brain_context, stream=False)
            summary = summary_response.get('text', '')
            response_queue.put(summary)
            response_queue.put(None)

        except Exception as e:
            print(f"[Research Error] {e}")
            response_queue.put("I encountered an error while trying to research and summarize the topic.")
            response_queue.put(None)

    def handle_research_webpage(self, entities):
        url = entities.get("url")
        if not url:
            return "Please provide a URL to research."
        
        result = scrape_and_store_url(url)
        return result

    def handle_plan_trip(self, entities):
        if not self.trip_plan_details.get('destination'):
            self.conversation_context = "AWAITING_TRIP_DESTINATION"
            return "Where would you like to go?"
        
        destination = self.trip_plan_details.get('destination')
        duration = self.trip_plan_details.get('duration')
        interests = self.trip_plan_details.get('interests')
        trip_type = self.trip_plan_details.get('trip_type')

        self.app.respond(f"Planning your {duration}-day {trip_type} trip to {destination} with interests in {', '.join(interests)}...")
        
        # Perform the Google search here
        search_query = f"top attractions, restaurants, and local transportation in {destination} for a {trip_type} trip with interests in {', '.join(interests)}"
        search_results = self.handle_google_search({"query": search_query}) # Call the agent's handle_google_search
        
        itinerary = plan_trip(destination, duration, interests, trip_type, search_results)
        
        self.trip_plan_details = {} # Reset for next time
        
        return itinerary

    def handle_set_default_city(self, entities):
        city = entities.get("city")
        if not self.app.current_user:
            return "Please login to set a default city."
        if city:
            set_user_preference(self.app.current_user['gmail'], 'default_city', city)
            return f"Your default city has been set to {city}."
        return "I didn't understand the city name. Please try again."

    def handle_set_interests(self, entities):
        interests = entities.get("interests")
        if not self.app.current_user:
            return "Please login to set your interests."
        if interests:
            set_user_preference(self.app.current_user['gmail'], 'interests', interests)
            return f"Your interests have been set to {interests}."
        return "I didn't understand your interests. Please try again."

    def handle_set_goal(self, entities):
        goal_description = entities.get("goal_description")
        if not self.app.current_user:
            return "Please login to set a goal."
        if not goal_description:
            return "Please provide a description for your goal."
        
        return add_goal(self.app.current_user['gmail'], goal_description)

    def handle_show_goals(self, entities):
        if not self.app.current_user:
            return "Please login to view your goals."
        
        active_goals = get_active_goals(self.app.current_user['gmail'])
        if not active_goals:
            return "You have no active goals."
        
        response = "Your active goals:\n"
        for goal_id, desc, status in active_goals:
            response += f"- ID: {goal_id}, Goal: {desc}\n"
        return response

    def handle_complete_goal(self, entities):
        goal_id = entities.get("goal_id")
        if not self.app.current_user:
            return "Please login to manage your goals."
        if not goal_id:
            return "Please provide the ID of the goal to complete."
        
        return update_goal_status(goal_id, 'completed')

    def handle_abandon_goal(self, entities):
        goal_id = entities.get("goal_id")
        if not self.app.current_user:
            return "Please login to manage your goals."
        if not goal_id:
            return "Please provide the ID of the goal to abandon."
        
        return update_goal_status(goal_id, 'abandoned')

    def handle_add_task(self, entities):
        task_description = entities.get("task_description")
        if not self.app.current_user:
            return "Please login to add a task."
        if not task_description:
            return "Please provide a description for your task."
        
        return add_task(self.app.current_user['gmail'], task_description)

    def handle_show_tasks(self, entities):
        if not self.app.current_user:
            return "Please login to view your tasks."
        
        pending_tasks = get_pending_tasks(self.app.current_user['gmail'])
        if not pending_tasks:
            return "You have no pending tasks."
        
        response = "Your pending tasks:\n"
        for task_id, desc, due_date in pending_tasks:
            response += f"- ID: {task_id}, Task: {desc}, Due: {due_date or 'N/A'}\n"
        return response

    def handle_complete_task(self, entities):
        task_id = entities.get("task_id")
        if not self.app.current_user:
            return "Please login to manage your tasks."
        if not task_id:
            return "Please provide the ID of the task to complete."
        
        return update_task_status(task_id, 'completed')

    def load_user_preferences(self, user_gmail):
        self.user_preferences = {
            'language': get_user_preference(user_gmail, 'language') or 'en',
            'tone': get_user_preference(user_gmail, 'tone') or 'neutral',
        }

    def handle_get_user_details(self, entities):
        if not self.app.current_user:
            return "You are not logged in. Please log in to see your details."
        
        user_details = self.app.current_user
        response = f"Here are your details:\n"
        response += f"- First Name: {user_details.get('first_name')}\n"
        response += f"- Last Name: {user_details.get('last_name')}\n"
        response += f"- Email: {user_details.get('gmail')}"
        return response
