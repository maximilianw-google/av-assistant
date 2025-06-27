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

"""Module to interact with Google Cloud Storage."""

import base64
import mimetypes
import os

from absl import logging
import google.auth
from google.auth import compute_engine
from google.auth.transport import requests
from google.cloud import storage


class StorageClientError(Exception):
  """Base StorageClientError class."""


class StorageClient:
  """Class to interact with the Google Cloud Storage."""

  def __init__(self) -> None:
    """Instantiates the StorageClient."""
    credentials, project = google.auth.default()
    self._client = storage.Client(project=project, credentials=credentials)
    auth_request = requests.Request()
    credentials.refresh(request=auth_request)
    self._signing_credentials = compute_engine.IDTokenCredentials(
        auth_request,
        "",
        service_account_email=credentials.service_account_email,
    )
    logging.info("StorageClient: Instantiated.")

  def remove(self, bucket_name: str, sub_dir: str, file_name: str):
    """Removes a file from GCS.

    Args:
      bucket_name: The name of the bucket.
      sub_dir: The subdirectory to store the file in.
      file_name: The name for the file to be generated.
    """
    try:
      bucket = self._client.bucket(bucket_name)
      blob = bucket.blob(os.path.join(sub_dir, file_name))
      blob.delete()
    except Exception as ex:
      raise StorageClientError(
          f"StorageClient: Could not upload file {ex}",
      ) from ex

  def upload(
      self,
      bucket_name: str,
      contents: str,
      mime_type: str,
      file_name: str,
      sub_dir: str = "",
  ) -> str:
    """Stores contents on GCS.

    Args:
        bucket_name: The name of the bucket.
        contents: base64 encoded bytes.
        mime_type: The mime type of the contents.
        file_name: The name for the file to be generated.
        sub_dir: The subdirectory to store the file in.

    Returns:
        The GCS uri of the stored image.
    """
    try:
      bucket = self._client.bucket(bucket_name)
      destination_blob_name = os.path.join(sub_dir, file_name)
      blob = bucket.blob(destination_blob_name)
      blob.upload_from_string(
          base64.b64decode(contents),
          content_type=mime_type,
      )
      uri = f"gs://{bucket_name}/{destination_blob_name}"
      logging.info("StorageClient: Uploaded image to %s.", uri)
      return uri
    except Exception as ex:
      raise StorageClientError(
          f"StorageClient: Could not upload file {ex}",
      ) from ex

  def download_as_bytes(
      self, bucket_name: str, sub_dir: str, file_name: str
  ) -> tuple[bytes, str]:
    """Downloads a file as bytes.

    Args:
        bucket_name: The name of the bucket.
        sub_dir: The subdirectory to store the file in.
        file_name: The name for the file to be generated.

    Returns:
        The bytes of the downloaded file and the mime type.
    """
    blob_name = os.path.join(sub_dir, file_name)
    try:
      bucket = self._client.bucket(bucket_name)
      blob = bucket.blob(blob_name)
      mimetype = mimetypes.guess_type(file_name)[0]
      return (blob.download_as_bytes(), mimetype)
    except Exception as ex:
      raise StorageClientError(
          f"StorageClient: Could not download file {ex}",
      ) from ex

  def list_session_files(
      self, bucket_name: str, session_id: str
  ) -> list[list[str]]:
    """Lists all "directories" (prefixes) within a specified path in a GCS bucket.

    Args:
        bucket_name: The name of your Google Cloud Storage bucket.
        session_id: The session Id.

    Returns:
        A list of files available for the session.
    """
    bucket = self._client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()

    session_objects = {}

    # The `prefixes` attribute of the iterator contains the "directories"
    for p in blobs:
      session = p.name.split("/")[0]
      if not session_objects.get(session):
        session_objects[session] = [p.name.split("/")[1:]]
      else:
        session_objects[session].append(p.name.split("/")[1:])
    return session_objects.get(session_id)
