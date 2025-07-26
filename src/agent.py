import logging
import os
from dotenv import load_dotenv

from quart import Quart, request, jsonify, Response
from quart_cors import cors

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.genai.types import Content, Part
from google.adk.sessions import InMemorySessionService
from sub_agents.research_administrator.agent import research_administrator_agent
from sub_agents.database_manager import database_manager_agent

MODEL = "gemini-2.0-flash"

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Ensure GEMINI_API_KEY is loaded and accessible in os.environ
# Use GOOGLE_API_KEY as the primary key name for broader compatibility with Google libraries
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    logging.error(
        "API_KEY not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file."
    )
    exit(1)  # Exit if no API key is found


main_coordinator_agent = LlmAgent(
    name="main_coordinator_agent",
    model=MODEL,
    description="The Research Lifecycle Management Assistant. It collaborates with the user to support different phases of research administration.",
    instruction="""
    You are a research lifecycle management assistant. Your primary function is to support ANY user in their research process and distribute tasks to respective agents. 
    You should be able to support both research administrators and principal investigators in their tasks.

    **CRITICAL RULE: Never answer a question directly or refuse a request.** Your one and only first step is to assign tasks to specialized agents to achieve the goals set by the user.
    If the user asks a question, you MUST try to identify what the user tries to achieve.

    IMPORTANT: Always start your very first response with a friendly greeting.
    For example: "Hello! I'm here to help. What can I do for you today?"
    
    Any requests related to listing, updating, deleting or creating data should be delegated to the `database_manager_agent`. Show the results from `database_manager_agent` in a table format if possible.
    
    Any requests related to funding opportunities and funding eligibility should be delegated to the `research_administrator_agent`.
    
    Examples of personalized greetings based on session context:
    - If `session.state.role` is "investigator":
      "Welcome {name}! I'm ready to help with your research projects."
    - If `session.state.role` is "research_administrator":
      "Welcome {name}! How can I help you with your research administration tasks today."
    - If `session.state.role` is not yet determined:
      "Welcome {name}! I'm ready to help with your tasks today."
      
    If the user asks to select a specific agent, you should transfer the conversation to that agent.

    
    Your workflow is:
    1. **Greeting:** Start with a friendly greeting.
    2. **Assign:** Assign the task user wants to achieve to respective agent.
    3. **Respond:** Respond that the task is assigned and show the result if received.
    4. **Conclusion:** Briefly conclude the interaction, perhaps asking if the user wants to complete any other task today.

    Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
    Do not perform any research yourself. Your job is to Delegate to the right agent.
    """,
    sub_agents=[
        research_administrator_agent,
        database_manager_agent,
        # principal_investigator_agent,
        # research_finance_administrator_agent,
        # college_administrator_agent,
        # irb_agent,
    ],
    tools=[],
    output_key="task_assignment",
)

root_agent = main_coordinator_agent

session_service = InMemorySessionService()
# session_service = DatabaseSessionService(db_url="sqlite:///./adk_sessions.db")
APP_NAME = "research"
runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)

app = Quart(__name__)
app = cors(app, allow_origin="*")


# --- Endpoint for Chat ---
@app.route("/chat", methods=["POST"])
async def chat_with_agent():
    data = await request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    print(data)
    user_id = data.get("user_id")
    session_id = data.get("session_id")
    message_text = data.get("message")
    role = data.get("role", "investigator")  # Default to investigator if not provided

    if not all([user_id, session_id, message_text]):
        return jsonify({"error": "Missing user_id, session_id, or message"}), 400

    # Get or create session
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    if not session:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
            state={"name": user_id, "role": role},
        )

    user_message = Content(role="user", parts=[Part(text=message_text)])
    logging.info(f"User message: {user_message.parts[0].text}")

    # Using stream_with_context for streaming responses (recommended for chat)
    async def generate_responses():
        try:
            async for event in runner.run_async(
                user_id=user_id, session_id=session_id, new_message=user_message
            ):
                logging.info(f"Event received: {event}")
                if getattr(event, "error_code", None):
                    logging.error(
                        f"Agent error: {event.error_code} - {getattr(event, 'error_message', '')}"
                    )
                    yield f"data: [Sorry I encountered an error: {event.error_code} - {getattr(event, 'error_message', 'No error message provided')}]\\n\\n"
                    continue

                if event.is_final_response():
                    if (
                        event.content
                        and event.content.parts
                        and event.content.parts[0].text
                    ):
                        response_text = event.content.parts[0].text
                        yield f"data: {response_text}\n\n"  # Server-Sent Events format
                        logging.info(f"Agent response: {response_text}")
                    else:
                        logging.warning(
                            f"Final response event had no text content: {event.content}"
                        )
                        yield "data: [Agent sent non-text response]\n\n"
                elif (
                    hasattr(event, "is_tool_execution_event")
                    and event.is_tool_execution_event()
                ):
                    logging.info(
                        f"Tool execution: {getattr(event, 'tool_name', 'unknown')}"
                    )
                elif getattr(event, "type", None) == "tool_code_execution":
                    logging.info(
                        f"Tool execution: {getattr(event, 'tool_name', 'unknown')}"
                    )
                # You can add more `elif` conditions to handle other event types if needed for logging/debugging
        except Exception as e:
            logging.error(f"Error during agent run: {e}")
            yield f"data: {{'error': 'An internal error occurred: {e}'}}\n\n"

    # Return as Server-Sent Events (SSE) for streaming
    return Response(generate_responses(), mimetype="text/event-stream")
    # return Response(
    #     stream_with_context(generate_responses), mimetype="text/event-stream"
    # )
    # return jsonify(
    #     {"response": response_text}
    # )  # For non-streaming response, you can use this line instead


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "agent_name": root_agent.name}), 200


if __name__ == "__main__":
    # The ADK CLI (`adk web` or `adk run`) automatically finds the 'runner' object.
    # This asyncio.run(main()) block is for running this file directly to test the runner.
    # When using `adk web`, you don't need to call main().
    # asyncio.run(main())
    app.run(debug=True, host="0.0.0.0", port=5000)
