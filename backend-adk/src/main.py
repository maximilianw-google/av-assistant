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

import os
from absl import logging

import fastapi
import tadau
import asyncio
from fastapi.responses import JSONResponse
from google.adk import runners
from google.adk.sessions import Session
import google.cloud.logging

from google.generativeai.types import GenerateContentResponse

from src.agents import agent as agent_lib
from src import analyzer as analyzer_lib
from dotenv import load_dotenv, find_dotenv

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
  managed_session = await get_managed_session(
      runner=runner, session_id=session_id, app_name=app.title, user_id=_USER_ID
  )
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


if __name__ == "__main__":
  import uvicorn  # pylint: disable=g-import-not-at-top

  uvicorn.run(
      "main:app",
      host="0.0.0.0",
      port=8080,
      reload=True,
  )
