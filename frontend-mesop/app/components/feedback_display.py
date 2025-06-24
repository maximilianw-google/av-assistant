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

"""Generates a feedback page for the analysis."""

from __future__ import annotations

from typing import Any
from app.common import utils

import mesop as me


def render_feedback(feedback: dict[str, Any]):
  """Renders the analysis feedback page based on the new JSON structure."""

  if not feedback:
    me.text("No feedback to display yet. Please submit your data for analysis.")
    return

  if "error" in feedback and isinstance(feedback["error"], str):
    me.text(
        "Analysis Error",
        type="headline-5",
        style=me.Style(color="#ea4335", margin=me.Margin(bottom=10)),
    )
    with me.box(
        style=me.Style(
            display="flex",
            align_items="center",
            gap=10,
            margin=me.Margin(bottom=15),
        )
    ):
      with me.box(
          style=me.Style(
              width="2.5em",
              height="2.5em",
              display="flex",
              align_items="center",
              justify_content="center",
          )
      ):
        me.icon("error", style=me.Style(color="#ea4335", font_size="1em"))
      me.text(
          feedback.get("details", feedback["error"]),
          style=me.Style(font_weight="bold"),
      )
    if "received_string" in feedback:
      me.text(
          "Problematic data received from agent (first 500 chars):",
          style=me.Style(
              font_size="0.8em", color="grey", margin=me.Margin(top=10)
          ),
      )
      me.text(
          str(feedback["received_string"])[:500],
          style=me.Style(
              font_family="monospace",
              white_space="pre-wrap",
              font_size="0.7em",
              background="#f0f0f0",
              padding=me.Padding.all(5),
          ),
      )
    return

  high_level_summary = feedback.get(
      "high_level_summary", "No summary provided by the analysis."
  )
  structured_analysis_items = feedback.get("structured_analysis", [])

  # Determine a derived overall status message and appearance
  derived_overall_title = "Analysis Complete"
  derived_overall_icon = "summarize"
  derived_overall_color = "#202124"

  if structured_analysis_items:
    statuses = [item.get("status") for item in structured_analysis_items]
    if "Red" in statuses:
      derived_overall_title = "Action Required: Critical Issues Found"
      derived_overall_icon = "error"
      derived_overall_color = "#ea4335"
    elif "Yellow" in statuses:
      derived_overall_title = "Review Recommended: Attention Needed"
      derived_overall_icon = "warning"
      derived_overall_color = "#fbbc05"
    else:
      derived_overall_title = "Looks Good: All Aspects Clear"
      derived_overall_icon = "check_circle"
      derived_overall_color = "#34a853"

  me.text(
      derived_overall_title,
      type="headline-5",
      style=me.Style(color=derived_overall_color, margin=me.Margin(bottom=10)),
  )

  # Display High-Level Summary in a distinct box
  with me.box(
      style=me.Style(
          padding=me.Padding.all(16),
          margin=me.Margin(bottom=24, top=5),
          border=me.Border.all(
              me.BorderSide(
                  width=1,
                  style="solid",
                  color=derived_overall_color
                  if derived_overall_color != "#202124"
                  else "#dadce0",
              )
          ),
          border_radius=8,
          background=f"{derived_overall_color}1A"
          if derived_overall_color != "#202124"
          else "#f8f9fa",
      )
  ):
    with me.box(
        style=me.Style(
            display="flex",
            align_items="center",
            gap=12,
            margin=me.Margin(bottom=8),
        )
    ):
      me.icon(
          derived_overall_icon,
          style=me.Style(
              color=derived_overall_color,
          ),
      )
      me.text(
          "Overall Summary",
          type="subtitle-1",
          style=me.Style(font_weight="bold", color=derived_overall_color),
      )
    me.markdown(
        high_level_summary,
        style=me.Style(margin=me.Margin(left=42), line_height="1.6"),
    )

  # Display Structured Analysis Items
  if structured_analysis_items:
    me.text(
        "Detailed Aspect Analysis:",
        type="headline-6",
        style=me.Style(margin=me.Margin(top=24, bottom=16)),
    )
    for item_data in structured_analysis_items:
      render_aspect_item(item_data)
  elif not ("error" in feedback and isinstance(feedback["error"], str)):
    me.text(
        "No detailed aspects were analyzed or provided in this report.",
        style=me.Style(margin=me.Margin(top=10)),
    )


def render_aspect_item(item_data: dict[str, Any]):
  """Renders a single structured analysis aspect item as a card."""
  aspect_name = item_data.get("aspect", "Unnamed Aspect")
  status = item_data.get("status", "UNKNOWN")
  justification = item_data.get("justification", "No justification provided.")
  evidence_references = item_data.get("evidence_references", [])
  evidence_image_links = item_data.get("evidence_image_links", [])

  icon_color = "#5f6368"
  item_icon = "rule"

  if status == "Green":
    icon_color = "#34a853"
    item_icon = "check_circle_outline"
  elif status == "Yellow":
    icon_color = "#fbbc05"
    item_icon = "warning_amber"
  elif status == "Red":
    icon_color = "#ea4335"
    item_icon = "highlight_off"
  else:
    pass

  with me.box(
      style=me.Style(
          border=me.Border.all(
              me.BorderSide(width=1, style="solid", color="#dadce0")
          ),
          padding=me.Padding.all(16),
          margin=me.Margin(bottom=16),
          border_radius=8,
          background="#ffffff",
          box_shadow="0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)",
      )
  ):
    with me.box(
        style=me.Style(
            display="flex",
            align_items="center",
            gap=12,
            margin=me.Margin(bottom=10),
        )
    ):
      me.icon(
          item_icon,
          style=me.Style(color=icon_color),
      )
      me.text(
          aspect_name,
          type="subtitle-1",
          style=me.Style(font_weight="500", color="#3c4043"),
      )

    # Justification
    if justification:
      me.markdown(
          justification,
          style=me.Style(
              margin=me.Margin(
                  left=44, bottom=10 if evidence_references else 0
              ),
              font_size="0.95em",
              line_height="1.6",
              color="#5f6368",
          ),
      )

    # Evidence/References
    if evidence_references:
      with me.box(
          style=me.Style(
              margin=me.Margin(left=44, top=8 if justification else 0)
          )
      ):
        me.text(
            "Evidence & References:",
            style=me.Style(
                font_weight="500",
                font_size="0.85em",
                color="#5f6368",
                margin=me.Margin(bottom=4),
            ),
        )
        for ref in evidence_references:
          me.markdown(
              f"- `{ref}`",
              style=me.Style(
                  font_size="0.85em",
                  color="#3c4043",
                  margin=me.Margin(bottom=2),
              ),
          )

    if evidence_image_links:
      with me.box(
          style=me.Style(
              margin=me.Margin(
                  left=44, bottom=10 if evidence_references else 0
              ),
              display="flex",
              flex_direction="row",
              gap=5,
          ),
      ):
        for idx, link in enumerate(evidence_image_links[:4]):
          me.image(
              src=link,
              alt=f"StreetView ({idx+1})",
              style=me.Style(
                  height="100px",
                  margin=me.Margin(top=1),
                  border_radius="10px",
              ),
          )
