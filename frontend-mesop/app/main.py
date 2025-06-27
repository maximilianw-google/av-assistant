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
from app.state import AppState
from app.state import load_backend_to_mesop_state
from app.state import load_mesop_state_to_backend
from app.state import session_backend
from app.state import SessionData
import dotenv
import fastapi
from fastapi import responses
from fastapi.middleware import wsgi
from fastapi_sessions.frontends.implementations import CookieParameters, SessionCookie
import google.cloud.logging
import mesop as me
import pydantic
import uvicorn

load_dotenv = dotenv.load_dotenv
find_dotenv = dotenv.find_dotenv

load_dotenv(find_dotenv())

BaseModel = pydantic.BaseModel
RedirectResponse = responses.RedirectResponse
Response = responses.Response
WSGIMiddleware = wsgi.WSGIMiddleware
FastAPI = fastapi.FastAPI
Request = fastapi.Request
HTTPException = fastapi.HTTPException
Depends = fastapi.Depends

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
logging.info("Logging client instantiated.")


cookie_params = CookieParameters()
cookie = SessionCookie(
    cookie_name="av-session",
    identifier="general_verifier",
    auto_error=True,
    secret_key="23edf8ugj430wedfu543",
    cookie_params=cookie_params,
)

app = FastAPI()


async def get_session(session_id: uuid.UUID = Depends(cookie)) -> SessionData:
  data = session_backend.get(session_id)
  if not data:
    # This case should ideally not happen if cookie.auto_error=True,
    # but good for safety. Create a new session data if not found.
    data = SessionData()
    session_backend[session_id] = data
  return data


@app.get("/__/auth/")
async def auth_proxy(request: Request, response: Response) -> RedirectResponse:
  """Authenticates the user and drops a session cookie if not present."""
  user_agent = request.headers.get("user-agent")
  user_email = request.headers.get("X-Goog-Authenticated-User-Email")

  try:
    session_id = cookie(request)
    session_id_str = str(session_id)
    session_data = session_backend.get(session_id_str)
    if not session_data:
      print("Session ID exists but no data in backend (e.g., server restart)")
      session_data = SessionData(user_email=user_email, user_agent=user_agent)
      session_backend[session_id_str] = session_data
    print("Found Existing")
  except Exception as e:
    session_id = uuid.uuid4()
    session_data = SessionData(user_email=user_email, user_agent=user_agent)
    session_backend[session_id] = session_data
    cookie.attach_to_response(response, session_id)

  redirect_response = RedirectResponse(
      url=f"/av-assistant?session_id={str(session_id)}"
  )
  return redirect_response


@app.get("/")
def home() -> RedirectResponse:
  """App entry point redirect."""
  return RedirectResponse(url="/__/auth/")


def on_load(event: me.LoadEvent):
  """On load event."""
  del event  # Unused.
  session_id = me.query_params["session_id"]
  session_data = session_backend.get(session_id)
  print(session_data)
  load_backend_to_mesop_state(session_data)
  state = me.state(AppState)
  state.session_id = session_id
  state.uploaded_documents = backend_service.get_existing_files(
      state.session_id
  )
  logging.info("AppState on Page Load: %s", state)


def on_next_step(event: me.ClickEvent):
  del event  # Unused.
  state = me.state(AppState)
  state.current_step += 1
  backend = session_backend.get(state.session_id)
  load_mesop_state_to_backend(backend)


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
    }
    # Call the backend ADK agent in a separate thread
    feedback = await backend_service.trigger_analysis(
        business_details,
        state.uploaded_documents,
        state.session_id,
    )
    state.analysis_feedback = json.dumps(feedback)
    state.current_step = 4
    backend = session_backend.get(state.session_id)
    load_mesop_state_to_backend(backend)
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
