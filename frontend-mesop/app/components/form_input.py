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

"""Renders the form input components."""

from __future__ import annotations

from absl import logging
import os
import requests
import mesop as me
from app.state import AppState

business_address_autocomplete_options = []


def render_form(state: AppState):
  """Renders the business details input form."""

  with me.box(
      style=me.Style(
          display="flex",
          flex_direction="column",
          gap=10,
          margin=me.Margin(bottom=20),
      )
  ):
    me.text(
        "Please select your business type from the options below.",
        style=me.Style(font_size="0.9em", color="grey"),
    )
    me.radio(
        key="business_type",
        on_change=update_business_detail,
        options=[
            me.RadioOption(label="Locksmith", value="Locksmith"),
            me.RadioOption(label="Garage door", value="Garage door"),
        ],
        color="accent",
        value=state.business_type,
    )
    me.text(
        "Please enter your business details as they should appear in your"
        " profile.",
        style=me.Style(font_size="0.9em", color="grey"),
    )
    # Business Name
    me.input(
        label="The full legal name of your business.",
        key="business_name",
        value=state.business_name,
        on_blur=update_business_detail,
        style=me.Style(width="100%"),
        required=True,
    )
    me.autocomplete(
        label="The registered business address",
        key="business_address",
        value=state.business_address,
        options=get_autocomplete_options(),
        on_selection_change=update_business_detail,
        on_enter=update_business_detail,
        on_input=on_business_address_raw_input,
        appearance="outline",
        style=me.Style(width="100%"),
    )
    me.input(
        label="Your business website.",
        key="business_website",
        value=state.business_website,
        on_blur=update_business_detail,
        style=me.Style(width="100%"),
        required=True,
    )
    me.text(
        text=(
            " If your business is an LLC operating with a DBA, please provide"
            " your trade name below."
        ),
        style=me.Style(font_size="0.9em", color="grey"),
    )
    me.box()
    me.slide_toggle(
        label="Doing Business As (DBA)",
        on_change=on_dba,
        color="accent",
    )
    me.box()
    if state.doing_business_as:
      me.input(
          label="Your business trade name (DBA).",
          key="business_trade_name",
          value=state.business_trade_name,
          on_blur=update_business_detail,
          style=me.Style(
              width="100%",
          ),
          required=False,
      )

    # Business Address (Street)
    me.text(
        "Any mailing addresses if different than your physical business"
        " address for which you are applying.",
        style=me.Style(font_size="0.9em", color="grey"),
    )

    for count in range(state.mailing_addresses_count):
      me.input(
          label=f"Mailing Address {str(count + 1)}",
          key=f"mailing_address_{count}",
          value=state.mailing_addresses[count],
          on_blur=update_mailing_addresses,
          style=me.Style(width="100%"),
          required=False,
      )
    with me.box(
        style=me.Style(
            display="flex",
        ),
    ):
      me.button(
          "Add",
          key="mailing_address_add",
          on_click=increment_mailing_address,
      )
      me.button(
          "Remove",
          key="mailing_address_remove",
          on_click=decrement_mailing_address,
      )

    me.text(
        "Select your business type from the options below:",
        style=me.Style(font_size="0.9em", color="grey"),
    )
    me.radio(
        key="business_sub_type",
        on_change=update_business_detail,
        options=[
            me.RadioOption(
                label="I only service customers at their locations",
                value="Service Area Business",
            ),
            me.RadioOption(
                label="I only have a branded storefront location",
                value="Storefront Only",
            ),
            me.RadioOption(
                label=(
                    "I service customers at their locations, and have a branded"
                    " storefront"
                ),
                value="Hybrid",
            ),
            me.RadioOption(
                label=(
                    "I do not provide any services; I operate a website and/or"
                    " call center that recommends local services"
                ),
                value="Aggregator",
            ),
        ],
        style=me.Style(display="flex", flex_direction="column"),
        color="accent",
        value=state.business_sub_type,
    )


def update_business_detail(
    event: (
        me.InputEvent
        | me.AutocompleteEnterEvent
        | me.AutocompleteSelectionChangeEvent
    ),
):
  """Helper function to update a specific business detail."""
  state = me.state(AppState)
  setattr(state, event.key, event.value)


def update_mailing_addresses(event: me.InputEvent):
  """Helper function to update a specific mailing address."""
  state = me.state(AppState)
  index = int(event.key.split("_")[-1])
  state.mailing_addresses[index] = event.value


def increment_mailing_address(event: me.ClickEvent):
  """Helper function to increment the mailing address count."""
  del event  # Unused.
  state = me.state(AppState)
  state.mailing_addresses_count += 1
  if state.mailing_addresses_count > len(state.mailing_addresses):
    state.mailing_addresses.append("")


def decrement_mailing_address(event: me.ClickEvent):
  """Helper function to decrement the mailing address count."""
  del event  # Unused.
  state = me.state(AppState)
  state.mailing_addresses_count -= 1
  state.mailing_addresses.pop()


def on_dba(event: me.SlideToggleChangeEvent) -> None:
  state = me.state(AppState)
  state.doing_business_as = not state.doing_business_as


def get_autocomplete_options() -> list[me.AutocompleteOptionGroup]:
  state = me.state(AppState)
  if state.business_address_raw_value:
    headers = {
        "X-Goog-Api-Key": os.environ.get("GOOGLE_MAPS_API_KEY"),
        "Content-Type": "application/json",
    }
    payload = {
        "input": state.business_address_raw_value,
        "includedRegionCodes": ["us"],
    }
    response = requests.post(
        "https://places.googleapis.com/v1/places:autocomplete",
        json=payload,
        headers=headers,
    )
    result = response.json()
    options = []
    for suggestion in result.get("suggestions"):
      formatted_address = suggestion["placePrediction"]["text"]["text"]
      options.append(
          me.AutocompleteOption(
              label=formatted_address,
              value=formatted_address,
          )
      )
    return options


def on_business_address_raw_input(event: me.InputEvent):
  state = me.state(AppState)
  state.business_address_raw_value = event.value
