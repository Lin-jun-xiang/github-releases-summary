import datetime
import re
from typing import Any, Dict, List, Tuple

import aiohttp


class GitHubClient:
    def __init__(self, username: str, repo: str) -> None:
        self.username: str = username
        self.repo: str = repo
        self.api_url: str = f"https://api.github.com/repos/{username}/{repo}/releases"
        self.headers: Dict[str, str] = {"Accept": "application/vnd.github+json"}
    
    async def fetch_all_releases(self) -> List[Dict[str, Any]]:
        """
        Asynchronously fetch all releases using pagination.
        """
        results: List[Dict[str, Any]] = []
        page: int = 1
        per_page: int = 100  # maximum items per page
        async with aiohttp.ClientSession() as session:
            while True:
                url: str = f"{self.api_url}?page={page}&per_page={per_page}"
                async with session.get(url, headers=self.headers) as resp:
                    if resp.status != 200:
                        print(f"Failed to fetch releases, HTTP status code: {resp.status}")
                        break
                    data: List[Dict[str, Any]] = await resp.json()
                    if not data:
                        break
                    results.extend(data)
                    # If the number of items returned is less than per_page, we've reached the last page.
                    if len(data) < per_page:
                        break
                    page += 1
        return results
    
    async def get_recent_releases(self, n_days: int) -> List[Dict[str, Any]]:
        """
        Filter and return releases within the last n days.
        """
        releases: List[Dict[str, Any]] = await self.fetch_all_releases()
        now: datetime.datetime = datetime.datetime.utcnow()  # current UTC time
        cutoff: datetime.datetime = now - datetime.timedelta(days=n_days)
        filtered_releases: List[Dict[str, Any]] = []
        for release in releases:
            published_str: str = release.get("published_at")
            if not published_str:
                continue
            try:
                # Parse the UTC time string returned by GitHub
                published_at: datetime.datetime = datetime.datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                print("Error parsing time:", e)
                continue
            if published_at >= cutoff:
                filtered_releases.append({
                    "time": published_str,
                    "version": release.get("tag_name"),
                    "description": release.get("body")
                })
        return filtered_releases


def parse_repo_input(repo_input: str) -> Tuple[str, str]:
    """
    Parse the repository input (GitHub URL or username/repo format)
    and return a tuple (username, repo).
    """
    repo_input = repo_input.strip()
    if repo_input.startswith("https://github.com/"):
        pattern: str = r"https://github\.com/([^/]+)/([^/]+)"
        match = re.match(pattern, repo_input)
        if not match:
            raise ValueError("Cannot parse repository URL")
        return match.group(1), match.group(2)
    else:
        if "/" not in repo_input:
            raise ValueError("Please enter in username/repo format")
        username, repo = repo_input.split("/", 1)
        return username, repo
