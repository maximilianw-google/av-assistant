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

"""Functions for triggering analysis of business data."""

from __future__ import annotations

import json
import os
from typing import Any

from absl import logging
import google.auth.transport.requests
import google.oauth2.id_token
import mesop as me
import requests

_BACKEND_URL = os.environ.get(  # Or your deployed Cloud Run URL
    "BACKEND_URL", "http://localhost:8008"
)
_RUN_ANALYSIS_ENDPOINT = f"{_BACKEND_URL}/run_analysis"
_GET_STATUS_ENDPOINT = f"{_BACKEND_URL}/status"


def _get_id_token(audience: str) -> str:
  """Fetches an ID token for the specified audience."""
  req = google.auth.transport.requests.Request()
  return google.oauth2.id_token.fetch_id_token(req, audience)


def trigger_analysis(
    business_details: dict[str, Any],
    documents: list[tuple[str, me.UploadedFile]],
    session_id: str,
) -> dict[str, Any]:
  """Sends the user's input data to the backend for analysis.

  Args:
    business_details: A dictionary containing the business details.
    documents: A list of tuples, where each tuple represents a document
      (filename, file_obj).
    session_id: The session ID for the current user.

  Returns:
    A dictionary containing the feedback from the backend.
  """
  payload_data = {"business_details_json": json.dumps(business_details)}
  files_to_upload = []

  headers = {
      "Client-Session-ID": session_id,
  }
  if "localhost" not in _BACKEND_URL:
    id_token = _get_id_token(_BACKEND_URL)
    headers["Authorization"] = f"Bearer {id_token}"

  for doc, file_obj in documents:
    # FastAPI expects multiple files under the SAME field name 'documents'
    # requests expects a list of tuples: (field_name, (filename, file_data,
    # content_type))
    files_to_upload.append((
        "documents",  # This MUST match the FastAPI parameter name for files
        (
            doc,
            file_obj.getvalue(),
            file_obj.mime_type,
        ),
    ))
  response = None
  try:
    logging.info("Frontend: Making request to backend service...")
    response = requests.post(
        _RUN_ANALYSIS_ENDPOINT,
        data=payload_data,
        headers=headers,
        files=files_to_upload,
        timeout=300,
    )

    response.raise_for_status()
    feedback = response.json()
    logging.info("Received feedback from backend: %s", feedback)
    return feedback

  except requests.exceptions.Timeout as e:
    logging.error("Request timed out: %s", e)
    return {
        "error": "The analysis request timed out. Please try again.",
        "details": str(e),
        "overall_status": "ERROR",
    }
  except requests.exceptions.ConnectionError as e:
    logging.error("Could not connect to backend: %s", e)
    return {
        "error": (
            "Could not connect to the backend service. Please check if it's"
            " running."
        ),
        "details": str(e),
        "overall_status": "ERROR",
    }
  except requests.exceptions.HTTPError as e:
    logging.error("HTTP error occurred: %s", e)
    error_content = "No additional error content."
    if response:
      try:
        error_content = response.json()
      except json.JSONDecodeError:
        error_content = response.text
    return {
        "error": f"An HTTP error occurred: {response.status_code}",
        "details": error_content,
        "overall_status": "ERROR",
    }
  except json.JSONDecodeError as e:
    logging.error("Failed to decode JSON response: %s", e)
    return {
        "error": "Received an invalid response from the backend.",
        "details": response.text if response else str(e),
        "overall_status": "ERROR",
    }
  except Exception as e:
    logging.error("An unexpected error occurred in backend_service: %s", e)
    return {
        "error": (
            "An unexpected error occurred while communicating with the backend."
        ),
        "details": str(e),
        "overall_status": "ERROR",
    }
