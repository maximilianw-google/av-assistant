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

"""Renders the document uploader components."""

from __future__ import annotations
import os

from absl import logging
import mesop as me
import requests
from app.state import AppState

_ACCEPTED_FILE_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/jpg",
    "application/pdf",
]

_LICENSE_REQUIREMENTS = {
    "Garage door": [
        "AK",
        "AZ",
        "CA",
        "CT",
        "DC",
        "IA",
        "MD",
        "MN",
        "MT",
        "NE",
        "NV",
        "NJ",
        "NJ",
        "NM",
        "ND",
        "OR",
        "PA",
        "SC",
        "UT",
        "VA",
        "WA",
    ],
    "Locksmith": [
        "AL",
        "CA",
        "CT",
        "IL",
        "LA",
        "MD",
        "NJ",
        "NC",
        "OK",
        "OR",
        "TX",
        "VA",
        "WA",
    ],
}


def render_document_uploader(state: AppState):
  """Renders the document uploader and lists uploaded document files."""
  us_state = validate_address(state.business_address)
  if us_state in _LICENSE_REQUIREMENTS[state.business_type]:
    render_uploader_row(
        "Business License",
        "Based on the provided business address you are required to provide"
        " abusiness license. Certain US states require licenses for Locksmiths"
        " or Garage door services.",
    )
  render_uploader_row(
      "Business Invoice",
      "Attach an image of a branded receipt you would provide to a customer."
      " A business address must be on the invoice, along with your business"
      " name, and contact information. If you're a Service Area Business, you"
      " may use a P.O. box as long as the business address on the invoice.",
  )
  render_uploader_row(
      "Business Card (Front)",
      "Attach two images of your business cards: 1. Front, and 2. Back",
  )
  render_uploader_row(
      "Business Card (Back)",
      "Attach two images of your business cards: 1. Front, and 2. Back",
  )
  render_uploader_row(
      "Vehicle Registration",
      "Attach an image of your vehicle registration or registration"
      " sticker/receipt. Please note: only a registration image will be"
      " accepted - your vehicle title is not a substitute for registration.",
  )
  me.text("Please submit 5 images of your service vehicle.")
  render_uploader_row(
      "Vehicle (1/5)",
      "Submit an image of the left side of your vehicle.",
  )
  render_uploader_row(
      "Vehicle (2/5)",
      "Submit an image of the right side of your vehicle.",
  )
  render_uploader_row(
      "Vehicle (3/5)",
      "Submit an image of the rear side of your vehicle.",
  )
  render_uploader_row(
      "Vehicle (4/5)",
      "Submit an image of the front side of your vehicle.",
  )
  render_uploader_row(
      "Vehicle (5/5)",
      "Submit an image of just your license plate.",
  )
  me.text(
      "Attach images of your business’ physical location, and a utility bill."
  )
  render_uploader_row(
      "Image (1/2)",
      "An image of the exterior of your business location clearly displaying"
      " your physical address number, including suite, office, or apartment"
      " number if applicable. If your registered business address is your"
      " home, please attach an image of the exterior of your home clearly"
      " displaying the street number.",
  )
  render_uploader_row(
      "Image (2/2)",
      "A wider image displaying the entire building. If you operate a"
      " Storefront: Attach an image of the exterior of your storefront,"
      " including any signs that feature your business name.",
  )
  render_uploader_row(
      "Utility Bill",
      "Attach a copy of the most recent copy of your utility bill from the last"
      " 3 months for the address registered to your business. Bank statements"
      " will not be accepted. The following are acceptable utility bills:"
      " garbage collection, water, sewage, electricity, internet, gas.",
  )
  me.text(
      "Attach 2 separate images of Tools & Equipment that you use to"
      " complete typical jobs, next to your business car or branded invoice."
      " We will disqualify images of tools or equipment that do not also"
      " contain a business card or branded invoice."
  )
  render_uploader_row(
      "Tools & Equipment (1/2)",
      "Common tools such as power drills, hammers, and"
      " similar hand tools DO NOT meet our requirements. If you are a"
      " full-service locksmith, you are required to provide a lock pick set"
      " and one other tool.",
  )
  render_uploader_row(
      "Tools & Equipment (2/2)",
      "Common tools such as power drills, hammers, and"
      " similar hand tools DO NOT meet our requirements. If you are a"
      " full-service locksmith, you are required to provide a lock pick set"
      " and one other tool.",
  )
  if state.uploaded_documents:
    me.text("Uploaded Documents:", type="subtitle-2")
    for index, file in enumerate(state.uploaded_documents):
      if file:  # me.UploadedFile can be None if a file was removed
        with me.box(
            style=me.Style(
                display="flex",
                align_items="center",
                gap=5,
                margin=me.Margin(top=5),
            )
        ):
          me.text(f"{file[0]}:", style=me.Style(font_weight="bold"))
          me.icon("description")  # Material icon for document
          me.text(file[1].name)
          with me.content_button(
              on_click=lambda e: remove_document(index),
              key=f"remove_document_{index}",
          ):
            me.icon(
                "delete",
                style=me.Style(color="red", cursor="pointer"),
            )


def render_uploader_row(title: str, description: str):
  state = me.state(AppState)
  is_uploaded = False
  if state.uploaded_documents:
    for file in state.uploaded_documents:
      if file[0] == title:
        is_uploaded = True
        break
  with me.box(
      style=me.Style(
          display="flex",
          gap=20,
          align_items="center",
          flex_direction="row",
      )
  ):
    if is_uploaded:
      me.icon("check_circle", style=me.Style(color="green"))
    with me.content_uploader(
        accepted_file_types=_ACCEPTED_FILE_MIME_TYPES,
        on_upload=handle_document_upload,
        key=title,
        type="flat",
        color="primary",
        # Not implemented, yet. Need to wait for newer mesop version
        # to come out, however one by one uploads may be preferred
        # anyways.
        # multiple=True,
        style=me.Style(font_weight="bold"),
    ):
      with me.box(style=me.Style(display="flex", gap=5)):
        me.icon("upload")
        me.text("Upload", style=me.Style(line_height="25px"))
    with me.box(style=me.Style(width="20%")):
      me.text(title)
    with me.box(style=me.Style(width="80%")):
      me.text(
          description,
          type="subtitle-2",
          style=me.Style(color="grey"),
      )


def handle_document_upload(event: me.UploadEvent):
  """Updates the app state with the uploaded document files."""
  state = me.state(AppState)
  state.uploaded_documents.append((event.key, event.file))


def remove_document(file_index_to_remove: int):
  state = me.state(AppState)
  state.uploaded_documents.pop(file_index_to_remove)


def validate_address(address_lines: str | list[str], region_code: str = "US"):
  """Validates an address using the Google Maps Address Validation API.

  Args:
      address_lines: A list of strings representing the address lines.
      region_code: The two-letter region code (e.g., "US" for United States).

  Returns:
      A the US state of the address.
  """
  payload = {
      "address": {"regionCode": region_code, "addressLines": [address_lines]}
  }
  api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
  url = f"https://addressvalidation.googleapis.com/v1:validateAddress?key={api_key}"
  try:
    response = requests.post(
        url=url, json=payload, headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    result = response.json()
    return result["result"]["address"]["postalAddress"]["administrativeArea"]
  except KeyError as e:
    logging.exception("Error exctracting state from address: %s", e)
    return None
  except requests.exceptions.HTTPError as e:
    logging.exception("Error making request to validate address: %s", e)
    return None
  except Exception as e:
    logging.exception("Error validating address: %s", e)
    return None
