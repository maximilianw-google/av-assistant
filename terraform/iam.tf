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

# Service Accounts
resource "google_service_account" "iap_sa" {
  account_id   = "av-assistant-iap-sa"
  display_name = "AV Assitant App IAP Service Account"
}

resource "google_service_account" "frontend_sa" {
  account_id   = "av-assistant-frontend-sa"
  display_name = "AV Assitant App Frontend Service Account"
}

resource "google_service_account" "backend_sa" {
  account_id   = "av-assistant-backend-sa"
  display_name = "GAV Assitant App Backend Service Account"
}

# Service Identities
resource "google_project_service_identity" "cloudbuild" {
  project = var.project_id
  provider = google-beta
  service  = "cloudbuild.googleapis.com"
}

resource "google_project_service_identity" "iap" {
  project = var.project_id
  provider = google-beta
  service  = "iap.googleapis.com"
}


resource "google_project_iam_binding" "logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  members = [
    "serviceAccount:${google_service_account.frontend_sa.email}",
    "serviceAccount:${google_service_account.backend_sa.email}",
  ]
}

resource "google_project_iam_binding" "logging_viewer" {
  project = var.project_id
  role    = "roles/logging.viewer"
  members = [
    "serviceAccount:${google_service_account.frontend_sa.email}",
    "serviceAccount:${google_service_account.backend_sa.email}",
  ]
}

resource "google_project_iam_binding" "token_creator" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  members = [
    "serviceAccount:${google_service_account.frontend_sa.email}",
    "serviceAccount:${google_service_account.backend_sa.email}",
  ]
}

resource "google_project_iam_binding" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  members = [
    "serviceAccount:${google_service_account.frontend_sa.email}",
    "serviceAccount:${google_service_account.backend_sa.email}",
  ]
}

resource "google_project_iam_binding" "run_invoker" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  members = [
    "serviceAccount:${google_project_service_identity.iap.email}",
  ]
}


# IAM policy for the Cloud Run services
resource "google_cloud_run_v2_service_iam_binding" "frontend_run_invoker" {
  location = google_cloud_run_v2_service.frontend.location
  project  = google_cloud_run_v2_service.frontend.project
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  members = [
    "serviceAccount:${google_service_account.frontend_sa.email}",
    "serviceAccount:${google_service_account.iap_sa.email}",
  ]
}

resource "google_cloud_run_v2_service_iam_binding" "backend_run_invoker" {
  location = google_cloud_run_v2_service.backend.location
  project  = google_cloud_run_v2_service.backend.project
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  members = [
    "serviceAccount:${google_service_account.frontend_sa.email}",
    "serviceAccount:${google_service_account.backend_sa.email}",
  ]
}

# Access to Frontend.

resource "google_iap_web_iam_binding" "binding" {
  role = "roles/iap.httpsResourceAccessor"
  members = [
    "domain:google.com",
  ]
}