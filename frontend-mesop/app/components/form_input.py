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

import mesop as me
from app.state import AppState


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
        "Please enter your business details as they should appear in your"
        " profile.",
        style=me.Style(font_size="0.9em", color="grey"),
    )

    # Business Name
    me.input(
        label=(
            "The full legal name of your business. If your business is an"
            " LLC operating with a DBA, please provide both names. "
        ),
        key="business_name",
        value=state.business_name,
        on_blur=update_business_detail,
        style=me.Style(width="100%"),
        required=True,
    )

    me.input(
        label="The registered business address",
        key="business_address",
        value=state.business_address,
        on_blur=update_business_detail,
        style=me.Style(width="100%"),
        required=True,
    )

    # Business Address (Street)
    me.text(
        "Any mailing addresses if different than your physical business"
        " address for which you are applying",
        style=me.Style(font_size="0.9em", color="grey"),
    )

    for count in range(state.mailing_addresses_count):
      me.input(
          label=f"Mailing Address {str(count + 1)}",
          key=f"mailing_address_{count}",
          value=state.mailing_addresses[count],
          on_blur=update_mailing_addresses,
          style=me.Style(width="100%"),
          required=True,
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


def update_business_detail(event: me.InputEvent):
  """Helper function to update a specific business detail."""

  state = me.state(AppState)
  print(state)
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
