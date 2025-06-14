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

resource "google_artifact_registry_repository" "av_assistant_app" {
  project = var.project_id
  location = var.region
  repository_id = "av-assistant-app"
  format = "DOCKER"
}


import {
  to = google_artifact_registry_repository.av_assistant_app
  id = "projects/${var.project_id}/locations/${var.region}/repositories/av-assistant-app"
}

data "google_artifact_registry_docker_image" "frontend" {
  location      = google_artifact_registry_repository.av_assistant_app.location
  repository_id = google_artifact_registry_repository.av_assistant_app.repository_id
  image_name    = "frontend:latest"
}

data "google_artifact_registry_docker_image" "backend" {
  location      = google_artifact_registry_repository.av_assistant_app.location
  repository_id = google_artifact_registry_repository.av_assistant_app.repository_id
  image_name    = "backend:latest"
}