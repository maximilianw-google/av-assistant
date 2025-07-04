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

"""This module contains the implementation of the Street View sub agent."""

import os
import time
from typing import Any, Optional

from absl import logging
import aiohttp
import dotenv
from google.adk import agents
from google.adk import models
from google.adk.agents import callback_context
from google.adk.tools import base_tool
from google.adk.tools import tool_context
from google.genai import types

from .tools import geocode_address
from .tools import get_streetview_image
from .instructions import get_instructions

ToolContext = tool_context.ToolContext
BaseTool = base_tool.BaseTool
LlmResponse = models.LlmResponse
LlmAgent = agents.LlmAgent
LlmRequest = models.LlmRequest
CallbackContext = callback_context.CallbackContext
load_dotenv = dotenv.load_dotenv
find_dotenv = dotenv.find_dotenv

load_dotenv(find_dotenv())

RATE_LIMIT_SECS = 60
RPM_QUOTA = 10


def rate_limit_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> None:
  """Callback function that implements a query rate limit.

  Args:
    callback_context: A CallbackContext obj representing the active callback
      context.
    llm_request: A LlmRequest obj representing the active LLM request.
  """
  for content in llm_request.contents:
    for part in content.parts:
      if part.text == "":
        part.text = " "

  now = time.time()
  if "timer_start" not in callback_context.state:

    callback_context.state["timer_start"] = now
    callback_context.state["request_count"] = 1
    logging.debug(
        "[Callback] rate_limit_callback [timestamp: %i, req_count: 1,"
        " elapsed_secs: 0]",
        now,
    )
    return

  request_count = callback_context.state["request_count"] + 1
  elapsed_secs = now - callback_context.state["timer_start"]
  logging.debug(
      "[Callback] rate_limit_callback [timestamp: %i, request_count: %i,"
      " elapsed_secs: %i]",
      now,
      request_count,
      elapsed_secs,
  )

  if request_count > RPM_QUOTA:
    delay = RATE_LIMIT_SECS - elapsed_secs + 1
    if delay > 0:
      logging.debug("Sleeping for %i seconds", delay)
      time.sleep(delay)
    callback_context.state["timer_start"] = now
    callback_context.state["request_count"] = 1
  else:
    callback_context.state["request_count"] = request_count


async def save_streetview_image(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict[str, Any],
) -> Optional[LlmResponse]:
  """Callback function that saves the streetview image.

  Args:
    tool: The tool that was called.
    args: The arguments that were passed to the tool.
    tool_context: The tool context.
    tool_response: The response from the tool.

  Returns:
    The LLM response.
  """
  agent_name = tool_context.agent_name
  tool_name = tool.name

  if tool_name == "get_streetview_image":
    logging.debug(
        "[Callback] After tool call for tool '%s' in agent '%s'",
        agent_name,
        tool_name,
    )
    image_url = tool_response["image_link"]
    async with aiohttp.ClientSession() as session:
      async with session.get(image_url) as response:
        image_bytes = await response.read()
    if image_bytes:
      part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
      name = f"streetview_{args['heading']}_{args['pitch']}_{int(time.time())}.jpeg"
      version = await tool_context.save_artifact(name, part)
      logging.info("[Callback] Saved artifact %s version %s", name, version)
    else:
      logging.error("[Callback] Failed to download image from %s", image_url)
  else:
    logging.debug(
        "[Callback] %s tool called, but no logic implemented.", tool_name
    )


generate_content_config = types.GenerateContentConfig(
    automatic_function_calling=types.AutomaticFunctionCallingConfig(
        maximum_remote_calls=30
    )
)

root_agent = LlmAgent(
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    name="google_maps_researcher",
    instruction=get_instructions(),
    tools=[
        geocode_address,
        get_streetview_image,
    ],
    after_tool_callback=save_streetview_image,
    # before_model_callback=rate_limit_callback,
    output_key="street_view_links",
    generate_content_config=generate_content_config,
)
