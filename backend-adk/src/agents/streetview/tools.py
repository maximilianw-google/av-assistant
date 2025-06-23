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
