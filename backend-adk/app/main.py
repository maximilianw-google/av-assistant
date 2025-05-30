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

"""Backend API."""

import time
import os

from absl import logging

import fastapi
from fastapi import responses
from google.adk import runners
from google.adk import sessions
from google.genai import types
import google.cloud.logging

import google.generativeai.types

from app.agent import MEMORY_SERVICE
from app.agent import SESSION_SERVICE
from app.agent import verification_agent
from app.models import verification_models


GenerateContentResponse = google.generativeai.types.GenerateContentResponse
Session = sessions.Session
JSONResponse = responses.JSONResponse


_USER_ID = "av_assistant_user"


logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
logging.info("Logging client instantiated.")

app = fastapi.FastAPI(title="av-assistant-backend")

runner = runners.Runner(
    agent=verification_agent,
    app_name=app.title,
    session_service=SESSION_SERVICE,
    memory_service=MEMORY_SERVICE,
)


async def get_managed_session(session_id: str) -> Session:
  """Retrieves the session.

  Args:
      session_id: The session ID.

  Returns:
      A Session object.
  """
  managed_session = await runner.session_service.get_session(
      session_id=session_id, app_name=app.title, user_id=_USER_ID
  )
  if managed_session:
    return managed_session

  return await runner.session_service.create_session(
      session_id=session_id,
      app_name=app.title,
      user_id=_USER_ID,
  )


@app.post("/run_analysis")
async def run_analysis_endpoint(
    business_details_json: str = fastapi.Form(...),
    documents: list[fastapi.UploadFile] = fastapi.File([]),
    session_id: str = fastapi.Header(None, alias="Client-Session-ID"),
):
  """Runs the analysis.

  Args:
      business_details_json: The business details in JSON format.
      documents: The documents to analyze.
      session_id: The session ID.

  Returns:
      A JSON response with the analysis results.
  """
  logging.info("Received Session ID: %s", session_id)
  managed_session = await get_managed_session(session_id=session_id)
  parsed_data = None
  try:
    parts = []
    for doc_file in documents:
      file_bytes = await doc_file.read()
      filename = doc_file.filename
      mime_type = doc_file.content_type
      parts.extend([
          types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
          types.Part.from_text(text=f"The preceding file is the '{filename}'."),
      ])

    parts.append(
        types.Part.from_text(
            text=(
                "Provided Business Details (JSON"
                f" format):\n```json\n{business_details_json}\n```"
            )
        )
    )
    content = types.Content(
        role="user",
        parts=parts,
    )

    logging.info("Backend: Running analysis...")
    parsed_data = None
    start_time = time.perf_counter()
    async for event in runner.run_async(
        session_id=managed_session.id,
        user_id=managed_session.user_id,
        new_message=content,
    ):
      if event.content.parts and event.content.parts[0].text:
        parsed_data = verification_models.AnalysisResponse.model_validate_json(
            event.content.parts[0].text
        )
        break

    end_time = time.perf_counter()
    logging.info(
        "Backend: Running analysis finished in %s seconds.",
        end_time - start_time,
    )

    if parsed_data:
      return JSONResponse(content=parsed_data.model_dump())
    else:
      return JSONResponse(status_code=500, content={"error": "No parsed data"})

  except ValueError as e:
    return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
  import uvicorn  # pylint: disable=g-import-not-at-top

  uvicorn.run(
      "main:app",
      host="0.0.0.0",
      port=8080,
      reload=True,
  )
