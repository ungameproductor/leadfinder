from __future__ import annotations

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


def allowed_by_robots(client: httpx.Client, url: str, user_agent: str, timeout: float) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = client.get(robots_url, timeout=timeout, follow_redirects=True)
        if response.status_code >= 400:
            return True
        parser = RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser.can_fetch(user_agent, url)
    except Exception:
        return True
