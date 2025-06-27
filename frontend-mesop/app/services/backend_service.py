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
import base64
import aiohttp

from absl import logging
import google.auth.transport.requests
import google.oauth2.id_token
import mesop as me
import requests

_BACKEND_URL = os.environ.get(  # Or your deployed Cloud Run URL
    "BACKEND_URL", "http://localhost:8008"
)
_RUN_ANALYSIS_ENDPOINT = f"{_BACKEND_URL}/run_analysis"
_UPLOAD_ENDPOINT = f"{_BACKEND_URL}/upload_document"
_REMOVE_ENDPOINT = f"{_BACKEND_URL}/remove_document"


def _get_id_token(audience: str) -> str:
  """Fetches an ID token for the specified audience."""
  req = google.auth.transport.requests.Request()
  return google.oauth2.id_token.fetch_id_token(req, audience)


def _get_headers(session_id: str) -> dict[str, str]:
  headers = {
      "Client-Session-ID": session_id,
  }
  if "localhost" not in _BACKEND_URL:
    id_token = _get_id_token(_BACKEND_URL)
    headers["Authorization"] = f"Bearer {id_token}"
  return headers


async def _make_backend_request_async(
    session_id: str,
    url: str,
    data: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
  headers = _get_headers(session_id)
  try:
    logging.info(
        "Frontend: Making request to backend service at url %s...", url
    )
    async with aiohttp.ClientSession(
        headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)
    ) as session:
      async with session.post(url=url, data=data) as response:
        response.raise_for_status()
        response_json = await response.json()
        logging.info("Received response from backend: %s", response_json)
        return response_json

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
        logging.error("JSONDecodeError occured: %s", e)
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


def _make_backend_request(
    session_id: str,
    url: str,
    data: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
  headers = _get_headers(session_id)
  try:
    logging.info(
        "Frontend: Making request to backend service at url %s...", url
    )
    response = requests.post(
        url,
        data=data,
        headers=headers,
        timeout=timeout,
    )

    response.raise_for_status()
    response_json = response.json()
    logging.info("Received response from backend: %s", response_json)
    return response_json

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
        logging.error("JSONDecodeError occured: %s", e)
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


async def trigger_analysis(
    business_details: dict[str, Any],
    documents: list[tuple[str, str]],
    session_id: str,
) -> dict[str, Any]:
  """Sends the user's input data to the backend for analysis.

  Args:
    business_details: A dictionary containing the business details.
    documents: A list of tuples, where each tuple represents a document
      (file_type, filename).
    session_id: The session ID for the current user.

  Returns:
    A dictionary containing the feedback from the backend.
  """
  payload_data = {
      "business_details_json": json.dumps(business_details),
      "documents_json": json.dumps(documents),
  }
  response = await _make_backend_request_async(
      session_id=session_id,
      url=_RUN_ANALYSIS_ENDPOINT,
      data=payload_data,
      timeout=300,
  )
  return response


def remove_file(
    file_type: str, file_name: str, session_id: str
) -> dict[str, Any]:
  """Removes a file from the backend.

  Args:
    file_path: The path to the file to remove.
    session_id: The session ID for the current user.
  """
  payload_data = {
      "file_name": f"{file_type}/{file_name}",
      "sub_dir": session_id,
  }
  response = _make_backend_request(
      session_id=session_id, url=_REMOVE_ENDPOINT, data=payload_data
  )
  return response


def upload_file(
    document: me.UploadedFile, file_type: str, session_id: str
) -> dict[str, Any]:
  """Uploads a document to the backend.

  Args:
    document: The document to upload.
    session_id: The session ID for the current user.
  """
  file_type_clean = file_type.replace("/", "_")
  payload_data = {
      "contents": base64.b64encode(document.getvalue()).decode("utf-8"),
      "mime_type": document.mime_type,
      "file_name": f"{file_type}/{document.name}",
      "sub_dir": session_id,
  }
  response = _make_backend_request(
      session_id=session_id, url=_UPLOAD_ENDPOINT, data=payload_data
  )
  return response
