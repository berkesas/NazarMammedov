# Research Lifecycle Management Agentic AI

The purpose of this project is to develop prototype functions for Research Lifecycle Management Agentic AI to be used at institutions where research projects are conducted at large scale such as universities, colleges, etc. It is a complex process and this project develops foundations of the framework. Research lifecycle consists of the following stages.

![Research Lifecycle Stages](images/research-lifecycle.png)

## Setup instructions

### Running the backend

```
# in repo root folder
python -m venv venv
pip install Quart quart-cors google-adk dotenv firebase-admin
python src/agent.py
```

### Running the frontend

```
cd src/frontend
python -m http.server 8000
```

Adjust ports if you decide to run with different ports

## 📂 Folder Layout

![Folder Layout Diagram](images/folder-githb.png)



## 🏅 Judging Criteria

- **Technical Excellence **  
  This criterion evaluates the robustness, functionality, and overall quality of the technical implementation. Judges will assess the code's efficiency, the absence of critical bugs, and the successful execution of the project's core features.

- **Solution Architecture & Documentation **  
  This focuses on the clarity, maintainability, and thoughtful design of the project's architecture. This includes assessing the organization and readability of the codebase, as well as the comprehensiveness and conciseness of documentation (e.g., GitHub README, inline comments) that enables others to understand and potentially reproduce or extend the solution.

- **Innovative Gemini Integration **  
  This criterion specifically assesses how effectively and creatively the Google Gemini API has been incorporated into the solution. Judges will look for novel applications, efficient use of Gemini's capabilities, and the impact it has on the project's functionality or user experience. You are welcome to use additional Google products.

- **Societal Impact & Novelty **  
  This evaluates the project's potential to address a meaningful problem, contribute positively to society, or offer a genuinely innovative and unique solution. Judges will consider the originality of the idea, its potential real‑world applicability, and its ability to solve a challenge in a new or impactful way.