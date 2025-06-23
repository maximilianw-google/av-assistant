from typing import Optional, Any
from absl import logging
import os
import aiohttp
import time


from .tools import get_streetview_image, geocode_address

from google.adk.agents import LlmAgent
from google.adk.models import LlmResponse

from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from google.genai import types
from dotenv import load_dotenv, find_dotenv

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
    tool_response: dict,
) -> Optional[LlmResponse]:
  agent_name = tool_context.agent_name
  tool_name = tool.name

  if tool_name == "get_streetview_image":
    logging.debug(
        "[Callback] After tool call for tool '%s' in agent '%s'",
        agent_name,
        tool_name,
    )
    image_bytes = None
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


root_agent = LlmAgent(
    model=os.environ.get("MODEL", "gemini-2.0-flash"),
    name="maps_assistant_agent",
    instruction=(
        "Given basic business information such as the name of the business and"
        " an address, use the `geocode_address` tool to get the coordinates"
        " (latlong). With those coordinates use the `get_streetview_image` tool"
        " to get images of the address with multiple headings and pitches.  Do"
        " NOT ask for user input on headings and pitches, instead come up with"
        " those on your own. Please add the links as a list of strings in the"
        " format: ['link1', 'link2', ...] in the state key 'street_view_links'."
    ),
    tools=[
        geocode_address,
        get_streetview_image,
    ],
    after_tool_callback=save_streetview_image,
    before_model_callback=rate_limit_callback,
    output_key="street_view_links",
)
