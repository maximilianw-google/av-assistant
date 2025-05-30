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

FROM python:3.12-slim

ENV PYTHONUNBUFFERED True

WORKDIR /backend

# Copy the service's requirements file
COPY requirements.txt .

# Install the service-specific dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the service's code 

COPY . .
RUN ls -R
# Expose the service's port
EXPOSE 8080

# Command to run the service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]