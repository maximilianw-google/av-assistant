import json
import os
from unittest.mock import AsyncMock, patch, MagicMock

os.environ["BUCKET_NAME"] = "test-bucket"
os.environ["TADAU_API_SECRET"] = "test-secret"
os.environ["TADAU_MEASUREMENT_ID"] = "test-id"

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_upload_document_endpoint_success():
  with patch("src.main.storage_client") as mock_storage:
    form_data = {
        "contents": "data:text/plain;base64,SGVsbG8h",
        "mime_type": "text/plain",
        "file_name": "greeting.txt",
        "sub_dir": "test-session/uploads",
    }
    response = client.post("/upload_document", data=form_data)

    assert response.status_code == 200
    assert response.json() == {"message": "Document uploaded successfully"}
    mock_storage.upload.assert_called_once_with(
        bucket_name="test-bucket",
        contents=form_data["contents"],
        mime_type=form_data["mime_type"],
        file_name=form_data["file_name"],
        sub_dir=form_data["sub_dir"],
    )


def test_upload_document_endpoint_failure():
  with patch("src.main.storage_client") as mock_storage:
    mock_storage.upload.side_effect = Exception("Storage connection failed")
    form_data = {
        "contents": "c",
        "mime_type": "m",
        "file_name": "f",
        "sub_dir": "s",
    }

    response = client.post("/upload_document", data=form_data)

    assert response.status_code == 500
    assert response.json() == {"error": "Storage connection failed"}


def test_remove_document_endpoint_success():
  with patch("src.main.storage_client") as mock_storage:
    form_data = {"file_name": "greeting.txt", "sub_dir": "test-session/uploads"}

    response = client.post("/remove_document", data=form_data)

    assert response.status_code == 200
    assert response.json() == {"message": "Document removed successfully"}
    mock_storage.remove.assert_called_once_with(
        bucket_name="test-bucket",
        file_name=form_data["file_name"],
        sub_dir=form_data["sub_dir"],
    )


def test_remove_document_endpoint_failure():
  with patch("src.main.storage_client") as mock_storage:
    mock_storage.remove.side_effect = Exception("File not found in storage")
    form_data = {"file_name": "f", "sub_dir": "s"}

    response = client.post("/remove_document", data=form_data)

    assert response.status_code == 500
    assert response.json() == {"error": "File not found in storage"}


def test_get_session_info_success():
  with patch("src.main.storage_client") as mock_storage:
    session_id = "test-session-123"
    mock_file_list = [{"name": "file1.pdf"}, {"name": "data.csv"}]
    mock_storage.list_session_files.return_value = mock_file_list

    response = client.get(f"/session_info/{session_id}")

    assert response.status_code == 200
    assert response.json() == json.dumps(mock_file_list)
    mock_storage.list_session_files.assert_called_once_with(
        bucket_name="test-bucket", session_id=session_id
    )


def test_get_session_info_failure():
  with patch("src.main.storage_client") as mock_storage:
    mock_storage.list_session_files.side_effect = ValueError(
        "Invalid session ID"
    )
    session_id = "invalid-session"

    response = client.get(f"/session_info/{session_id}")

    assert response.status_code == 500
    assert response.json() == {"error": "Invalid session ID"}


def test_run_analysis_success_with_new_session():
  with patch("src.main.runner") as mock_runner, patch(
      "src.main.analyzer_lib.Analyzer"
  ) as mock_analyzer_class, patch("src.main.tadau_client"):
    mock_runner.session_service.get_session = AsyncMock(return_value=None)
    mock_runner.session_service.create_session = AsyncMock(
        return_value=MagicMock(id="new-session")
    )

    mock_analyzer_instance = mock_analyzer_class.return_value
    mock_analyzer_instance.analyze = AsyncMock()
    mock_analyzer_instance.get_status_payload.return_value = {
        "name": "run_analysis_succeeded"
    }
    mock_analyzer_instance.parsed_data.model_dump.return_value = {
        "result": "complete"
    }

    response = client.post(
        "/run_analysis",
        data={"business_details_json": "{}", "documents_json": "[]"},
        headers={"Client-Session-ID": "new-session-id"},
    )

    assert response.status_code == 200
    assert response.json() == {"result": "complete"}
    mock_runner.session_service.get_session.assert_awaited_once()
    mock_runner.session_service.create_session.assert_awaited_once()
    mock_analyzer_class.assert_called_once()
    mock_analyzer_instance.analyze.assert_awaited_once()


def test_run_analysis_success_with_existing_session():
  with patch("src.main.runner") as mock_runner, patch(
      "src.main.analyzer_lib.Analyzer"
  ) as mock_analyzer_class, patch("src.main.tadau_client"):
    mock_session = MagicMock(id="existing-session")
    mock_runner.session_service.get_session = AsyncMock(
        return_value=mock_session
    )
    mock_runner.session_service.create_session = AsyncMock()

    mock_analyzer_instance = mock_analyzer_class.return_value
    mock_analyzer_instance.analyze = AsyncMock()
    mock_analyzer_instance.get_status_payload.return_value = {
        "name": "run_analysis_succeeded"
    }
    mock_analyzer_instance.parsed_data.model_dump.return_value = {
        "result": "ok"
    }

    response = client.post(
        "/run_analysis",
        data={"business_details_json": "{}", "documents_json": "[]"},
        headers={"Client-Session-ID": "existing-session-id"},
    )

    assert response.status_code == 200
    mock_runner.session_service.get_session.assert_awaited_once()
    mock_runner.session_service.create_session.assert_not_awaited()


def test_run_analysis_analyzer_reports_failure():
  with patch(
      "src.main.get_managed_session", new_callable=AsyncMock
  ) as mock_get_session, patch(
      "src.main.analyzer_lib.Analyzer"
  ) as mock_analyzer_class, patch(
      "src.main.tadau_client"
  ):
    mock_get_session.return_value.id = "mock-session-id"
    mock_analyzer_instance = mock_analyzer_class.return_value
    mock_analyzer_instance.analyze = AsyncMock()
    mock_analyzer_instance.get_status_payload.return_value = {
        "name": "run_analysis_failed"
    }

    response = client.post(
        "/run_analysis",
        data={"business_details_json": "{}", "documents_json": "[]"},
        headers={"Client-Session-ID": "any-id"},
    )

    assert response.status_code == 500
    assert response.json() == {"error": "No parsed data"}
    mock_analyzer_instance.analyze.assert_awaited_once()
