"""
Workshop Scraper for RimModManager
Fetches and parses Steam Workshop pages using stdlib only (urllib + json + re).
No external dependencies needed.
"""

import re
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger("rimmodmanager.workshop_scraper")

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

APP_ID = "294100"  # RimWorld

# Global opener with cookie support
_opener = None

def _get_opener() -> urllib.request.OpenerDirector:
    """Get a URL opener with cookie support."""
    global _opener
    if _opener is None:
        cookie_jar = http.cookiejar.CookieJar()
        cookie_handler = urllib.request.HTTPCookieProcessor(cookie_jar)
        _opener = urllib.request.build_opener(cookie_handler)
    return _opener


@dataclass
class WorkshopMod:
    """Represents a single Workshop mod."""
    workshop_id: str
    name: str = ""
    author: str = ""
    description: str = ""
    thumbnail_url: str = ""
    is_collection: bool = False
    url: str = ""


@dataclass
class WorkshopPage:
    """Represents a parsed Workshop browse page."""
    mods: list[WorkshopMod] = field(default_factory=list)
    total_results: int = 0
    current_page: int = 1
    total_pages: int = 1
    has_next: bool = False
    has_prev: bool = False
    showing_range: str = ""


def _fetch_html(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch HTML from a URL with proper headers and cookie support."""
    log.debug(f"Fetching: {url}")
    try:
        opener = _get_opener()
        request = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        with opener.open(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        log.error(f"HTTP error {e.code}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        log.error(f"URL error: {e.reason}")
        return None
    except Exception as e:
        log.error(f"Fetch error: {e}")
        return None


def parse_workshop_html(html: str) -> WorkshopPage:
    """
    Parse Steam Workshop browse page HTML.
    
    Steam Workshop embeds mod data in JavaScript SharedFileBindMouseHover() calls.
    We extract this JSON data and combine it with thumbnail URLs from the HTML.
    """
    page = WorkshopPage()

    # Extract total results: "Showing 1-30 of 54,639 entries"
    stats_match = re.search(r'Showing\s+\d+-\d+\s+of\s+([\d,]+)\s+entries', html)
    if stats_match:
        page.total_results = int(stats_match.group(1).replace(",", ""))
        page.showing_range = stats_match.group(0)

    # Extract current page from URL or pagination
    page_match = re.search(r'[?&]p=(\d+)', html)
    if page_match:
        page.current_page = int(page_match.group(1))
    else:
        start_match = re.search(r'start=(\d+)', html)
        if start_match:
            page.current_page = (int(start_match.group(1)) // 30) + 1

    # Calculate total pages
    if page.total_results > 0:
        page.total_pages = max(1, (page.total_results + 29) // 30)

    page.has_next = page.current_page < page.total_pages
    page.has_prev = page.current_page > 1

    # Extract mod data from SharedFileBindMouseHover JavaScript calls
    # Pattern: SharedFileBindMouseHover("sharedfile_ID", false, {JSON_DATA});
    js_pattern = re.compile(
        r'SharedFileBindMouseHover\s*\(\s*"sharedfile_(\d+)"\s*,\s*[^,]+,\s*(\{.*?\})\s*\)\s*;',
        re.DOTALL
    )

    js_matches = js_pattern.findall(html)
    log.info(f"Found {len(js_matches)} mod data blocks in JS")

    # Extract thumbnail URLs in order
    thumb_pattern = re.compile(
        r'<img\s+class="workshopItemPreviewImage[^"]*"\s+src="([^"]+)"'
    )
    thumbnails = thumb_pattern.findall(html)

    # Extract author names in order
    author_pattern = re.compile(
        r'class="workshop_author_link"[^>]*>([^<]+)</a>'
    )
    authors = author_pattern.findall(html)

    # Build mod list
    for i, (mod_id, json_str) in enumerate(js_matches):
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            log.warning(f"Failed to parse JSON for mod {mod_id}")
            continue

        mod = WorkshopMod(workshop_id=mod_id)
        mod.name = data.get("title", "").strip()
        
        # Clean description (remove imgur links prefix, limit length)
        desc = data.get("description", "").strip()
        # Remove leading image URLs
        desc = re.sub(r'https?://[^\s]+\.(gif|png|jpg|jpeg)\s*', '', desc)
        mod.description = desc[:300]

        # Get thumbnail
        if i < len(thumbnails):
            mod.thumbnail_url = thumbnails[i]

        # Get author
        if i < len(authors):
            mod.author = authors[i].strip()

        # Check if collection
        mod.is_collection = data.get("itemtype") == "Collection" or "Collection" in data.get("title", "")

        # Build URL
        mod.url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"

        page.mods.append(mod)

    log.info(f"Parsed {len(page.mods)} mods from workshop page")
    return page


def fetch_workshop_page(
    sort: str = "toprated",
    page: int = 1,
    search_text: str = "",
    timeout: int = 15,
) -> WorkshopPage:
    """
    Fetch and parse a Steam Workshop browse page.

    Args:
        sort: Sort order - 'toprated', 'mostrecent', 'trend', 'favorited'
        page: Page number (1-based)
        search_text: Search query text
        timeout: Request timeout in seconds

    Returns:
        WorkshopPage with parsed mod data
    """
    base_url = "https://steamcommunity.com/workshop/browse/"
    params = {
        "appid": APP_ID,
        "browsesort": sort,
        "p": page,
        "numperpage": "30",
    }

    if search_text:
        params["searchtext"] = search_text

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    html = _fetch_html(url, timeout=timeout)

    if html is None:
        return WorkshopPage()

    return parse_workshop_html(html)


def fetch_mod_details(workshop_id: str, timeout: int = 15) -> Optional[WorkshopMod]:
    """Fetch details for a single workshop mod by ID."""
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"
    html = _fetch_html(url, timeout=timeout)

    if html is None:
        return None

    mod = WorkshopMod(workshop_id=workshop_id, url=url)

    # Extract title
    title_match = re.search(
        r'<div\s+class="workshopItemTitle"[^>]*>([^<]+)</div>',
        html
    )
    if title_match:
        mod.name = title_match.group(1).strip()

    # Extract author
    author_match = re.search(
        r'<a[^>]*class="[^"]*author[^"]*"[^>]*>([^<]+)</a>',
        html
    )
    if author_match:
        mod.author = author_match.group(1).strip()

    # Extract description from JS data
    js_match = re.search(
        r'g_rgInitialAppDetails\s*=\s*(\{.*?\})\s*;',
        html,
        re.DOTALL
    )
    if js_match:
        try:
            data = json.loads(js_match.group(1))
            desc = data.get("description", "")
            mod.description = re.sub(r'<[^>]+>', '', desc)[:500]
        except json.JSONDecodeError:
            pass

    # Extract thumbnail
    thumb_match = re.search(
        r'<img[^>]+id="previewImage"[^>]+src="([^"]+)"',
        html
    )
    if thumb_match:
        mod.thumbnail_url = thumb_match.group(1)

    return mod if mod.name else None
