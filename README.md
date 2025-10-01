# Generative AI Chatbot / Proactive Desktop Assistant

This is a desktop chatbot application with proactive capabilities, powered by generative AI.

## Features

- **Conversational AI:** Chat with a helpful AI assistant.
- **Image Generation:** Create images from text prompts.
- **File Analysis:** Ask questions about your uploaded documents.
- **Web Research:** Ask the AI to research topics on the web.
- **Conversation History:** Your conversations are saved and can be reviewed later.
- **User Authentication:** Secure login and registration system.
- **Rate Limiting:** Prevents abuse of the application.
- **Content Moderation:** Filters out inappropriate content.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```

2.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**

    ```bash
    python run.py
    ```

## Usage

-   **Chat:** Type your message in the input box and press Enter.
-   **Generate Image:** Type "generate image [prompt]" to create an image.
-   **Upload File:** Click the "Upload" button to upload a file for analysis.
-   **Voice Command:** Click the microphone button to issue voice commands.

## Data Flow

The application follows a clear data flow to process user queries and generate responses:

1.  **Input Handling (`app/core/input_handler.py`):**
    -   The user's raw input (from text or voice) is first sanitized to prevent any malicious script injections.
    -   The sanitized text is then run through a spell checker to correct any mistakes.
    -   Finally, a content safety check is performed to ensure the query complies with safety guidelines.

2.  **Intent Detection (`app/core/planner.py`):**
    -   The processed query is passed to the `PlanningEngine`.
    -   The planner uses a large language model (LLM) to analyze the query and understand the user's intent.
    -   It then creates a step-by-step plan by selecting the appropriate tools (e.g., `weather`, `google_search`, `file_query`) to fulfill the request.

3.  **Decision (Core Logic) (`app/core/agent.py` & `app/core/planner.py`):**
    -   The `PlanningEngine` executes the generated plan.
    -   It calls the corresponding handler function for each tool in the plan, passing the necessary arguments extracted from the query.
    -   If no specific tool is required (e.g., for a general conversational question), the query is sent to a general-purpose AI model for a response.

4.  **Response Generation:**
    -   The output from the executed tool or the AI model is formatted into a user-friendly response.

5.  **Output to User:**
    -   The final response is displayed in the chat window.
    -   If speech is enabled, the response is also converted to audio and played.

6.  **Database Storage (`app/database/`):**
    -   The conversation (both user query and assistant response) is saved to the database for history and feedback purposes.

## Docker

1.  **Build and run the containers:**

    ```bash
    docker-compose up -d --build
    ```

2.  **View the logs:**

    ```bash
    docker-compose logs -f
    ```
