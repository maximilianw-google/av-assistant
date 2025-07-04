"""Orchestrates getting and sending analysis results."""

import os
import re
import time
import asyncio

from absl import logging
from google.adk import runners
from google.adk import sessions
from google.genai import types
from src.agents.verification import models
from src.clients import storage_client as storage_client_lib

storage_client = storage_client_lib.StorageClient()


_SPECIAL_CHAR_PATTERN = r"[^a-zA-Z0-9\s]"
_BUCKET_NAME = os.environ.get("BUCKET_NAME")


class Analyzer:
  """Analyzer class."""

  def __init__(
      self,
      runner: runners.Runner,
      managed_session: sessions.Session,
      business_details_json: str,
      documents: list[list[str]],
      storage_client: storage_client_lib.StorageClient,
  ) -> None:
    """Initializes the analyzer.

    Args:
      runner: The runner.
      managed_session: The managed session.
      business_details_json: The business details in JSON format.
      documents: The documents to analyze.
      storage_client: An instance of StorageClient.
    """
    self.runner = runner
    self.managed_session = managed_session
    self.business_details_json = business_details_json
    self.storage_client = storage_client
    self.documents = documents
    self.last_duration = None
    self.parsed_data = None

  async def _download_file_and_save_to_artifacts(
      self, file_type: str, file_name: str
  ) -> None:
    """Downloads the file and saves it to artifacts."""
    file_bytes, mime_type = await asyncio.to_thread(
        storage_client.download_as_bytes,
        bucket_name=_BUCKET_NAME,
        sub_dir=self.managed_session.id,
        file_name=os.path.join(file_type, file_name),
    )
    await self.runner.artifact_service.save_artifact(
        app_name=self.runner.app_name,
        user_id=self.managed_session.user_id,
        session_id=self.managed_session.id,
        filename=f"document|{file_type}|{file_name}",
        artifact=types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
    )

  async def _save_documents_to_artifacts(self) -> None:
    """Saves the documents to artifacts."""
    tasks = []
    for file_type, file_name in self.documents:
      tasks.append(
          self._download_file_and_save_to_artifacts(file_type, file_name)
      )
    await asyncio.gather(*tasks, return_exceptions=True)

  def _build_prompt(self) -> types.Content:
    """Builds the prompt."""
    parts = []
    parts.append(
        types.Part.from_text(
            text=(
                "Provided Business Details (JSON"
                f" format):\n```json\n{self.business_details_json}\n```"
            )
        )
    )
    content = types.Content(
        role="user",
        parts=parts,
    )
    return content

  async def analyze(self) -> None:
    """Runs the analysis and stores results in `self.parsed_data`."""
    await self._save_documents_to_artifacts()
    new_message = self._build_prompt()

    logging.info("AGENT: Running analysis with content %s", new_message)
    start_time = time.perf_counter()
    async for event in self.runner.run_async(
        session_id=self.managed_session.id,
        user_id=self.managed_session.user_id,
        new_message=new_message,
    ):
      if event and event.content:
        if event.content.parts and event.content.parts[0].text:
          try:
            parsed_data = models.AnalysisResponse.model_validate_json(
                event.content.parts[0].text
            )
            if parsed_data:
              self.parsed_data = parsed_data
              break
          except Exception as e:
            logging.exception(e)
            continue

    end_time = time.perf_counter()
    self.last_duration = end_time - start_time
    logging.info(
        "AGENT: Running analysis finished in %s seconds.",
        end_time - start_time,
    )

  def get_status_payload(self) -> dict[str, str]:
    """Gets the status payload."""
    if self.parsed_data:
      payload = {
          "client_id": str(self.managed_session.id),
          "name": "run_analysis_ended",
          "duration": str(round(self.last_duration, 0)),
      }
      aspect_statuses = [
          item.status for item in self.parsed_data.structured_analysis
      ]
      if "Green" in aspect_statuses:
        payload["overall_status"] = "green"
      if "Yellow" in aspect_statuses:
        payload["overall_status"] = "yellow"
      if "Red" in aspect_statuses:
        payload["overall_status"] = "red"
      for item in self.parsed_data.structured_analysis:
        aspect_clean = (
            re.sub(_SPECIAL_CHAR_PATTERN, "", item.aspect)
            .replace(" ", "_")
            .lower()
        )
        payload[aspect_clean] = item.status.lower()
      return payload
    else:
      return {
          "client_id": str(self.managed_session.id),
          "name": "run_analysis_failed",
          "error_msg": "No parsed data",
      }
