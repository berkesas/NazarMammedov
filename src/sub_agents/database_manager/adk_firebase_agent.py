# adk_firebase_agent.py
import asyncio
import os
import uuid
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService  # For ADK session state
from google.adk.tools.function_tool import FunctionTool

# Import your Firebase service functions
from firestore_service import (
    create_project,
    get_project_details,
    list_projects,
    update_project,
    create_person,
    get_person_details,
    initialize_firebase,  # Initialize once at start
)

# --- Ensure Firebase is initialized before creating tools or agents ---
# It's good practice to call this once globally when your application starts
firestore_client = initialize_firebase()
if not firestore_client:
    raise RuntimeError(
        "Firebase client could not be initialized. Check service account path."
    )


# --- 1. Define ADK FunctionTools ---
# Projects
create_project_tool = FunctionTool(create_project)
get_project_details_tool = FunctionTool(get_project_details)
list_projects_tool = FunctionTool(list_projects)
update_project_tool = FunctionTool(update_project)

# People
create_person_tool = FunctionTool(create_person)
get_person_details_tool = FunctionTool(get_person_details)

# --- 2. Create the Agent ---
research_project_agent = Agent(
    model="gemini-2.0-flash",  # Use a suitable Gemini model
    name="ResearchProjectManager",
    instruction=f"""
    You are an intelligent assistant for managing research projects and people.
    You can perform the following actions by calling tools:

    Project Management:
    - `create_project`: To add a new research project. Requires 'project_id', 'name', 'status' (e.g., "Planning", "Active", "Completed", "On Hold"), and can optionally take 'lead_person_id', 'description', 'start_date', 'end_date', 'tags'.
    - `get_project_details`: To retrieve all details about a specific project given its 'project_id'.
    - `list_projects`: To list projects. Can filter by 'status' (e.g., "Active", "Planning") or 'lead_person_id'.
    - `update_project`: To change the status, lead, or description of an existing project. Needs 'project_id'.

    People Management:
    - `create_person`: To add a new person. Requires 'person_id', 'name', 'email', 'role' (e.g., "Investigator", "Research Administrator").
    - `get_person_details`: To retrieve details about a specific person given their 'person_id'.

    Always be clear about the information you are requesting or providing.
    If you need to infer a project ID or person ID, try to ask for clarification.
    """,
    tools=[
        create_project_tool,
        get_project_details_tool,
        list_projects_tool,
        update_project_tool,
        create_person_tool,
        get_person_details_tool,
    ],
)

# --- 3. Initialize DatabaseSessionService for ADK's conversational state ---
# This is for the agent's memory of the *conversation*, not the project data itself.
ADK_SESSIONS_DB_FILE = os.path.abspath("./adk_firebase_sessions.db")
ADK_SESSIONS_DB_URL = f"sqlite:///{ADK_SESSIONS_DB_FILE}"
session_service = DatabaseSessionService(db_url=ADK_SESSIONS_DB_URL)
print(f"ADK session database at: {ADK_SESSIONS_DB_FILE}")


# --- Helper function to run a query ---
# from google.generativeai.types import Part # You could comment this line out if you only need text

# ... (rest of your code)


async def run_conversation(user_query: str, session_id: str):
    print(f"\n--- User Query: '{user_query}' ---")
    response_received = False
    async for event in runner.run_async(
        app_name="ResearchProjectManager",
        user_id="dev_user_firebase",
        session_id=session_id,
        new_message=user_query,  # ADK often wraps this in a Part for you
    ):
        if event.is_agent_response():
            # Simply iterate and try to get text, or use ADK's convenience
            agent_response = ""
            if event.content and event.content.parts:
                for part in event.content.parts:
                    # Rely on duck typing or a direct check for .text attribute
                    if hasattr(part, "text") and part.text is not None:
                        agent_response += part.text + " "

            # Or even simpler, if you expect primarily single text responses:
            # You might just get the text from the first part if you're confident
            # agent_response = event.content.parts[0].text if event.content and event.content.parts else ""

            agent_response = agent_response.strip()
            if agent_response:
                print(f"Agent Response: {agent_response}")
                response_received = True
        elif event.is_tool_code_execution_request():
            print(
                f"Tool Call: {event.tool_code_execution_request.tool_name} with args: {event.tool_code_execution_request.args}"
            )
        elif event.is_tool_code_execution_result():
            print(f"Tool Result: {event.tool_code_execution_result.result}")
        elif event.is_final_result():
            # The final_result.output might be directly text in some cases
            if hasattr(event.final_result.output, "text"):
                print(f"Final Result: {event.final_result.output.text}")
            else:
                print(f"Final Result: {event.final_result.output}")  # Print as is
            response_received = True  # Consider this a final response display


# --- Main Execution ---
async def main():
    # Clean up old session DB for fresh start in this example
    if os.path.exists(ADK_SESSIONS_DB_FILE):
        # os.remove(ADK_SESSIONS_DB_FILE)
        print(f"Removed old ADK session database: {ADK_SESSIONS_DB_FILE}")

    # Get or create an ADK session for the agent's conversational state
    session_id = str(uuid.uuid4())
    await session_service.create_session(
        app_name="ResearchProjectManager",
        user_id="dev_user_firebase",
        session_id=session_id,
    )
    print(f"Created new ADK session ID: {session_id}")

    global runner
    runner = Runner(agent=research_project_agent, session_service=session_service)

    # --- Interaction Examples ---
    # 1. Create a person
    await run_conversation(
        "Add a new person: Dr. Alice Smith, email alice.smith@example.com, role Lead Researcher, ID 'alice_smith'.",
        session_id,
    )

    # 2. Create a project
    await run_conversation(
        "Create a project 'AI for Smart Cities', ID 'smart_cities_ai', status 'Planning', led by 'alice_smith', description 'Using AI for urban planning and traffic optimization'.",
        session_id,
    )

    # 3. List all projects
    await run_conversation("List all projects.", session_id)

    # 4. Get details for a specific project
    await run_conversation(
        "Tell me more about the project with ID 'smart_cities_ai'.", session_id
    )

    # 5. Update project status
    await run_conversation(
        "Change the status of 'smart_cities_ai' to 'Active'.", session_id
    )

    # 6. List active projects
    await run_conversation("What are the active projects now?", session_id)

    # 7. List projects by a specific lead (after adding more projects/people)
    await run_conversation(
        "Add a person: Bob Johnson, bob@example.com, Junior Researcher, ID 'bob_johnson'.",
        session_id,
    )
    await run_conversation(
        "Create project 'Sustainable Energy Grids', ID 'energy_grids', status 'Planning', lead 'bob_johnson'.",
        session_id,
    )
    await run_conversation("List projects led by 'alice_smith'.", session_id)

    print("\n--- Firebase Integration Example Complete ---")
    print(
        "Check your Firebase console (Firestore Database) to see the 'people' and 'projects' collections and data."
    )


if __name__ == "__main__":
    asyncio.run(main())
