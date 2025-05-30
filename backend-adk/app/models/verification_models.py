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

"""Defines the output schema for the Business Verification Analyst agent."""

from typing import Literal
import pydantic


Field = pydantic.Field


class AspectAnalysis(pydantic.BaseModel):
  """Represents the structured analysis for a single predefined aspect."""

  aspect: str = Field(
      ...,
      description=(
          "The name of the aspect being analyzed (e.g., 'Business Name"
          " Consistency')."
      ),
  )
  status: Literal["Green", "Yellow", "Red"] = Field(
      ...,
      description=(
          "The assessed status for this aspect, must be one of 'Green',"
          " 'Yellow', or 'Red'."
      ),
  )
  justification: str = Field(
      ...,
      description=(
          "Detailed justification for the status, referencing specific"
          " details or documents."
      ),
  )
  evidence_references: list[str] = Field(
      ...,
      description=(
          "A list of strings referencing specific business details keys or"
          " document identifiers (e.g., 'Business Details: business_name',"
          " 'Document: invoice.pdf')."
      ),
  )


class AnalysisResponse(pydantic.BaseModel):
  """The overall structured JSON response from the agent.

  This model should be used as the output_schema for the LlmAgent.
  """

  high_level_summary: str = Field(
      ...,
      description=(
          "A concise high-level summary (3-4 sentences) of the business based"
          " on provided details and documents."
      ),
  )
  structured_analysis: list[AspectAnalysis] = Field(
      ...,
      description=(
          "A list of analysis objects, one for each predefined aspect that"
          " was evaluated."
      ),
  )
