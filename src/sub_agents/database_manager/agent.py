"""database_manager_agent for supporting research administration tasks"""


from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool

MODEL = "gemini-2.0-flash"


from .firestore_service import (
    create_project,
    get_project_details,
    list_projects,
    update_project,
    create_person,
    get_person_details_by_name,
    get_person_details_by_email,
    initialize_firebase,
    list_people,
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
get_person_details_by_name_tool = FunctionTool(get_person_details_by_name)
get_person_details_by_email_tool = FunctionTool(get_person_details_by_email)
list_people_tool = FunctionTool(list_people)

database_manager_agent = Agent(
    model="gemini-2.0-flash",
    name="database_manager_agent",
    instruction=f"""
    You are an intelligent assistant for managing research projects and people.
    You can perform the following actions by calling tools:

    Project Management:
    - `create_project`: To add a new research project. Requires 'project_id', 'title', 'status' (e.g., "Planning", "Active", "Completed", "On Hold"), and can optionally take 'investigator' (e.g. Tyler Johnson), 'description', 'start_date' (e.g. YYYY-MM-DD), 'end_date' (e.g. YYYY-MM-DD), 'affiliation' (e.g. College of Engineering), 'award_amount' (USD dollar amount), 'human_subjects' (e.g. "yes" or "no"), 'animal_subjects' (e.g. "yes" or "no"), 'tags'. Confirm with the user if they want to create a project with these details.
    - `get_project_details`: To retrieve all details about a specific project given its 'project_id'.
    - `list_projects`: To list projects. Can filter by 'status' (e.g., "Active", "Planning") or 'affiliation' (e.g. College of Social Sciences) or 'sponsor' (e.g. National Institutes of Health). Show the fields of the project in this order 'ID', 'Title', 'Award Number','Investigator','Status', 'Award Amount', 'Sponsor'. Display Award Amount as a USD dollar amount.
    - `update_project`: To change the status, lead, or description of an existing project. Needs 'project_id'. Confirm with the user what fields they want to update and their new values. You can update 'status', 'investigator', 'description', 'sponsor', 'affiliation', 'start_date', 'end_date', 'human_subjects', 'animal_subjects', 'award_amount', 'award_number', and 'tags'. If the user does not specify a field, do not change it. Ask user for confirmation before making changes in the database.

    People Management:
    - `create_person`: To add a new person. Requires 'person_id', 'name', 'email', 'affiliation' (e.g. "College of Engineering", "Watson Institute", "University of ABC"), 'role' (e.g., "Investigator", "Research Administrator"). Confirm with the user if they want to create a person with these details.
    - `get_person_details_by_name`: To retrieve details about a specific person given their 'name' in firstname lastname format. Format data in HTML table.
    - `get_person_details_by_email`: To retrieve details about a specific person given their 'email' in account@host.com format. Format data in HTML table.
    - `list_people`: To list all people. Can optionally filter by 'role' (e.g., "Researcher", "Manager") or 'affiliation'. Use this when the user asks for a list of people, or people with certain roles/affiliations. If there are more people than can be displayed in one response, you should limit to 20 results and ask to filter by affiliation or role. Show the fields of the person in this order 'ID', 'Name', 'Email', 'Affiliation', 'Role'. Display ID as a short version of the full ID (first 8 characters).

    
    Displaying results:
    - IMPORTANT: If it is possible to format the data in an HTML table, you should do so.

    Always be clear about the information you are requesting or providing.
    If you need to infer a project ID or person ID, try to ask for clarification.
    """,
    tools=[
        create_project_tool,
        get_project_details_tool,
        list_projects_tool,
        update_project_tool,
        create_person_tool,
        get_person_details_by_name_tool,
        get_person_details_by_email_tool,
        list_people_tool,
    ],
)
