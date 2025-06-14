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

"""Renders the header component."""

from __future__ import annotations

import mesop as me


@me.component
def header(title: str, icon: str) -> None:
  """The header component.

  Args:
    title: The title of the header.
    icon: The icon of the header.
  """
  with me.box(
      style=me.Style(
          display="flex",
          justify_content="space-between",
      )
  ):
    with me.box(style=me.Style(display="flex", flex_direction="row", gap=15)):
      me.icon(
          icon=icon,
          style=me.Style(
              font_size="2em",
              height="1em",
              width="1em",
          ),
      )
      me.text(
          title,
          type="headline-5",
          style=me.Style(font_family="Google Sans", align_self="bottom"),
      )
