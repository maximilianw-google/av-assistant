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

"""This module contains the load_image_artifact_tool function."""

from absl import logging
from google.adk import tools
from google.adk.tools import tool_context
from google.genai import types

ToolContext = tool_context.ToolContext
FunctionTool = tools.FunctionTool


async def _load_image_artifact_tool(
    tool_context: ToolContext, filename: str
) -> types.Part:
  """Tool to load an image artifact by filename and return it as a types.Part."""
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
