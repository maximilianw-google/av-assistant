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

"""Scaffolding for pages."""

from __future__ import annotations
import datetime
import mesop as me
from app.components import header
from app.state import AppState

APP_STEPS = [
    {"number": 1, "title": "Business Details"},
    {"number": 2, "title": "Upload Items"},
    {"number": 3, "title": "Review & Submit"},
    {"number": 4, "title": "Analysis Feedback"},
]

OVERALL_PAGE_STYLE = me.Style(
    display="flex",
    flex_direction="column",
    height="100vh",
    background=me.theme_var("surface-container-lowest"),
)

APP_HEADER_BAR_STYLE = me.Style(
    width="100%",
    padding=me.Padding(top=12, bottom=12, left=24, right=24),
    height="64px",
    display="flex",
    align_items="center",
    box_sizing="border-box",
    flex_shrink=0,
)

MAIN_LAYOUT_WITH_SIDEBAR_STYLE = me.Style(
    display="flex",
    flex_direction="row",
    flex_grow=1,
    width="100%",
    overflow="hidden",
)

SIDEBAR_STYLE = me.Style(
    width="280px",
    height="100%",
    background=me.theme_var("surface-container-low"),
    padding=me.Padding(top=24, left=8, right=8, bottom=24),
    border=me.Border(
        right=me.BorderSide(
            width=1, style="solid", color=me.theme_var("outline-variant")
        )
    ),
    display="flex",
    flex_direction="column",
    gap="4px",
    box_sizing="border-box",
    flex_shrink=0,
)

SIDEBAR_ITEM_BASE_PROPERTIES = {
    "padding": me.Padding.symmetric(vertical=10, horizontal=16),
    "border_radius": 20,
    "cursor": "default",
    "display": "flex",
    "align_items": "center",
    "gap": 12,
    "font_size": "0.9em",
}

CONTENT_AREA_SCROLLABLE_WRAPPER_STYLE = me.Style(
    flex_grow=1,
    height="100%",
    display="flex",
    flex_direction="column",
    align_items="left",
    padding=me.Padding(top=24, bottom=32, left=32, right=24),
    overflow_y="auto",
    box_sizing="border-box",
    flex_shrink=0,
)

MAIN_CONTENT_PANEL_STYLE = me.Style(
    background=me.theme_var("surface"),
    border_radius=16,
    box_shadow="0px 1px 3px rgba(0,0,0,0.1), 0px 2px 4px rgba(0,0,0,0.06)",
    padding=me.Padding(top=32, bottom=32, left=32, right=32),
    width="min(1080px, 100%)",
    display="flex",
    flex_direction="column",
    gap="24px",
    box_sizing="border-box",
    margin=me.Margin(bottom=24),
)

APP_FOOTER_STYLE = me.Style(
    width="100%",
    padding=me.Padding(top=24, bottom=24, left=24, right=24),
    text_align="center",
    color=me.theme_var("on-surface-variant"),
    font_size="0.875em",
    # CORRECTED BORDER:
    border=me.Border(
        top=me.BorderSide(
            width=1, style="solid", color=me.theme_var("outline-variant")
        )
    ),
    flex_shrink=0,
    box_sizing="border-box",
)


@me.content_component
def page_frame() -> None:
  """A more polished, Google-themed page frame component with a step sidebar."""
  state = me.state(AppState)

  with me.box(style=OVERALL_PAGE_STYLE):
    with me.box(style=MAIN_LAYOUT_WITH_SIDEBAR_STYLE):
      # Sidebar
      with me.box(style=SIDEBAR_STYLE):
        me.text(
            "STEPS",
            type="headline-6",
            style=me.Style(
                color=me.theme_var("on-surface-variant"),
                padding=me.Padding(left=16, right=16, bottom=12, top=8),
                font_weight="500",
            ),
        )
        for step_info in APP_STEPS:
          is_active = state.current_step == step_info["number"]
          is_completed = state.current_step > step_info["number"]

          current_item_props = SIDEBAR_ITEM_BASE_PROPERTIES.copy()
          current_item_props["color"] = me.theme_var("on-surface-variant")
          current_item_props["font_weight"] = "400"

          icon_name = "radio_button_unchecked"
          icon_color = me.theme_var("outline")

          if is_active:
            current_item_props["background"] = me.theme_var(
                "secondary-container"
            )
            current_item_props["color"] = me.theme_var("on-secondary-container")
            current_item_props["font_weight"] = "500"
            icon_name = "radio_button_checked"
            icon_color = me.theme_var("on-secondary-container")
          elif is_completed:
            current_item_props["color"] = me.theme_var("primary")
            icon_name = "check_circle"
            icon_color = me.theme_var("primary")

          final_item_style = me.Style(**current_item_props)

          with me.box(style=final_item_style):
            me.icon(
                icon_name, style=me.Style(color=icon_color, font_size="1.25em")
            )
            me.text(f"{step_info['title']}")

      # Main Content Area.
      with me.box(style=CONTENT_AREA_SCROLLABLE_WRAPPER_STYLE):
        with me.box(style=APP_HEADER_BAR_STYLE):
          header.header("Advanced Verification Assistant", "robot_2")
        with me.box(style=MAIN_CONTENT_PANEL_STYLE):
          me.slot()

    with me.box(style=APP_FOOTER_STYLE):
      me.text(
          f"© {datetime.datetime.now().year} Google Inc. All rights reserved."
      )
