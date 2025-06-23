"""Implements the main Agent orchestration."""

from .scraping import agent as scraper_agent_lib
from .streetview import agent as streetview_agent_lib
from .verification import agent as verification_agent_lib

from google.adk.agents import SequentialAgent
from google.adk.agents import ParallelAgent
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService

# Singleton instances to be consumed by other moduels
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()
artifact_service = InMemoryArtifactService()

scraper_agent = scraper_agent_lib.root_agent
streetview_agent = streetview_agent_lib.root_agent
verfication_agent = verification_agent_lib.root_agent

website_researcher = SequentialAgent(
    name="MyPipeline",
    sub_agents=[scraper_agent, streetview_agent, verfication_agent],
)

root_agent = website_researcher
