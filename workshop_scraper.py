"""
Workshop Scraper for RimModManager
Fetches and parses Steam Workshop pages using stdlib only.
Extracts mod metadata including requirements, dates, ratings, and categories.
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
    """Represents a single Workshop mod with full metadata."""
    workshop_id: str
    name: str = ""
    author: str = ""
    description: str = ""
    thumbnail_url: str = ""
    url: str = ""
    
    # Metadata from detail page
    file_size: str = ""
    posted_date: str = ""
    updated_date: str = ""
    tags: list[str] = field(default_factory=list)
    
    # Stats
    subscriptions: str = ""
    favorites: str = ""
    ratings: str = ""
    change_notes: int = 0
    
    # Requirements
    required_mod_ids: list[str] = field(default_factory=list)
    required_mods: list["WorkshopMod"] = field(default_factory=list)
    
    # Status
    is_collection: bool = False
    is_downloaded: bool = False
    has_all_requirements: bool = True
    missing_requirements: list[str] = field(default_factory=list)


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


# Category definitions for filtering
WORKSHOP_CATEGORIES = [
    ("🔥 Most Popular", "toprated", ""),
    ("🆕 Most Recent", "mostrecent", ""),
    ("📈 Trending", "trend", ""),
    ("⭐ Most Favorited", "favorited", ""),
    ("---", "", ""),
    ("🏗️ Buildings", "toprated", "Buildings"),
    ("🎨 Textures", "toprated", "Textures"),
    ("⚔️ Weapons", "toprated", "Weapons"),
    ("🧠 AI", "toprated", "AI"),
    ("🗺️ Maps", "toprated", "Maps"),
    ("👥 Races", "toprated", "Races"),
    ("🎭 Apparel", "toprated", "Apparel"),
    ("🔧 Tools", "toprated", "Tools"),
    ("🎮 Gameplay", "toprated", "Gameplay"),
    ("📦 Libraries", "toprated", "Libraries"),
    ("🌍 World", "toprated", "World"),
    ("📖 Story", "toprated", "Story"),
]


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
    """Parse Steam Workshop browse page HTML."""
    page = WorkshopPage()

    # Extract total results
    stats_match = re.search(r'Showing\s+\d+-\d+\s+of\s+([\d,]+)\s+entries', html)
    if stats_match:
        page.total_results = int(stats_match.group(1).replace(",", ""))
        page.showing_range = stats_match.group(0)

    # Extract current page
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

    # Extract mod data from JavaScript
    js_pattern = re.compile(
        r'SharedFileBindMouseHover\s*\(\s*"sharedfile_(\d+)"\s*,\s*[^,]+,\s*(\{.*?\})\s*\)\s*;',
        re.DOTALL
    )
    js_matches = js_pattern.findall(html)

    # Extract thumbnails and authors in order
    thumb_pattern = re.compile(r'<img\s+class="workshopItemPreviewImage[^"]*"\s+src="([^"]+)"')
    thumbnails = thumb_pattern.findall(html)

    author_pattern = re.compile(r'class="workshop_author_link"[^>]*>([^<]+)</a')
    authors = author_pattern.findall(html)

    # Build mod list
    for i, (mod_id, json_str) in enumerate(js_matches):
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            continue

        mod = WorkshopMod(workshop_id=mod_id)
        mod.name = data.get("title", "").strip()
        
        # Clean description
        desc = data.get("description", "").strip()
        desc = re.sub(r'https?://[^\s]+\.(gif|png|jpg|jpeg)\s*', '', desc)
        mod.description = desc[:300]

        if i < len(thumbnails):
            mod.thumbnail_url = thumbnails[i]
        if i < len(authors):
            mod.author = authors[i].strip()

        mod.is_collection = data.get("itemtype") == "Collection"
        mod.url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"

        page.mods.append(mod)

    log.info(f"Parsed {len(page.mods)} mods from workshop page")
    return page


def fetch_workshop_page(
    sort: str = "toprated",
    page: int = 1,
    search_text: str = "",
    tag: str = "",
    timeout: int = 15,
) -> WorkshopPage:
    """Fetch and parse a Steam Workshop browse page."""
    base_url = "https://steamcommunity.com/workshop/browse/"
    params = {
        "appid": APP_ID,
        "browsesort": sort,
        "p": page,
        "numperpage": "30",
    }

    if search_text:
        params["searchtext"] = search_text
    if tag:
        params["requiredtags[]"] = tag

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    html = _fetch_html(url, timeout=timeout)

    if html is None:
        return WorkshopPage()

    return parse_workshop_html(html)


def fetch_mod_details(workshop_id: str, timeout: int = 15) -> Optional[WorkshopMod]:
    """
    Fetch full details for a single workshop mod including:
    - File size, posted/updated dates
    - Tags, subscriptions, favorites
    - Required mod IDs (dependencies)
    """
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"
    html = _fetch_html(url, timeout=timeout)

    if html is None:
        return None

    mod = WorkshopMod(workshop_id=workshop_id, url=url)

    # Extract title
    title_match = re.search(r'<div\s+class="workshopItemTitle"[^>]*>([^<]+)</div>', html)
    if title_match:
        mod.name = title_match.group(1).strip()

    # Extract author
    author_match = re.search(r'class="workshop_author_link"[^>]*>([^<]+)</a>', html)
    if author_match:
        mod.author = author_match.group(1).strip()

    # Extract description
    desc_match = re.search(r'<div\s+class="workshopItemDescription">(.*?)</div>', html, re.DOTALL)
    if desc_match:
        desc = re.sub(r'<[^>]+>', '', desc_match.group(1))
        mod.description = desc.strip()[:500]

    # Extract thumbnail
    thumb_match = re.search(r'<img[^>]+id="previewImage"[^>]+src="([^"]+)"', html)
    if thumb_match:
        mod.thumbnail_url = thumb_match.group(1)

    # Extract file stats (size, dates)
    stats_left = re.findall(r'<div class="detailsStatLeft">([^<]+)</div>', html)
    stats_right = re.findall(r'<div class="detailsStatRight">([^<]+)</div>', html)
    
    for i, label in enumerate(stats_left):
        if i < len(stats_right):
            value = stats_right[i].strip()
            if "File Size" in label:
                mod.file_size = value
            elif "Posted" in label:
                mod.posted_date = value
            elif "Updated" in label:
                mod.updated_date = value

    # Extract tags
    tags_section = re.search(r'detailsTags(.*?)</div>', html, re.DOTALL)
    if tags_section:
        tags = re.findall(r'>([^<]+)</a>', tags_section.group(1))
        mod.tags = [t.strip() for t in tags if t.strip() and len(t.strip()) > 1]

    # Extract subscriptions
    sub_match = re.search(r'Subscriptions.*?<div[^>]*>([^<]+)</div>', html, re.DOTALL)
    if sub_match:
        mod.subscriptions = sub_match.group(1).strip()

    # Extract favorites
    fav_match = re.search(r'Favorited.*?<div[^>]*>([^<]+)</div>', html, re.DOTALL)
    if fav_match:
        mod.favorites = fav_match.group(1).strip()

    # Extract change notes count
    change_match = re.search(r'(\d+)\s+Change Notes', html)
    if change_match:
        mod.change_notes = int(change_match.group(1))

    # Extract required mod IDs (dependencies)
    # Steam shows required items as links to other workshop items
    required_section = re.search(
        r'Required Items.*?</div>(.*?)</div>',
        html, re.DOTALL
    )
    if required_section:
        req_ids = re.findall(r'id=(\d+)', required_section.group(1))
        mod.required_mod_ids = list(set(req_ids))

    # Also check for required items in a different pattern
    if not mod.required_mod_ids:
        req_links = re.findall(
            r'<a[^>]*href="[^"]*sharedfiles/filedetails/\?id=(\d+)"[^>]*class="[^"]*required[^"]*"[^>]*>',
            html
        )
        mod.required_mod_ids = list(set(req_links))

    # Check if it's a collection
    if re.search(r'workshopItemCollection|In\s+\d+\s+collection', html):
        mod.is_collection = True

    return mod if mod.name else None


def fetch_mod_requirements(workshop_id: str, downloaded_ids: set[str] = None) -> list[str]:
    """
    Fetch and return list of missing requirement mod IDs.
    Returns empty list if all requirements are met.
    """
    downloaded_ids = downloaded_ids or set()
    mod = fetch_mod_details(workshop_id)
    
    if not mod or not mod.required_mod_ids:
        return []
    
    missing = []
    for req_id in mod.required_mod_ids:
        if req_id not in downloaded_ids:
            missing.append(req_id)
    
    return missing
