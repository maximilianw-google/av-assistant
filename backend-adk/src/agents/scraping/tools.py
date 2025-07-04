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

"""Scrapes the text content and same-domain links from a given website URL."""

import re
from urllib import parse
import bs4
import requests

BeautifulSoup = bs4.BeautifulSoup
urlparse = parse.urlparse
urljoin = parse.urljoin


def scrape_website_content_and_links(url: str) -> dict[str, str]:
  """Scrapes the text content and same-domain links from a given website URL.

  Args:
      url: The URL of the website to scrape.

  Returns:
      A dictionary containing 'text_content' and 'same_domain_links'.
  """
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/96.0.4664.110 Safari/537.36"
      ),
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
      "Accept-Language": "en-US,en;q=0.9",
      "Referer": "https://www.google.com/",
      "Connection": "keep-alive",
      "Upgrade-Insecure-Requests": "1",
  }

  try:
    page = requests.get(
        url,
        allow_redirects=True,
        timeout=15,
        headers=headers,
    )
    page.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
  except (
      requests.exceptions.RequestException,
      requests.exceptions.HTTPError,
  ) as e:
    return {
        "text_content": f"Error accessing website: {e}",
        "same_domain_links": [],
    }
  except Exception as e:
    return {
        "text_content": f"An unexpected error occurred: {e}",
        "same_domain_links": [],
    }

  page.encoding = page.apparent_encoding
  parsed = BeautifulSoup(page.text, "html.parser")

  text = parsed.get_text(" ")
  text = re.sub("[ \t]+", " ", text)
  text = re.sub("\\s+\n\\s+", "\n", text)
  text_content = text.strip()

  base_domain = urlparse(url).netloc
  same_domain_links = []
  for link in parsed.find_all("a", href=True):
    href = link["href"]
    full_url = urljoin(url, href)
    parsed_full_url = urlparse(full_url)

    if parsed_full_url.netloc == base_domain:
      same_domain_links.append(full_url)

  return {
      "text_content": text_content,
      "same_domain_links": list(set(same_domain_links)),
  }
