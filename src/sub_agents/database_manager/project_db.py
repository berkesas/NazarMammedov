import sqlite3
import json
from typing import List, Dict, Optional

DATABASE_FILE = "database.db"


def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            lead TEXT,
            start_date TEXT
        )
    """
    )
    conn.commit()
    conn.close()


def add_project_to_db(
    project_id: str,
    name: str,
    status: str,
    lead: Optional[str] = None,
    start_date: Optional[str] = None,
) -> Dict:
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO projects (id, name, status, lead, start_date) VALUES (?, ?, ?, ?, ?)",
            (project_id, name, status, lead, start_date),
        )
        conn.commit()
        return {"status": "success", "message": f"Project '{name}' added successfully."}
    except sqlite3.IntegrityError:
        return {
            "status": "error",
            "message": f"Project with ID '{project_id}' already exists.",
        }
    finally:
        conn.close()


def get_projects_from_db(status_filter: Optional[str] = None) -> List[Dict]:
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    query = "SELECT id, name, status, lead, start_date FROM projects"
    params = []
    if status_filter:
        query += " WHERE status = ?"
        params.append(status_filter)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    projects = []
    for row in rows:
        projects.append(
            {
                "id": row[0],
                "name": row[1],
                "status": row[2],
                "lead": row[3],
                "start_date": row[4],
            }
        )
    return projects


def update_project_status_in_db(project_id: str, new_status: str) -> Dict:
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE projects SET status = ? WHERE id = ?", (new_status, project_id)
    )
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    if rows_affected > 0:
        return {
            "status": "success",
            "message": f"Project '{project_id}' status updated to '{new_status}'.",
        }
    else:
        return {
            "status": "error",
            "message": f"Project with ID '{project_id}' not found.",
        }


# Call init_db() once at the start of your application
init_db()
