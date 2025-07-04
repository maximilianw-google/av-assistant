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

"""Tests for streetview and geocoding tools."""

import os
import unittest
from unittest.mock import patch, MagicMock

from src.agents.streetview.tools import get_streetview_image, geocode_address

FAKE_API_KEY = "test-api-key-12345"


class TestStreetviewTools(unittest.TestCase):
  """Contains tests for the streetview and geocoding tool functions."""

  @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": FAKE_API_KEY})
  @patch("src.agents.streetview.tools.google_streetview.api.results")
  def test_get_streetview_image(self, mock_streetview_results):
    mock_api_result = MagicMock()
    mock_api_result.links = ["http://fake-image-link.com/streetview"]
    mock_streetview_results.return_value = mock_api_result

    latlong = "40.7587,-73.9853"
    heading = "151.78"
    pitch = "-0.76"
    result = get_streetview_image(latlong, heading, pitch)

    expected_params = [{
        "size": "600x300",
        "location": latlong,
        "heading": heading,
        "pitch": pitch,
        "key": FAKE_API_KEY,
    }]
    mock_streetview_results.assert_called_once_with(expected_params)

    self.assertEqual(
        result,
        {
            "image_link": "http://fake-image-link.com/streetview",
            "pitch": pitch,
            "heading": heading,
        },
    )

  @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": FAKE_API_KEY})
  @patch("src.agents.streetview.tools.googlemaps.Client")
  def test_geocode_address(self, mock_gmaps_client):
    mock_geocode_response = [
        {"geometry": {"location": {"lat": 34.0522, "lng": -118.2437}}}
    ]
    mock_instance = mock_gmaps_client.return_value
    mock_instance.geocode.return_value = mock_geocode_response

    address = "Los Angeles, CA"
    result = geocode_address(address)

    mock_gmaps_client.assert_called_once_with(key=FAKE_API_KEY)
    mock_instance.geocode.assert_called_once_with(address)

    self.assertEqual(result, {"latlong": "34.0522,-118.2437"})


if __name__ == "__main__":
  unittest.main()
