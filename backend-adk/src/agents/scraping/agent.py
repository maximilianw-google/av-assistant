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

import os
from google.adk import agents
from google.genai import types

from .tools import scrape_website_content_and_links
from .instructions import get_instructions

LlmAgent = agents.LlmAgent

generate_content_config = types.GenerateContentConfig(
    automatic_function_calling=types.AutomaticFunctionCallingConfig(
        maximum_remote_calls=30
    )
)

root_agent = LlmAgent(
    name="website_researcher",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction=get_instructions(),
    input_schema=None,
    tools=[scrape_website_content_and_links],
    output_key="website_report",
    generate_content_config=generate_content_config,
)
