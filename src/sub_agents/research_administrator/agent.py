"""research_administrator_agent for supporting research administration tasks"""

from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search

MODEL = "gemini-2.0-flash"

from . import prompt

from ..database_manager.agent import get_project_details_tool

funding_eligibility_checker_agent = Agent(
    name="funding_eligibility_checker_agent",
    model=MODEL,
    instruction=prompt.NSF_EVALUATION_PROMPT,
    tools=[get_project_details_tool],
    description="An agent that evaluates the funding eligibility of research projects based on NSF review criteria.",
)

funding_opportunity_search_agent = Agent(
    model=MODEL,
    name="funding_opportunity_search_agent",
    instruction=prompt.FUNDING_OPPORTUNITY_SEARCH_PROMPT,
    output_key="funding_opportunities",
    tools=[get_project_details_tool],
)

research_administrator_agent = Agent(
    name="research_administrator_agent",
    model=MODEL,
    instruction=prompt.RESEARCH_ADMINISTRATOR_PROMPT,
    sub_agents=[funding_eligibility_checker_agent, funding_opportunity_search_agent],
    tools=[],
    description="An agent that supports research administrators in their tasks, including funding eligibility checks.",
)
