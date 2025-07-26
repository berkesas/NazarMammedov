import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict


class FirestoreJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "timestamp"):
            return obj.isoformat()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def initialize_firebase(service_account_path: str) -> firestore.Client:
    """
    Initialize Firebase Admin SDK with service account credentials.

    Args:
        service_account_path: Path to your service account JSON file

    Returns:
        Firestore client instance
    """
    if not firebase_admin._apps:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)

    return firestore.client()


def insert_json_to_firestore(
    json_file_path: str,
    collection_name: str,
    service_account_path: str,
    batch_size: int = 500,
    auto_generate_id: bool = True,
    id_field: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Insert data from JSON file into Firestore collection.

    Args:
        json_file_path: Path to the JSON file containing the data
        collection_name: Name of the Firestore collection
        service_account_path: Path to Firebase service account JSON file
        batch_size: Number of documents per batch (max 500)
        auto_generate_id: Whether to auto-generate document IDs
        id_field: Field name to use as document ID (if auto_generate_id is False)

    Returns:
        Dictionary with insertion results and statistics
    """
    try:
        # Initialize Firestore client
        db = initialize_firebase(service_account_path)

        # Read JSON file
        with open(json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Ensure data is a list
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("JSON file must contain an object or array of objects")

        # Statistics
        total_documents = len(data)
        successful_inserts = 0
        failed_inserts = 0
        batches_processed = 0

        # Process data in batches
        for i in range(0, total_documents, batch_size):
            batch = db.batch()
            batch_data = data[i : i + batch_size]
            batch_count = 0

            for document in batch_data:
                try:
                    # Convert string dates to datetime objects if needed
                    document = convert_date_strings(document)

                    if auto_generate_id:
                        # Auto-generate document ID
                        doc_ref = db.collection(collection_name).document()
                    else:
                        # Use specified field as document ID
                        if id_field and id_field in document:
                            doc_id = str(document[id_field])
                            doc_ref = db.collection(collection_name).document(doc_id)
                            # Remove the ID field from document data
                            document = {
                                k: v for k, v in document.items() if k != id_field
                            }
                        else:
                            raise ValueError(
                                f"ID field '{id_field}' not found in document"
                            )

                    batch.set(doc_ref, document)
                    batch_count += 1

                except Exception as e:
                    print(f"Error preparing document for batch: {e}")
                    failed_inserts += 1

            # Commit the batch
            if batch_count > 0:
                try:
                    batch.commit()
                    successful_inserts += batch_count
                    batches_processed += 1
                    print(
                        f"Batch {batches_processed} completed: {batch_count} documents inserted"
                    )
                except Exception as e:
                    print(f"Error committing batch {batches_processed + 1}: {e}")
                    failed_inserts += batch_count

        # Return results
        result = {
            "success": True,
            "total_documents": total_documents,
            "successful_inserts": successful_inserts,
            "failed_inserts": failed_inserts,
            "batches_processed": batches_processed,
            "collection_name": collection_name,
        }

        print(f"\nInsertion completed!")
        print(f"Total documents: {total_documents}")
        print(f"Successfully inserted: {successful_inserts}")
        print(f"Failed insertions: {failed_inserts}")
        print(f"Batches processed: {batches_processed}")

        return result

    except FileNotFoundError:
        return {"success": False, "error": f"JSON file not found: {json_file_path}"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON format: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}


def convert_date_strings(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert ISO date strings to datetime objects for Firestore.

    Args:
        document: Document dictionary

    Returns:
        Document with converted date fields
    """
    converted_doc = document.copy()

    for key, value in document.items():
        if isinstance(value, str):
            # Try to parse common date formats
            date_formats = [
                "%Y-%m-%dT%H:%M:%SZ",  # ISO format with Z
                "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds
                "%Y-%m-%d %H:%M:%S",  # Standard datetime
                "%Y-%m-%d",  # Date only
            ]

            for fmt in date_formats:
                try:
                    converted_doc[key] = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue

    return converted_doc


def delete_duplicate_users_by_name(
    collection_name: str, service_account_path: str, dry_run: bool = True
):
    """
    Delete duplicate users with identical names. Keeps the first one found.

    Args:
        collection_name: Name of the Firestore collection
        service_account_path: Path to Firebase service account JSON file
        dry_run: If True, only show what would be deleted without actually deleting
    """
    # Initialize Firestore
    db = initialize_firebase(service_account_path)

    # Get all documents
    docs = db.collection(collection_name).stream()

    # Track names we've seen and documents to delete
    seen_names = set()
    docs_to_delete = []
    total_docs = 0

    for doc in docs:
        total_docs += 1
        doc_data = doc.to_dict()

        # Skip if no data or no name field
        if not doc_data or "name" not in doc_data:
            continue

        name = doc_data["name"].strip().lower()

        # If we've seen this name before, mark for deletion
        if name in seen_names:
            docs_to_delete.append(
                {
                    "id": doc.id,
                    "name": doc_data["name"],
                    "email": doc_data.get("email", "N/A"),
                }
            )
        else:
            # First time seeing this name, keep it
            seen_names.add(name)

    # Show results
    print(f"Total documents: {total_docs}")
    print(f"Duplicates found: {len(docs_to_delete)}")

    if docs_to_delete:
        print("\nDocuments to delete:")
        for doc in docs_to_delete:
            print(f"  - {doc['name']} ({doc['email']}) - ID: {doc['id'][:8]}...")

    # Delete documents if not dry run
    if not dry_run and docs_to_delete:
        batch = db.batch()
        for doc in docs_to_delete:
            doc_ref = db.collection(collection_name).document(doc["id"])
            batch.delete(doc_ref)

        batch.commit()
        print(f"\n✅ Deleted {len(docs_to_delete)} duplicate documents")
    elif dry_run and docs_to_delete:
        print(f"\n🔍 DRY RUN: Would delete {len(docs_to_delete)} documents")
        print("Set dry_run=False to actually delete them")
    else:
        print("\n✨ No duplicates found!")


# Example usage function
def insert_users():
    JSON_FILE = (
        "C:/www/hackathon/NazarMammedov/src/sub_agents/database_manager/mock_projects.json"
    )
    COLLECTION_NAME = "projects"
    SERVICE_ACCOUNT_KEY_PATH = "C:/www/hackathon/firebase_service_account_key.json"

    result = insert_json_to_firestore(
        json_file_path=JSON_FILE,
        collection_name=COLLECTION_NAME,
        service_account_path=SERVICE_ACCOUNT_KEY_PATH,
        auto_generate_id=False,
        id_field="id",
    )

    print(json.dumps(result, indent=2))


# If running as script
if __name__ == "__main__":
    # Example usage
    insert_users()

    # Example of deleting duplicates
    # delete_duplicate_users_by_name(
    #     collection_name="people",
    #     service_account_path="C:/www/hackathon/firebase_service_account_key.json",
    #     dry_run=False,
    # )

    # print(json.dumps(delete_result, indent=2))
