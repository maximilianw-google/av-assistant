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

"""Main App Page."""

from __future__ import annotations

import asyncio
import json
import os
import uuid

from absl import logging
from app.components import feedback_display
from app.components import file_uploader
from app.components import form_input
from app.components import review
from app.components import scaffold
from app.services import backend_service

import fastapi
from fastapi import responses
from fastapi.middleware import wsgi
import google.cloud.logging
import mesop as me
import pydantic
import requests

from app.state import AppState
import uvicorn
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

BaseModel = pydantic.BaseModel
RedirectResponse = responses.RedirectResponse
WSGIMiddleware = wsgi.WSGIMiddleware
FastAPI = fastapi.FastAPI
Request = fastapi.Request

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
logging.info("Logging client instantiated.")

app = FastAPI()


class UserInfo(BaseModel):
  email: str | None
  agent: str | None


@app.get("/__/auth/")
def auth_proxy(request: Request) -> RedirectResponse:
  user_agent = request.headers.get("user-agent")
  user_email = request.headers.get("X-Goog-Authenticated-User-Email")
  app.state.user_info = UserInfo(email=user_email, agent=user_agent)
  return RedirectResponse(url="/av-assistant")


@app.get("/")
def home() -> RedirectResponse:
  return RedirectResponse(url="/__/auth/")


def on_load(event: me.LoadEvent) -> None:
  """On load event."""
  del event  # Unused.
  state = me.state(AppState)
  state.user_email = app.state.user_info.email if not None else ""
  state.user_agent = app.state.user_info.agent if not None else ""
  logging.info("AppState on Page Load: %s", state)


def get_session_id():
  """Retrieves the existing user session ID or generates a new one."""
  state = me.state(AppState)
  if not state.session_id:
    state.session_id = str(uuid.uuid4())
  return state.session_id


def on_next_step(event: me.ClickEvent):
  del event  # Unused.
  state = me.state(AppState)
  state.current_step += 1


async def on_submit_data(event: me.ClickEvent):
  """Handles the submission of data for analysis."""
  del event  # Unused.
  state = me.state(AppState)
  state.is_loading = True
  state.error_message = ""
  yield
  try:
    business_details = {
        "business_name": state.business_name,
        "business_website": state.business_website,
        "business_address": state.business_address,
        "doing_business_as": str(state.doing_business_as),
        "business_trade_name": state.business_trade_name,
        "business_type": state.business_type,
        "business_sub_type": state.business_sub_type,
        "mailing_addresses": state.mailing_addresses,
        "mailing_addresses_count": state.mailing_addresses_count,
    }
    # Call the backend ADK agent in a separate thread
    feedback = await asyncio.to_thread(
        backend_service.trigger_analysis,
        business_details,
        state.uploaded_documents,
        state.session_id,
    )
    state.analysis_feedback = json.dumps(feedback)
    state.current_step = 4
  except Exception as err:  # pylint: disable=broad-exception-caught
    state.error_message = f"Analysis failed: {err}"
    # Move to an error display.
  finally:
    state.is_loading = False
    yield


@me.page(
    path="/av-assistant",
    title="AV Assistant App",
    on_load=on_load,
    security_policy=me.SecurityPolicy(
        allowed_script_srcs=[
            "https://cdn.jsdelivr.net",
        ],
        dangerously_disable_trusted_types=True,
    ),
)
def page():
  """Main App Page."""
  session_id = get_session_id()
  logging.info("Frontend: Session ID: %s", session_id)
  state = me.state(AppState)
  with scaffold.page_frame():
    if state.error_message:
      me.text(
          state.error_message,
          style=me.Style(color="red", margin=me.Margin(bottom=10)),
      )

    if state.is_loading:
      with me.box(
          style=me.Style(
              position="fixed",
              top="0",
              left="0",
              right="0",
              bottom="0",
              display="flex",
              gap=25,
              flex_direction="column",
              align_items="center",
              justify_content="center",
              background="rgba(255, 255, 255, 0.85)",
              z_index=9999,
          )
      ):
        me.progress_spinner()
        me.text("Analyzing your data, please wait...")
      return

    # Step 1: Input Business Details
    if state.current_step == 1:
      me.text("Step 1: Business Details", type="headline-5")
      form_input.render_form(state)
      me.button(
          "Next to Document Upload",
          on_click=on_next_step,
          disabled=(
              not state.business_name
              or not state.business_address
              or not state.business_website
          ),
      )

    # Step 2: Upload Documents
    elif state.current_step == 2:
      me.text(
          "Step 2: Provide Paperwork / Branding.",
          type="headline-5",
      )
      file_uploader.render_document_uploader(state)
      with me.box(
          style=me.Style(
              display="flex",
              justify_content="space-between",
              margin=me.Margin(top=20),
          )
      ):
        me.button(
            "Back",
            on_click=lambda e: setattr(state, "current_step", 1),
        )
        me.button(
            "Next to Review & Submit",
            on_click=on_next_step,
            disabled=not state.uploaded_documents,
        )

    # Step 3: Review & Submit
    elif state.current_step == 3:
      me.text("Step 3: Review & Submit", type="headline-5")
      review.render_review(state)
      with me.box(
          style=me.Style(
              display="flex",
              justify_content="space-between",
              margin=me.Margin(top=20),
          )
      ):
        me.button(
            "Back",
            on_click=lambda e: setattr(state, "current_step", 2),
        )
        me.button(
            "Submit for Analysis",
            on_click=on_submit_data,
            type="raised",
        )

    # Step 5: Display Feedback
    elif state.current_step == 4:
      me.text("Step 5: Analysis Feedback", type="headline-5")

      feedback_display.render_feedback(json.loads(state.analysis_feedback))
      me.button(
          "Start Over",
          on_click=lambda e: setattr(state, "current_step", 1),
      )


app.mount(
    "/",
    WSGIMiddleware(
        me.create_wsgi_app(
            debug_mode=os.environ.get("DEBUG_MODE", "") == "true"
        ),
    ),
)

if __name__ == "__main__":
  uvicorn.run(
      "main:app",
      host="0.0.0.0",
      port=8080,
      reload=True,
      reload_includes=["*.py", "*.js"],
  )
