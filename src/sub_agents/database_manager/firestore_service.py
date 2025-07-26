# firestore_service.py
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import (
    FieldFilter,
)  # Import FieldFilter for specific queries
from typing import List, Dict, Optional, Any
import os
import logging

# Configure logging for better debugging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Firebase Initialization (call once at application start) ---
# SERVICE_ACCOUNT_KEY_PATH = os.getenv(
#     "FIREBASE_SERVICE_ACCOUNT_KEY_PATH",
#     "C:/www/hackathon/firebase_service_account_key.json",
# )
SERVICE_ACCOUNT_KEY_PATH = "C:/www/hackathon/firebase_service_account_key.json"


def initialize_firebase():
    """Initializes the Firebase Admin SDK."""
    try:
        if not firebase_admin._apps:  # Check if app is already initialized
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized.")
        else:
            print("Firebase Admin SDK already initialized.")
        return firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
        print(
            f"Please ensure '{SERVICE_ACCOUNT_KEY_PATH}' exists and is a valid Firebase service account key."
        )
        return None


db = initialize_firebase()


# --- Functions for Project Management ---
def create_project(
    project_id: str,
    title: str,
    status: str,  # e.g., "Planning", "Active", "Completed", "On Hold"
    investigator: Optional[str] = None,
    sponsor: Optional[str] = None,
    affiliation: Optional[str] = None,
    description: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    human_subjects: Optional[str] = "no",
    animal_subjects: Optional[str] = "no",
    award_amount: Optional[float] = None,
    award_number: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Adds a new research project to the database."""
    if not db:
        return {"status": "error", "message": "Database not initialized."}

    project_data = {
        "title": title,
        "status": status,
        "investigator": investigator,
        "description": description,
        "start_date": start_date,
        "end_date": end_date,
        "affiliation": affiliation,
        "sponsor": sponsor,
        "human_subjects": human_subjects,
        "animal_subjects": animal_subjects,
        "award_amount": award_amount,
        "award_number": award_number,
        "tags": tags if tags is not None else [],
        "created_at": firestore.SERVER_TIMESTAMP,
    }

    try:
        doc_ref = db.collection("projects").document(project_id)
        doc_ref.set(project_data)
        return {
            "status": "success",
            "message": f"Project '{title}' (ID: {project_id}) added to the Projects database.",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to add project '{title}': {str(e)}",
        }


def get_project_details(project_id: str) -> Dict[str, Any]:
    """Retrieves details for a specific project by its ID."""
    if not db:
        return {"status": "error", "message": "Database not initialized."}
    try:
        doc_ref = db.collection("projects").document(project_id)
        doc = doc_ref.get()
        if doc.exists:
            project_data = doc.to_dict()
            project_data["id"] = doc.id  # Include the ID in the returned data
            return {"status": "success", "project": project_data}
        else:
            return {
                "status": "not_found",
                "message": f"Project with ID '{project_id}' not found.",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get project details: {str(e)}",
        }


def list_projects(
    status_filter: Optional[str] = None,
    affiliation_filter: Optional[str] = None,
    sponsor_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lists all research projects from the Firestore 'projects' collection.
    This is a simplified function that does not include filtering or investigator name lookups.
    """
    if not db:
        logging.error("Firestore database not initialized.")
        return {"status": "error", "message": "Database not initialized."}
    try:
        logging.info("Attempting to list all projects from the 'projects' collection.")
        
        query = db.collection("projects")

        if status_filter:
            query = query.where(filter=FieldFilter("status", "==", status_filter))
        if affiliation_filter:
            query = query.where(
                filter=FieldFilter("affiliation", "==", affiliation_filter)
            )
        if sponsor_filter:
            query = query.where(filter=FieldFilter("sponsor", "==", affiliation_filter))

        projects_list = []
        # Query the entire 'projects' collection
        for doc in query.stream():
            project_data = doc.to_dict()
            project_data["id"] = doc.id  # Include the document ID
            projects_list.append(project_data)

        if not projects_list:
            logging.info("No projects found in the 'projects' collection.")
            return {
                "status": "no_projects",
                "message": "No projects found in the database.",
            }
        else:
            logging.info(f"Successfully retrieved {len(projects_list)} projects.")
            return {"status": "success", "projects": projects_list}

    except Exception as e:
        logging.exception(
            f"An unexpected error occurred while simply listing projects: {e}"
        )
        return {"status": "error", "message": f"Failed to list projects: {str(e)}"}


def update_project(
    project_id: str,
    new_status: Optional[str] = None,
    new_investigator: Optional[str] = None,
    new_description: Optional[str] = None,
    new_sponsor: Optional[str] = None,
    new_affiliation: Optional[str] = None,
    new_start_date: Optional[str] = None,
    new_end_date: Optional[str] = None,
    new_human_subjects: Optional[str] = None,
    new_animal_subjects: Optional[str] = None,
    new_award_amount: Optional[float] = None,
    new_award_number: Optional[str] = None,
    new_tags: Optional[List[str]] = None,
    # Add more fields as needed for updates
) -> Dict[str, Any]:
    """Updates fields of an existing project."""
    if not db:
        return {"status": "error", "message": "Database not initialized."}
    try:
        doc_ref = db.collection("projects").document(project_id)
        update_data = {}
        if new_status is not None:
            update_data["status"] = new_status
        if new_investigator is not None:
            update_data["investigator"] = new_investigator
        if new_description is not None:
            update_data["description"] = new_description
        if new_sponsor is not None:
            update_data["sponsor"] = new_sponsor
        if new_affiliation is not None:
            update_data["affiliation"] = new_affiliation
        if new_start_date is not None:
            update_data["start_date"] = new_start_date
        if new_end_date is not None:
            update_data["end_date"] = new_end_date
        if new_human_subjects is not None:
            update_data["human_subjects"] = new_human_subjects
        if new_animal_subjects is not None:
            update_data["animal_subjects"] = new_animal_subjects
        if new_award_amount is not None:
            update_data["award_amount"] = new_award_amount
        if new_award_number is not None:
            update_data["award_number"] = new_award_number
        if new_tags is not None:
            update_data["tags"] = new_tags

        if not update_data:
            return {"status": "info", "message": "No fields provided for update."}

        doc_ref.update(update_data)
        return {
            "status": "success",
            "message": f"Project '{project_id}' updated successfully.",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update project '{project_id}': {str(e)}",
        }


# --- Functions for People Management (similar structure) ---
def create_person(
    person_id: str, name: str, email: str, affiliation: str, role: str
) -> Dict[str, Any]:
    """Adds a new person to People table."""
    if not db:
        return {"status": "error", "message": "Database not initialized."}
    try:
        doc_ref = db.collection("people").document(person_id)
        doc_ref.set(
            {
                "name": name,
                "email": email,
                "role": role,
                "affiliation": affiliation,
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
        return {
            "status": "success",
            "message": f"Person '{name}' (ID: {person_id}) added.",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to add person '{name}': {str(e)}",
        }


def get_person_details(person_id: str) -> Dict[str, Any]:
    """Retrieves details for a specific person by their ID."""
    if not db:
        return {"status": "error", "message": "Database not initialized."}
    try:
        doc_ref = db.collection("people").document(person_id)
        doc = doc_ref.get()
        if doc.exists:
            person_data = doc.to_dict()
            person_data["id"] = doc.id  # Include the ID in the returned data
            return {"status": "success", "person": person_data}
        else:
            return {
                "status": "not_found",
                "message": f"Person with ID '{person_id}' not found.",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get person details: {str(e)}",
        }


def get_person_details_by_name(name: str) -> Dict[str, Any]:
    """
    Retrieves details for a specific person by their 'name' field.
    Returns the first matching person found, or an error if multiple or none.
    """
    if not db:
        return {"status": "error", "message": "Database not initialized."}
    try:
        # Use a query to search by the 'name' field
        query = (
            db.collection("people")
            .where(filter=FieldFilter("name", "==", name))
            .limit(2)
        )  # Limit to 2 to detect duplicates

        results = query.stream()

        found_people = []
        for doc in results:
            person_data = doc.to_dict()
            person_data["id"] = doc.id  # Add the actual document ID
            found_people.append(person_data)

        if not found_people:
            return {
                "status": "not_found",
                "message": f"Person with name '{name}' not found.",
            }
        elif len(found_people) > 1:
            # Handle non-unique names: inform the agent there are duplicates
            # The agent might then ask for more distinguishing info (e.g., email, role)
            return {
                "status": "multiple_found",
                "message": f"Multiple people with the name '{name}' found. Please provide more specific information (e.g., email or a unique ID) to identify the correct person.",
                "people_found": found_people,  # Return found data for agent to reason
            }
        else:
            # Exactly one person found
            return {"status": "success", "person": found_people[0]}

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get person details by name: {str(e)}",
        }


def get_person_details_by_email(email: str) -> Dict[str, Any]:
    """
    Retrieves details for a specific person by their 'email' field.
    Returns the first matching person found, or an error if multiple or none.
    """
    if not db:
        return {"status": "error", "message": "Database not initialized."}
    try:
        # Use a query to search by the 'email' field
        query = (
            db.collection("people")
            .where(filter=FieldFilter("email", "==", email))
            .limit(2)
        )  # Limit to 2 to detect duplicates

        results = query.stream()

        found_people = []
        for doc in results:
            person_data = doc.to_dict()
            person_data["id"] = doc.id  # Add the actual document ID
            found_people.append(person_data)

        if not found_people:
            return {
                "status": "not_found",
                "message": f"Person with email '{email}' not found.",
            }
        elif len(found_people) > 1:
            # Handle non-unique emails: inform the agent there are duplicates
            return {
                "status": "multiple_found",
                "message": f"Multiple people with the email '{email}' found. Please provide more specific information (e.g., name or a unique ID) to identify the correct person.",
                "people_found": found_people,  # Return found data for agent to reason
            }
        else:
            # Exactly one person found
            return {"status": "success", "person": found_people[0]}

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get person details by email: {str(e)}",
        }


def list_people(
    role_filter: Optional[str] = None,  # Example filter: list people by their role
    affiliation_filter: Optional[
        str
    ] = None,  # Example filter: list people by their affiliation
) -> Dict[str, Any]:
    """
    Lists all persons in the 'people' collection, with optional filters.
    Can filter by 'role' or 'affiliation'.
    """
    if not db:
        return {"status": "error", "message": "Database not initialized."}
    try:
        query = db.collection("people")

        # Apply filters if provided
        if role_filter:
            query = query.where(filter=FieldFilter("role", "==", role_filter))
        if affiliation_filter:
            query = query.where(
                filter=FieldFilter("affiliation", "==", affiliation_filter)
            )

        people_list = []
        for doc in query.stream():
            person_data = doc.to_dict()
            person_data["id"] = doc.id  # Add the document ID to the data
            people_list.append(person_data)

        if not people_list:
            message = "No people found matching the criteria."
            if role_filter and affiliation_filter:
                message = f"No people found with role '{role_filter}' and affiliation '{affiliation_filter}'."
            elif role_filter:
                message = f"No people found with role '{role_filter}'."
            elif affiliation_filter:
                message = f"No people found with affiliation '{affiliation_filter}'."
            else:
                message = "No people found in the database."

            return {
                "status": "no_people",
                "message": message,
            }
        else:
            return {"status": "success", "people": people_list}

    except Exception as e:
        return {"status": "error", "message": f"Failed to list people: {str(e)}"}
