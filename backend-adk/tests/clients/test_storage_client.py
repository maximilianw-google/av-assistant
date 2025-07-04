import base64
import unittest
from unittest import mock

import google.auth
from google.cloud import exceptions
from google.cloud import storage

from src.clients import storage_client as storage_client_lib

_FAKE_BUCKET_NAME = 'fake-test-bucket'
_FAKE_PROJECT = 'fake-project'
_FAKE_CONTENTS_BYTES = b'hello world'
_FAKE_CONTENTS_B64 = base64.b64encode(_FAKE_CONTENTS_BYTES).decode('utf-8')


class StorageClientTest(unittest.TestCase):

  def setUp(self):
    """Set up the test environment and mock dependencies."""
    super().setUp()
    self.mock_credentials = mock.create_autospec(
        google.auth.credentials.Credentials
    )
    self.mock_auth = self.enterContext(
        mock.patch.object(
            google.auth,
            'default',
            autospec=True,
            return_value=(self.mock_credentials, _FAKE_PROJECT),
        )
    )
    self.storage_client_mock = self.enterContext(
        mock.patch.object(storage, 'Client', autospec=True)
    )

    self.mock_bucket = mock.create_autospec(storage.Bucket, instance=True)
    self.mock_blob = mock.create_autospec(
        storage.Blob, instance=True, spec_set=True
    )

    self.storage_client_mock.return_value.bucket.return_value = self.mock_bucket
    self.storage_client_mock.return_value.get_bucket.return_value = (
        self.mock_bucket
    )

    self.mock_bucket.blob.return_value = self.mock_blob

  def test_initialization(self):
    """Tests that the client initializes correctly."""
    storage_client_lib.StorageClient()
    self.mock_auth.assert_called_once()
    self.storage_client_mock.assert_called_once_with(
        project=_FAKE_PROJECT, credentials=self.mock_credentials
    )

  def test_upload_success(self):
    """Tests successful file upload."""
    client = storage_client_lib.StorageClient()
    uri = client.upload(
        bucket_name=_FAKE_BUCKET_NAME,
        contents=_FAKE_CONTENTS_B64,
        mime_type='text/plain',
        file_name='test.txt',
        sub_dir='uploads',
    )

    self.storage_client_mock.return_value.bucket.assert_called_once_with(
        _FAKE_BUCKET_NAME
    )
    self.mock_bucket.blob.assert_called_once_with('uploads/test.txt')
    self.mock_blob.upload_from_string.assert_called_once_with(
        _FAKE_CONTENTS_BYTES, content_type='text/plain'
    )
    self.assertEqual(uri, f'gs://{_FAKE_BUCKET_NAME}/uploads/test.txt')

  def test_upload_raises_error(self):
    """Tests that upload raises StorageClientError on failure."""
    self.mock_blob.upload_from_string.side_effect = exceptions.ClientError(
        'Fake GCS Error'
    )
    client = storage_client_lib.StorageClient()

    with self.assertRaises(storage_client_lib.StorageClientError):
      client.upload(
          bucket_name=_FAKE_BUCKET_NAME,
          contents=_FAKE_CONTENTS_B64,
          mime_type='text/plain',
          file_name='test.txt',
      )

  def test_remove_success(self):
    """Tests successful file removal."""
    client = storage_client_lib.StorageClient()
    client.remove(
        bucket_name=_FAKE_BUCKET_NAME, sub_dir='uploads', file_name='test.txt'
    )

    self.mock_bucket.blob.assert_called_once_with('uploads/test.txt')
    self.mock_blob.delete.assert_called_once()

  def test_download_as_bytes_success(self):
    """Tests successful file download."""
    self.mock_blob.download_as_bytes.return_value = _FAKE_CONTENTS_BYTES
    mock_mimetypes = self.enterContext(
        mock.patch.object(
            storage_client_lib.mimetypes,
            'guess_type',
            return_value=('text/plain', None),
        )
    )

    client = storage_client_lib.StorageClient()
    data, mime_type = client.download_as_bytes(
        bucket_name=_FAKE_BUCKET_NAME,
        sub_dir='downloads',
        file_name='test.txt',
    )

    self.mock_bucket.blob.assert_called_once_with('downloads/test.txt')
    self.assertEqual(data, _FAKE_CONTENTS_BYTES)
    self.assertEqual(mime_type, 'text/plain')
    mock_mimetypes.assert_called_once_with('test.txt')

  def test_list_session_files(self):
    """Tests listing files for a specific session."""
    blob1 = mock.create_autospec(storage.Blob, instance=True)
    blob1.name = 'session123/images/cat.png'
    blob2 = mock.create_autospec(storage.Blob, instance=True)
    blob2.name = 'session123/text/dog.txt'
    blob3 = mock.create_autospec(storage.Blob, instance=True)
    blob3.name = 'session456/audio/song.mp3'
    self.mock_bucket.list_blobs.return_value = [blob1, blob2, blob3]

    client = storage_client_lib.StorageClient()
    result = client.list_session_files(
        bucket_name=_FAKE_BUCKET_NAME, session_id='session123'
    )
    self.assertEqual(
        [['images', 'cat.png'], ['text', 'dog.txt']],
        result,
    )


if __name__ == '__main__':
  unittest.main()
