resource "time_static" "creation_time" {
  triggers = {
    frontend_create_time = data.google_artifact_registry_docker_image.frontend.build_time
    backend_create_time = data.google_artifact_registry_docker_image.backend.build_time
  }
}

resource "time_static" "update_time" {
  triggers = {
    frontend_update_time = data.google_artifact_registry_docker_image.frontend.update_time
    backend_update_time = data.google_artifact_registry_docker_image.backend.update_time
  }
}

locals {
  deploy_id   = "av_assistant_${var.project_id}"
  deploy_infra    = "gcp"
  deploy_created_time = time_static.creation_time.rfc3339
  deploy_updated_time = time_static.update_time.rfc3339
}