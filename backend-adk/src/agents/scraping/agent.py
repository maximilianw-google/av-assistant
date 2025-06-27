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
from .tools import scrape_website_content_and_links

LlmAgent = agents.LlmAgent


root_agent = LlmAgent(
    name="Analyst",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction="""
    You are a detail oriented web analyst. Your job is to create a detailed and comprehensive summary of a web page and its sub pages.

    ## Instructions
    1. Scrape the provided business website from the `business_details` using the `scrape_website_content_and_links` tool.
    2. Produce a detailed report on the company's product & services offering.
    3. Once you are done with everything save the final written report to the output key 'website_content'

    ## Guidelines for the `scrape_website_content_and_links` tool.
    -   **When to Use:** Call this tool as many times as you need in order to gather the necessary information about the business service / products offerings.
    -   **How to Use:** 
        -   The tool will return the `text_content` and `same_domain_links` to subpages on the same domain. Start by using the home page and continue making calls with urls that are returned in `same_domain_links` as needed.
    -   **Arguments:**
        -   `url`: (string) The URL for the business website from the `business_details`.

    ## Final Report Guidelines:
    *  Make sure you can provide details on each of the services or products in your report.
    *  Make sure to describe the overall page outline and categories.
    """,
    input_schema=None,
    tools=[scrape_website_content_and_links],
    output_key="website_report",
)
