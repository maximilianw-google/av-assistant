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


"""This module contains functions for getting streetview images and geocoding addresses."""

import os

import google_streetview.api
import googlemaps


def get_streetview_image(
    latlong: str, heading: str, pitch: str
) -> dict[str, str]:
  """Gets a streetview image.

  Args:
    latlong: The latitude and longitude of the location.
    heading: The heading of the camera.
    pitch: The pitch of the camera.

  Returns:
    The streetview image link.
  """
  params = [{
      "size": "600x300",  # max 640x640 pixels
      "location": latlong,
      "heading": heading,
      "pitch": pitch,
      "key": os.environ.get("GOOGLE_MAPS_API_KEY"),
  }]

  # Create a results object
  results = google_streetview.api.results(params)
  return {
      "image_link": results.links[0],
      "pitch": pitch,
      "heading": heading,
  }


def geocode_address(address: str):
  """Geocodes an address.

  Args:
    address: The address to geocode.

  Returns:
    The latitude and longitude of the address.
  """
  gmaps = googlemaps.Client(key=os.environ.get("GOOGLE_MAPS_API_KEY"))
  geocode_result = gmaps.geocode(address)
  location = geocode_result[0]["geometry"]["location"]
  return {"latlong": f"{location['lat']},{location['lng']}"}
