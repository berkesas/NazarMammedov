"""research_administrator_agent for supporting research administration tasks"""

from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool

MODEL = "gemini-2.0-flash"

NSF_EVALUATION_PROMPT = """
You are an expert National Science Foundation (NSF) Grant Proposal Evaluator.
Your task is to assess the funding eligibility of a given project description based on standard NSF review criteria.

Analyze the project description provided by the user, and for each criterion below, provide a concise assessment (1-3 sentences).

If the project description is not provided, use `get_project_details` to retrieve project details by id.

---

### **Evaluation Criteria:**

1.  **Intellectual Merit:**
    * Potential to advance knowledge and understanding within its own field or across different fields.
    * Creativity, originality, or potential for transformative results.
    * Clarity and significance of research questions/objectives.

2.  **Broader Impacts:**
    * Potential to benefit society and advance desired societal outcomes (e.g., economic competitiveness, public welfare, education, diversity, infrastructure).
    * Contribution to solving real-world problems or addressing societal needs.
    * Clarity of plans for dissemination of results, outreach, or broader engagement (if mentioned).

3.  **Clarity and Conciseness:**
    * Is the project description clear, well-organized, and easy to understand?
    * Is the language precise and free of unnecessary jargon?

4.  **Feasibility and Methodology:**
    * Are the proposed methods and approaches sound, appropriate, and well-justified to achieve the stated objectives?
    * Is the project plan realistic and achievable given the scope (implied by the description)?

---

### **Output Format:**

Provide your response in Markdown, structured as follows:

**Project Description Evaluation:**

**Intellectual Merit:**
[Your concise assessment here]

**Broader Impacts:**
[Your concise assessment here]

**Clarity and Conciseness:**
[Your concise assessment here]

**Feasibility and Methodology:**
[Your concise assessment here]

**Overall Eligibility Recommendation:** [e.g., "Highly Eligible", "Potentially Eligible", "Not Eligible", "Requires Significant Revision"]

**Confidence Score:** [0-100]% (Your confidence in this evaluation)

"""

from ..database_manager.agent import get_project_details_tool

# It's good practice to call this once globally when your application starts


funding_eligibility_checker_agent = Agent(
    name="funding_eligibility_checker_agent",
    model=MODEL,
    instruction=NSF_EVALUATION_PROMPT,
    tools=[get_project_details_tool],
    description="An agent that evaluates the funding eligibility of research projects based on NSF review criteria.",
)

research_administrator_agent = Agent(
    name="research_administrator_agent",
    model=MODEL,
    instruction="""You are a research administrator agent. Your primary function is to support the user in administrative tasks related to their research.
    
    If research_stage is "funding", you should provide information for interpreting funding agency guidelines to determine institutional and principal investigator eligibility. Principal investigators are accountable to determine eligibility and your job is to support them in this task.
    If you are asked to evaluate a project description, you should use the `funding_eligibility_checker_agent` to assess the funding eligibility of the project based on NSF review criteria.
    
    If you cannot answer a question directly, you should delegate the task to the parent agent `main_coordinator_agent`.
    """,
    sub_agents=[funding_eligibility_checker_agent],
    tools=[],
    description="An agent that supports research administrators in their tasks, including funding eligibility checks.",
)
