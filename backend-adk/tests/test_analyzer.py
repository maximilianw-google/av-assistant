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

"""Unit tests for analyzer."""

import asyncio
from unittest import mock

import pytest
from src import analyzer as analyzer_lib
from src.agents.verification import models
from src.clients import storage_client as storage_client_lib


@pytest.fixture
def mock_runner():
  """Provides a reusable mock for the runner."""
  mock_runner = mock.MagicMock()
  mock_runner.artifact_service.save_artifact = mock.AsyncMock()
  mock_response_json = """
        {
          "structured_analysis": [
            {"aspect": "Business Name", "status": "Green", "reasoning": "OK"}
          ],
          "summary": "All good."
        }
        """
  mock_event = mock.MagicMock()
  mock_event.content.parts[0].text = mock_response_json

  async def mock_run_async(*args, **kwargs):
    yield mock_event

  mock_runner.run_async.side_effect = mock_run_async
  return mock_runner


@pytest.fixture
def mock_session():
  """Provides a reusable mock for the session."""
  session = mock.MagicMock()
  session.id = "fake-session-id-123"
  session.user_id = "fake-user-id-456"
  return session


@pytest.fixture
def mock_storage_client():
  """Provides a reusable mock for the storage client."""
  client = mock.create_autospec(storage_client_lib.StorageClient, instance=True)
  client.download_as_bytes.return_value = (b"fake file bytes", "image/png")
  return client


@pytest.fixture
def analyzer_factory(mock_runner, mock_session, mock_storage_client):
  """Provides a factory to create Analyzer instances for tests."""

  def _create_analyzer(documents=None):
    if documents is None:
      documents = []
    return analyzer_lib.Analyzer(
        runner=mock_runner,
        managed_session=mock_session,
        business_details_json='{"name": "Test Co."}',
        documents=documents,
        storage_client=mock_storage_client,
    )

  return _create_analyzer


@pytest.mark.asyncio
async def test_analyze_success(
    analyzer_factory, mock_runner, mock_storage_client, monkeypatch
):
  """Tests the successful orchestration of the analyze method."""
  monkeypatch.setenv("BUCKET_NAME", "fake-bucket")
  monkeypatch.setattr(analyzer_lib, "storage_client", mock_storage_client)

  async def fake_to_thread(func, *args, **kwargs):
    return func(*args, **kwargs)

  monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

  mock_parsed_data = mock.MagicMock()
  monkeypatch.setattr(
      models.AnalysisResponse,
      "model_validate_json",
      lambda *a, **k: mock_parsed_data,
  )
  monkeypatch.setattr(
      "time.perf_counter", mock.MagicMock(side_effect=[100.0, 105.5])
  )

  analyzer = analyzer_factory(
      documents=[["image", "id.png"], ["text", "terms.txt"]]
  )

  await analyzer.analyze()

  assert mock_storage_client.download_as_bytes.call_count == 2
  assert mock_runner.artifact_service.save_artifact.call_count == 2
  mock_runner.run_async.assert_called_once()
  assert analyzer.parsed_data is mock_parsed_data
  assert analyzer.last_duration == 5.5


def test_get_status_payload_success(analyzer_factory, mock_session):
  """Tests payload generation after a successful analysis."""
  analyzer = analyzer_factory()
  analyzer.last_duration = 15.3
  mock_analysis = mock.MagicMock()
  mock_analysis.structured_analysis = [
      mock.MagicMock(aspect="Business Name", status="Green"),
      mock.MagicMock(aspect="Phone Number", status="Red"),
      mock.MagicMock(aspect="Website Content", status="Yellow"),
  ]
  analyzer.parsed_data = mock_analysis

  payload = analyzer.get_status_payload()

  expected_payload = {
      "client_id": mock_session.id,
      "name": "run_analysis_ended",
      "duration": "15.0",
      "overall_status": "red",
      "business_name": "green",
      "phone_number": "red",
      "website_content": "yellow",
  }
  assert payload == expected_payload


def test_get_status_payload_failure_no_data(analyzer_factory, mock_session):
  """Tests payload generation when analysis fails to produce data."""
  analyzer = analyzer_factory()
  analyzer.parsed_data = None

  payload = analyzer.get_status_payload()

  assert payload == {
      "client_id": mock_session.id,
      "name": "run_analysis_failed",
      "error_msg": "No parsed data",
  }


def test_build_prompt(analyzer_factory):
  """Tests that the prompt is built correctly."""
  analyzer = analyzer_factory()
  business_json = '{"name": "ACME Corp."}'
  analyzer.business_details_json = business_json

  content = analyzer._build_prompt()

  assert content.role == "user"
  assert "Provided Business Details" in content.parts[0].text
  assert business_json in content.parts[0].text
