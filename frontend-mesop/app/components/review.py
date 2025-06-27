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

"""Renders the review page."""

from __future__ import annotations

import mesop as me
from app.state import AppState


def render_review(
    state: AppState,
) -> None:
  """Renders the review section.

  Args:
    state: The current state of the app.
  """
  # Section for Business Details
  with me.box(
      style=me.Style(
          background="#ffffff",
          padding=me.Padding.all(20),
          border_radius=8,
          margin=me.Margin(bottom=24),
          box_shadow="0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)",
      )
  ):
    me.text(
        "Business Details",
        type="headline-6",
        style=me.Style(margin=me.Margin(bottom=16), color="#3c4043"),
    )

    _render_detail_row(
        "Business Name:",
        state.business_name if state.business_name else "Not provided",
    )
    _render_detail_row(
        "Business Website:",
        state.business_website if state.business_website else "Not provided",
    )
    _render_detail_row(
        "Primary Business Address:",
        state.business_address if state.business_address else "Not provided",
    )
    _render_detail_row(
        "Doing business as trade name:",
        state.business_trade_name
        if state.business_trade_name
        else "Not provided",
    )
    _render_detail_row(
        "Business Type:",
        state.business_type if state.business_type else "Not provided",
    )
    _render_detail_row(
        "Business Sub Type:",
        state.business_sub_type if state.business_sub_type else "Not provided",
    )

    # Mailing Addresses
    valid_mailing_addresses = [
        addr for addr in state.mailing_addresses if addr.strip()
    ]
    if valid_mailing_addresses:
      with me.box(style=me.Style(margin=me.Margin(bottom=8, top=8))):
        me.text(
            "Mailing Address(es):",
            style=me.Style(
                font_weight="bold",
                color="#3c4043",
                width="200px",
                flex_shrink=0,
                margin=me.Margin(bottom=4),
            ),
        )
        with me.box(style=me.Style(padding=me.Padding(left=24))):
          for addr in valid_mailing_addresses:
            me.text(
                f"• {addr}",
                style=me.Style(color="#5f6368", margin=me.Margin(bottom=4)),
            )
    else:
      _render_detail_row("Mailing Address(es):", "Not provided")

  # Section for Uploaded Documents
  with me.box(
      style=me.Style(
          background="#ffffff",
          padding=me.Padding.all(20),
          border_radius=8,
          margin=me.Margin(bottom=24),
          box_shadow="0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)",
      )
  ):
    me.text(
        "Uploaded Documents",
        type="headline-6",
        style=me.Style(margin=me.Margin(bottom=16), color="#3c4043"),
    )
    if state.uploaded_documents:
      for doc_type, filename in state.uploaded_documents:
        _render_document_row(
            doc_type,
            filename,
        )
    else:
      me.text(
          "No documents have been uploaded yet.",
          style=me.Style(color="#5f6368", font_style="italic"),
      )
  if state.session_id:
    me.text(
        f"Reference Session ID: {state.session_id}",
        style=me.Style(
            font_size="0.8em", color="#757575", margin=me.Margin(top=20)
        ),
    )


def _render_detail_row(label: str, value: str) -> None:
  """Helper function for rendering label-value pairs for business details."""
  with me.box(
      style=me.Style(
          display="flex",
          align_items="flex-start",
          margin=me.Margin(bottom=10),
          gap=8,
      )
  ):
    me.text(
        label,
        style=me.Style(
            font_weight="500", color="#3c4043", width="200px", flex_shrink=0
        ),
    )
    me.text(value, style=me.Style(color="#5f6368", flex_grow=1))


def _render_document_row(doc_type: str, filename: str) -> None:
  """Helper function for rendering each document row."""
  with me.box(
      style=me.Style(
          display="flex",
          align_items="center",
          gap=12,
          padding=me.Padding.symmetric(vertical=10),
      )
  ):
    icon_name = "attach_file"  # if file_is_present else "do_not_disturb_on"
    icon_color = "#4285f4"  # if file_is_present else "#bdbdbd"
    filename_color = "#5f6368"  # if file_is_present else "#9e9e9e"
    filename_style = "normal"  # if file_is_present else "italic"

    me.icon(icon_name, style=me.Style(color=icon_color, font_size="1.3em"))
    me.text(
        f"{doc_type}:",
        style=me.Style(
            font_weight="500",
            color="#3c4043",
            flex_basis="250px",
            flex_shrink=0,
        ),
    )
    me.text(
        filename,
        style=me.Style(
            color=filename_color,
            font_style=filename_style,
            flex_grow=1,
            white_space="nowrap",
            overflow="hidden",
            text_overflow="ellipsis",
        ),
    )
