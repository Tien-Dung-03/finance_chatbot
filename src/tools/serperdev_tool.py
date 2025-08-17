# serperdev_tool.py
import datetime
import json
import logging
import os
from typing import Any, Optional

import aiohttp
import asyncio
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/portfolio_optimization.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def _save_results_to_file(content: str) -> None:
    """Saves the search results to a file."""
    try:
        filename = f"search_results_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)
        logger.info(f"Results saved to {filename}")
    except IOError as e:
        logger.error(f"Failed to save results to file: {e}")
        raise


class SerperDevToolConfig(BaseModel):
    search_query: str = Field(..., description="Mandatory search query you want to use to search the internet")
    search_type: str = Field(default="search", description="Search type: 'search' or 'news'")
    n_results: int = Field(default=10, description="Number of results to fetch")
    country: Optional[str] = ""
    location: Optional[str] = ""
    locale: Optional[str] = ""
    save_file: bool = False


class SerperDevToolAsync:
    def __init__(self, api_key: str, base_url: str = "https://google.serper.dev"):
        self.api_key = api_key
        self.base_url = base_url

    def _get_search_url(self, search_type: str) -> str:
        allowed_search_types = ["search", "news"]
        if search_type not in allowed_search_types:
            raise ValueError(f"Invalid search type: {search_type}. Must be one of: {', '.join(allowed_search_types)}")
        return f"{self.base_url}/{search_type}"

    def _process_knowledge_graph(self, kg: dict) -> dict:
        return {
            "title": kg.get("title", ""),
            "type": kg.get("type", ""),
            "website": kg.get("website", ""),
            "imageUrl": kg.get("imageUrl", ""),
            "description": kg.get("description", ""),
            "descriptionSource": kg.get("descriptionSource", ""),
            "descriptionLink": kg.get("descriptionLink", ""),
            "attributes": kg.get("attributes", {}),
        }

    def _process_organic_results(self, organic_results: list, n_results: int) -> list:
        processed_results = []
        for result in organic_results[:n_results]:
            try:
                result_data = {
                    "title": result["title"],
                    "link": result["link"],
                    "snippet": result.get("snippet", ""),
                    "position": result.get("position"),
                }
                if "sitelinks" in result:
                    result_data["sitelinks"] = [
                        {"title": sitelink.get("title", ""), "link": sitelink.get("link", "")}
                        for sitelink in result["sitelinks"]
                    ]
                processed_results.append(result_data)
            except KeyError:
                logger.warning(f"Skipping malformed organic result: {result}")
        return processed_results

    def _process_people_also_ask(self, paa_results: list, n_results: int) -> list:
        processed_results = []
        for result in paa_results[:n_results]:
            try:
                processed_results.append({
                    "question": result["question"],
                    "snippet": result.get("snippet", ""),
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                })
            except KeyError:
                logger.warning(f"Skipping malformed PAA result: {result}")
        return processed_results

    def _process_related_searches(self, related_results: list, n_results: int) -> list:
        processed_results = []
        for result in related_results[:n_results]:
            try:
                processed_results.append({"query": result["query"]})
            except KeyError:
                logger.warning(f"Skipping malformed related search result: {result}")
        return processed_results

    def _process_news_results(self, news_results: list, n_results: int) -> list:
        processed_results = []
        for result in news_results[:n_results]:
            try:
                processed_results.append({
                    "title": result["title"],
                    "link": result["link"],
                    "snippet": result.get("snippet", ""),
                    "date": result.get("date", ""),
                    "source": result.get("source", ""),
                    "imageUrl": result.get("imageUrl", ""),
                })
            except KeyError:
                logger.warning(f"Skipping malformed news result: {result}")
        return processed_results

    async def _make_api_request(self, cfg: SerperDevToolConfig) -> dict:
        search_url = self._get_search_url(cfg.search_type)
        payload = {"q": cfg.search_query, "num": cfg.n_results}

        if cfg.country:
            payload["gl"] = cfg.country
        if cfg.location:
            payload["location"] = cfg.location
        if cfg.locale:
            payload["hl"] = cfg.locale

        headers = {"X-API-KEY": self.api_key, "content-type": "application/json"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(search_url, headers=headers, json=payload, timeout=10) as resp:
                    if resp.status != 200:
                        raise ValueError(f"Serper API request failed with status {resp.status}")
                    results = await resp.json()
                    if not results:
                        raise ValueError("Empty response from Serper API")
                    return results
            except asyncio.TimeoutError:
                logger.error("Serper API request timed out")
                raise
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error calling Serper API: {e}")
                raise

    def _process_search_results(self, results: dict, cfg: SerperDevToolConfig) -> dict:
        formatted_results = {}

        if cfg.search_type == "search":
            if "knowledgeGraph" in results:
                formatted_results["knowledgeGraph"] = self._process_knowledge_graph(results["knowledgeGraph"])
            if "organic" in results:
                formatted_results["organic"] = self._process_organic_results(results["organic"], cfg.n_results)
            if "peopleAlsoAsk" in results:
                formatted_results["peopleAlsoAsk"] = self._process_people_also_ask(results["peopleAlsoAsk"], cfg.n_results)
            if "relatedSearches" in results:
                formatted_results["relatedSearches"] = self._process_related_searches(results["relatedSearches"], cfg.n_results)
        elif cfg.search_type == "news":
            if "news" in results:
                formatted_results["news"] = self._process_news_results(results["news"], cfg.n_results)

        return formatted_results

    async def run(self, **kwargs: Any) -> dict:
        """Main function to execute search asynchronously."""
        cfg = SerperDevToolConfig(**kwargs)
        results = await self._make_api_request(cfg)

        formatted_results = {
            "searchParameters": {"q": cfg.search_query, "type": cfg.search_type, **results.get("searchParameters", {})}
        }
        formatted_results.update(self._process_search_results(results, cfg))
        formatted_results["credits"] = results.get("credits", 1)

        if cfg.save_file:
            _save_results_to_file(json.dumps(formatted_results, indent=2, ensure_ascii=False))

        return formatted_results


# Example usage
async def main():
    api_key = os.environ.get("SERPER_API_KEY", "YOUR_API_KEY_HERE")
    tool = SerperDevToolAsync(api_key)

    # Run multiple queries in parallel
    tasks = [
        tool.run(search_query="AI news", search_type="news", n_results=5, save_file=True),
        tool.run(search_query="Machine learning trends", search_type="search", n_results=5),
    ]
    results = await asyncio.gather(*tasks)

    for idx, res in enumerate(results):
        print(f"\n--- Result {idx+1} ---")
        print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
