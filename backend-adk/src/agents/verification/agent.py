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

"""The Verification Agent module."""

import os
from typing import Optional

from absl import logging
from google.adk import agents
from google.adk import models
from google.adk.agents import callback_context
from google.genai import types

from .models import AnalysisResponse
from .instructions import get_instructions


LlmAgent = agents.LlmAgent
LlmResponse = models.LlmResponse
LlmRequest = models.LlmRequest
CallbackContext = callback_context.CallbackContext

_MISSING_FILES_TEXT = "No files available for analysis."


async def _list_artifacts(self) -> list[str]:
  """Lists the filenames of the artifacts attached to the current session."""
  if self._invocation_context.artifact_service is None:
    raise ValueError("Artifact service is not initialized.")
  return await self._invocation_context.artifact_service.list_artifact_keys(
      app_name=self._invocation_context.app_name,
      user_id=self._invocation_context.user_id,
      session_id=self._invocation_context.session.id,
  )


async def add_documents_and_streetview_images_to_prompt(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  """Adds available files to the LLM prompt."""
  logging.info("[Callback] Called save_available_street_view_images_to_state")
  try:
    available_files = await _list_artifacts(callback_context)
    logging.info("[Callback] Available files: %s", available_files)
    if not available_files:
      part = types.Part(text=_MISSING_FILES_TEXT)
      llm_request.contents.append(
          types.Content(
              role="model",
              parts=[part],
          )
      )
      return None

    if llm_request.contents and llm_request.contents[-1].role == "user":
      current_message_content = llm_request.contents[-1]
    else:
      # If the last message isn't from the user or contents is empty,
      # create a new content block for the images.
      current_message_content = types.Content(role="model", parts=[])
      llm_request.contents.append(current_message_content)
    logging.info(
        "[Callback] Current message content: %s", current_message_content
    )
    image_num: int = 1
    for file in available_files:
      try:
        artifact_part = await callback_context.load_artifact(file)
        if (
            artifact_part
            and artifact_part.inline_data
            and artifact_part.inline_data.data
        ):
          if file.startswith("streetview"):
            text = f"Street View image {image_num} of the business '{file}':"
          if file.startswith("document"):
            file_type = file.split("|")[1]
            file_name = file.split("|")[2]
            text = f"{file_type} was provided with file name '{file_name}':"
          current_message_content.parts.append(types.Part(text=text))
          current_message_content.parts.append(artifact_part)
          logging.info("[Callback] Appended '%s' to prompt.", file)
        else:
          logging.warning(
              "[Callback] Artifact %s does not contain expected inline image"
              " data or is invalid. Skipping.",
              file,
          )
      except Exception as load_error:
        logging.error("Error loading artifact %s: %s", file, load_error)
        continue  # Try to load other images
    return None
  except Exception as e:
    logging.exception(
        "[Callback] An unexpected error occurred during Python artifact"
        " list: %s",
        e,
    )
    llm_request.contents.append(
        types.Content(
            role="model",
            parts=[types.Part(text=_MISSING_FILES_TEXT)],
        )
    )
    return None


generate_content_config = types.GenerateContentConfig(
    automatic_function_calling=types.AutomaticFunctionCallingConfig(
        maximum_remote_calls=30
    )
)

root_agent = LlmAgent(
    name="verification_specialist",
    description="Agent to assist with Google Advanced Verification pre-checks.",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    instruction=get_instructions(),
    output_schema=AnalysisResponse,
    output_key="analysis_results",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    before_model_callback=add_documents_and_streetview_images_to_prompt,
    generate_content_config=generate_content_config,
)
