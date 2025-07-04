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

"""Unit tests for the tools used by the website researcher agent."""

import unittest
from unittest.mock import patch, MagicMock
import requests

from src.agents.scraping import tools


class TestTools(unittest.TestCase):
  """Tests for the website scraper function."""

  def setUp(self):
    """Set up test case by patching requests.get."""
    patcher = patch("src.agents.scraping.tools.requests.get")
    self.mock_get = patcher.start()
    self.addCleanup(patcher.stop)

  def test_successful_scrape(self):
    """Tests a successful scrape of a website."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.apparent_encoding = "UTF-8"
    mock_response.text = """
            <html><head><title>Test Page</title></head><body>
                <p>Hello World</p>
                <a href="/internal">Internal</a>
            </body></html>
        """
    self.mock_get.return_value = mock_response

    result = tools.scrape_website_content_and_links("https://example.com")

    self.assertEqual(result["text_content"], "Test Page\nHello World\nInternal")
    self.assertIn("https://example.com/internal", result["same_domain_links"])
    self.mock_get.assert_called_once()

  def test_request_exception(self):
    """Tests handling of a requests.exceptions.RequestException."""
    self.mock_get.side_effect = requests.exceptions.RequestException(
        "Connection error"
    )

    url = "https://example.com"
    result = tools.scrape_website_content_and_links(url)

    self.assertIn(
        "Error accessing website: Connection error", result["text_content"]
    )
    self.assertEqual(result["same_domain_links"], [])

  def test_http_error(self):
    """Tests handling of an HTTPError (e.g., 404 Not Found)."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "404 Client Error: Not Found for url"
    )
    self.mock_get.return_value = mock_response

    url = "https://example.com"
    result = tools.scrape_website_content_and_links(url)

    self.assertIn("Error accessing website", result["text_content"])
    self.assertEqual(result["same_domain_links"], [])


if __name__ == "__main__":
  unittest.main()
