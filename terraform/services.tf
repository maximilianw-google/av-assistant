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

resource "google_cloud_run_v2_service" "frontend" {
  project  = var.project_id
  provider = google-beta
  name     = format("%s-frontend", var.service_name_prefix)
  location = var.region
  ingress = "INGRESS_TRAFFIC_ALL"
  launch_stage = "BETA"
  iap_enabled = true
  deletion_protection = false

  template {
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }
    service_account = google_service_account.frontend_sa.email
    containers {
      image = data.google_artifact_registry_docker_image.frontend.self_link
      resources {
        startup_cpu_boost = true
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "REGION"
        value = var.region
      }
      env {
        name  = "BACKEND_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
    }
  }
}

resource "google_cloud_run_v2_service" "backend" {
  project  = var.project_id
  name     =  format("%s-backend", var.service_name_prefix)
  location = var.region
  deletion_protection = false
  provider = google-beta
  launch_stage = "BETA"
  ingress = "INGRESS_TRAFFIC_ALL"
  

  template {
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }
    service_account = google_service_account.backend_sa.email
    containers {
      ports {
        container_port = 8000
      }
      image = data.google_artifact_registry_docker_image.backend.self_link
      resources {
        startup_cpu_boost = true
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "REGION"
        value = var.region
      }
      env {
        name  = "GOOGLE_API_KEY"
        value = var.gemini_api_key
      }
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "false"
      }
    }
  }
}
