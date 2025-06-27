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

import fastapi
import mesop as me
import pydantic


field = dataclasses.field

BaseModel = pydantic.BaseModel


@me.stateclass
class AppState:
  """State class for the application."""

  session_id: str = ""
  current_step: int = 1
  business_name: str = ""
  business_website: str = ""
  doing_business_as: bool = False
  business_trade_name: str = ""
  business_type: str = "Garage door"
  business_sub_type: str = "Service Area Business"
  business_address: str = ""
  business_address_raw_value: str
  mailing_addresses: list[str] = field(default_factory=lambda: [""])
  mailing_addresses_count: int = 0

  uploaded_documents: list[tuple[str, str]] = field(default_factory=list)
  analysis_feedback: str = ""
  error_message: str = ""
  is_loading: bool = False
  user_email: str = ""
  user_agent: str = ""


def load_mesop_state_to_app_state(app: fastapi.FastAPI) -> None:
  """Loads Mesop App state to the fast api app state.

  Args:
    app: The FastAPI App instance.
  """
  state = me.state(AppState)
  for key in state.__dict__:
    if key in (
        "session_id",
        "business_name",
        "business_website",
        "doing_business_as",
        "business_trade_name",
        "business_type",
        "business_sub_type",
        "business_address",
        "business_address_raw_value",
        "mailing_addresses",
        "mailing_addresses_count",
        "user_email",
        "user_agent",
    ):
      setattr(app.state, key, state.__getattribute__(key))


def load_app_state_to_mesop_state(app: fastapi.FastAPI) -> None:
  """Loads the FastAPI app state to the Mesop App state.

  Args:
    app: The FastAPI App instance.
  """
  state = me.state(AppState)
  app_state = dict(app.state.__dict__.get("_state"))
  for key in app_state:
    setattr(state, key, app_state.get(key))
