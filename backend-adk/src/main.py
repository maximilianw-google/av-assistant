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

"""Defines the backend API endpoints."""

import asyncio
import json
import os
from absl import logging
import dotenv
import fastapi
from fastapi import responses
from google.adk import runners
from google.adk import sessions
import google.cloud.logging
from src import analyzer as analyzer_lib
from src.agents import agent as agent_lib
from src.clients import storage_client as storage_client_lib
import tadau

load_dotenv = dotenv.load_dotenv
find_dotenv = dotenv.find_dotenv
Session = sessions.Session
JSONResponse = responses.JSONResponse

load_dotenv(find_dotenv())

Tadau = tadau.Tadau
orchestrator_agent = agent_lib.root_agent

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
logging.info("Logging client instantiated.")

_USER_ID = "av_assistant_user"
_TADAU_FIXED_DIMENSIONS = {
    "deploy_id": os.environ.get("DEPLOY_ID"),
    "deploy_infra": os.environ.get("DEPLOY_INFRA"),
    "deploy_created_time": os.environ.get("DEPLOY_CREATED_TIMESTAMP"),
    "deploy_updated_time": os.environ.get("DEPLOY_UPDATED_TIMESTAMP"),
}
_BUCKET_NAME = os.environ.get("BUCKET_NAME")


app = fastapi.FastAPI(title="av-assistant-backend")
runner = runners.Runner(
    agent=orchestrator_agent,
    app_name=app.title,
    session_service=agent_lib.session_service,
    memory_service=agent_lib.memory_service,
    artifact_service=agent_lib.artifact_service,
)
tadau_client = Tadau(
    api_secret=os.environ.get("TADAU_API_SECRET"),
    measurement_id=os.environ.get("TADAU_MEASUREMENT_ID"),
    opt_in=os.environ.get("TADAU_OPT_IN", "false").lower() == "true",
    fixed_dimensions=_TADAU_FIXED_DIMENSIONS,
)
storage_client = storage_client_lib.StorageClient()


async def get_managed_session(
    runner: runners.Runner, session_id: str, app_name: str, user_id: str
) -> Session:
  """Retrieves the session.

  Args:
      runner: The runner.
      session_id: The session ID.
      app_name: The app name.
      user_id: The user ID.

  Returns:
      A Session object.
  """
  managed_session = await runner.session_service.get_session(
      session_id=session_id, app_name=app_name, user_id=user_id
  )
  if managed_session:
    return managed_session

  return await runner.session_service.create_session(
      session_id=session_id,
      app_name=app_name,
      user_id=user_id,
  )


@app.post("/run_analysis")
async def run_analysis_endpoint(
    business_details_json: str = fastapi.Form(...),
    documents_json: str = fastapi.Form(...),
    # documents: list[fastapi.UploadFile] = fastapi.File([]),
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
  logging.info(
      "Received Request for /run_analysis: Business data: %s, documents: %s",
      business_details_json,
      documents_json,
  )
  managed_session = await get_managed_session(
      runner=runner, session_id=session_id, app_name=app.title, user_id=_USER_ID
  )
  documents: list[list[str]] = json.loads(documents_json)
  await asyncio.to_thread(
      tadau_client.send_events,
      events=[{
          "client_id": str(managed_session.id),
          "name": "run_analysis_started",
          "documents_count": len(documents),
      }],
  )
  try:
    analyzer = analyzer_lib.Analyzer(
        runner=runner,
        managed_session=managed_session,
        business_details_json=business_details_json,
        documents=documents,
        storage_client=storage_client,
    )
    await analyzer.analyze()
    payload = analyzer.get_status_payload()
    await asyncio.to_thread(tadau_client.send_events, events=[payload])
    if payload.get("name") == "run_analysis_failed":
      return JSONResponse(status_code=500, content={"error": "No parsed data"})
    return JSONResponse(content=analyzer.parsed_data.model_dump())

  except ValueError as e:
    payload = {
        "client_id": str(managed_session.id),
        "name": "run_analysis_failed",
        "error_msg": str(e),
    }
    await asyncio.to_thread(tadau_client.send_events, events=[payload])
    logging.exception("Error running analysis: %s", e)
    return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/upload_document")
async def upload_document(
    contents: str = fastapi.Form(...),
    mime_type: str = fastapi.Form(...),
    file_name: str = fastapi.Form(...),
    sub_dir: str = fastapi.Form(...),
):
  """Uploads a document to the storage.

  Args:
      contents: The contents of the document.
      mime_type: The MIME type of the document.
      file_name: The name of the file.
      sub_dir: The subdirectory where the file should be uploaded.

  Returns:
      A JSON response with the upload status.
  """
  logging.info(
      "Received request for /upload_document: %s, %s",
      file_name,
      sub_dir,
  )
  try:
    storage_client.upload(
        bucket_name=_BUCKET_NAME,
        contents=contents,
        mime_type=mime_type,
        file_name=file_name,
        sub_dir=sub_dir,
    )
    return JSONResponse(content={"message": "Document uploaded successfully"})
  except Exception as e:
    logging.exception("Error uploading document: %s", e)
    return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/remove_document")
async def remove_document(
    file_name: str = fastapi.Form(...),
    sub_dir: str = fastapi.Form(...),
):
  """Removes a document from the storage.

  Args:
      file_name: The name of the file.
      sub_dir: The subdirectory where the file should be removed from.

  Returns:
      A JSON response with the removal status.
  """
  try:
    storage_client.remove(
        bucket_name=_BUCKET_NAME, file_name=file_name, sub_dir=sub_dir
    )
    return JSONResponse(content={"message": "Document removed successfully"})
  except Exception as e:
    logging.exception("Error removing document: %s", e)
    return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/session_info/{session_id}")
async def get_session_info(session_id: str):
  """Gets the session information.

  Args:
      session_id: The ID of the session.

  Returns:
      A JSON response with the session information.
  """
  try:
    session_data = storage_client.list_session_files(
        bucket_name=_BUCKET_NAME, session_id=session_id
    )
    return JSONResponse(content=json.dumps(session_data))
  except ValueError as e:
    logging.exception("Error getting session info: %s", e)
    return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
  import uvicorn  # pylint: disable=g-import-not-at-top

  uvicorn.run(
      "main:app",
      host="0.0.0.0",
      port=8080,
      reload=True,
  )
