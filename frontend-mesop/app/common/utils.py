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

import re


def extract_links(text: str) -> list[str]:
  """
  Extracts all URLs (links) from a given text string into a list of strings.

  Args:
    text (str): The input text string potentially containing links.

  Returns:
    A list of strings, where each string is a URL found in the text.
    Returns an empty list if no links are found.
  """
  url_pattern = re.compile(
      r'(?:https?://|www\.)'  # Matches http://, https://, or www.
      r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+'  # Matches domain parts
      r'[a-zA-Z]{2,6}'  # Matches TLD (e.g., com, org, net, co.uk)
      r'(?:[/][a-zA-Z0-9.,?\'\\+&%$#=~_-]*)*'  # Matches optional path, query, fragment
  )
  return url_pattern.findall(text)
