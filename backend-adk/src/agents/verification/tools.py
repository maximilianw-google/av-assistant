from absl import logging

from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from google.adk.models import LlmResponse
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

from google.genai import types


async def _load_image_artifact_tool(
    tool_context: ToolContext, filename: str
) -> types.Part:
  """
  Tool to load an image artifact by filename and return it as a types.Part.
  """
  logging.info("Tool: Attempting to load artifact: %s", filename)
  try:
    image_part = await tool_context.load_artifact(filename)

    if image_part.inline_data:
      logging.info(
          "Tool: Successfully loaded image '%s' with MIME type: %s",
          filename,
          image_part.inline_data.mime_type,
      )
      return image_part
    else:
      raise ValueError(f"Artifact '{filename}' has no inline data.")

  except Exception as e:
    logging.exception(
        "Tool Error: Failed to load artifact '%s': %s", filename, e
    )
    raise e


load_image_artifact_tool = FunctionTool(func=_load_image_artifact_tool)
