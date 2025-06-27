# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Implements the main Agent orchestration."""

from google.adk.agents import ParallelAgent
from google.adk.agents import SequentialAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService

from .scraping import agent as scraper_agent_lib
from .streetview import agent as streetview_agent_lib
from .verification import agent as verification_agent_lib

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
