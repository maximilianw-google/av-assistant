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

variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for Cloud Run."
  type        = string
  default     = "us-central1"
}

variable "gemini_api_key" {
  description = "The Gemini API key."
  type        = string
}

variable "tadau_opt_in" {
  description = "Whether to opt-in to anonymous usage reporting."
  type        = string
}

# --- Optional Inputs ---
variable "service_name_prefix" {
  description = "Name for the Cloud Run service."
  type        = string
  default     = "av-assistant-app"
}

variable "tadau_api_secret" {
  description = "GA4 API Secret."
  type        = string
  default     = "0"
}

variable "tadau_measurement_id" {
  description = "GA4 Measurement ID."
  type        = string
  default     = "0"
}

