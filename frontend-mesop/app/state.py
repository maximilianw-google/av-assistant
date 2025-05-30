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

"""State class for the application."""

from __future__ import annotations

import dataclasses

import mesop as me

field = dataclasses.field


@me.stateclass
class AppState:
  """State class for the application."""

  session_id: str = ""
  current_step: int = 1
  business_name: str = ""
  business_address: str = ""
  mailing_addresses: list[str] = field(default_factory=lambda: [""])
  mailing_addresses_count: int = 0

  uploaded_documents: list[tuple[str, me.UploadedFile]] = field(
      default_factory=list
  )
  analysis_feedback: str = ""
  error_message: str = ""
  is_loading: bool = False
  user_email: str = ""
  user_agent: str = ""
