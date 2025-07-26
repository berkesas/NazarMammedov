# Technical Explanation

## 1. Agent Workflow

1. User enters the system through `main_coordinator_agent` which assigns tasks to different sub-agents.
2. Session is stored in InMemoryService
3. Users can create records and update them. 
    - For example, type 'create project', 'create person'  
4. Data is retrieved using Firestore database API if needed. 
5. Summarize and return final output  

## 2. Key Modules

- **Planner** (`src/agent.py`): This is the main_coordinator_agent.py
- **Executor** (`executor.py`): The real tasks are done by agents in /sub_agents folder
- **Memory Store** (`memory.py`): Persistent memory storage for data is Firestore database. There is not much session and state management unfortunately.

## 3. Tool Integration

List each external tool or API and how you call it:
- **Firestore API**: CRUD actions are possible for Projects and People collection such as "list projects", "create person" 

## 4. Observability & Testing

- TBD

## 5. Known Limitations

This is a basic prototype and it has many limitations:
- It includes only a few functions CRUD functions for Projects and People management
- It formats results in HTML output which is not good for network traffic. Instead it should support default Markdown format.
- Due to model usage compatibility issues some functions do not run well in this demo for example 'google_search' doesn't work in funding opportunity search.