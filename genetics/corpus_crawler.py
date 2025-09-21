"""Genetics corpus crawler for specifications and documentation"""

import asyncio
import aiohttp
import aiofiles
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
import time
import re
import hashlib
import json
from bs4 import BeautifulSoup
import yaml
import logging
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()
logger = logging.getLogger(__name__)

class GeneticsCorpusCrawler:
    """Crawler for genetics documentation and specifications"""

    def __init__(
        self,
        output_dir: str = "data/genetics_corpus",
        max_concurrent: int = 10,
        delay_between_requests: float = 1.0,
        user_agent: str = "GeneticsRAGBot/1.0"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.max_concurrent = max_concurrent
        self.delay_between_requests = delay_between_requests
        self.user_agent = user_agent

        # Track crawled URLs to avoid duplicates
        self.crawled_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()

        # Load genetics corpus configuration
        self.corpus_config = self._load_corpus_config()

    def _load_corpus_config(self) -> Dict[str, Any]:
        """Load genetics corpus URLs and configuration"""
        return {
            "hts_specs": {
                "base_urls": [
                    "https://samtools.github.io/hts-specs/",
                    "https://samtools.github.io/hts-specs/SAMv1.pdf",
                    "https://samtools.github.io/hts-specs/VCFv4.2.pdf",
                    "https://samtools.github.io/hts-specs/BEDv1.pdf"
                ],
                "priority": 10,
                "allow_patterns": ["/SAM*", "/VCF*", "/BCF*", "/CRAM*", "/BED*", "/htsget*"],
                "deny_patterns": ["/issues", "/pulls"]
            },
            "samtools": {
                "base_urls": [
                    "https://www.htslib.org/doc/samtools.html",
                    "https://samtools.github.io/bcftools/bcftools.html"
                ],
                "priority": 9,
                "allow_patterns": ["/doc/*"],
                "deny_patterns": []
            },
            "gatk": {
                "base_urls": [
                    "https://gatk.broadinstitute.org/hc/en-us/sections/360007226651-Best-Practices-Workflows"
                ],
                "priority": 8,
                "allow_patterns": ["/hc/en-us/articles/*", "/hc/en-us/categories/*"],
                "deny_patterns": ["/community"]
            },
            "ncbi_resources": {
                "base_urls": [
                    "https://www.ncbi.nlm.nih.gov/refseq/",
                    "https://www.ncbi.nlm.nih.gov/clinvar/docs/help/"
                ],
                "priority": 7,
                "allow_patterns": ["/about*", "/faq*", "/help*", "/docs/*"],
                "deny_patterns": ["/variation*", "/rcv*"]
            },
            "bioinformatics_tools": {
                "base_urls": [
                    "https://bedtools.readthedocs.io/en/latest/",
                    "https://biopython.org/wiki/Documentation"
                ],
                "priority": 6,
                "allow_patterns": ["/*"],
                "deny_patterns": ["/edit", "/history"]
            }
        }

    async def crawl_genetics_corpus(
        self,
        max_pages_per_source: int = 50,
        include_pdfs: bool = True
    ) -> Dict[str, Any]:
        """Crawl the complete genetics corpus"""

        console.print("[cyan]Starting genetics corpus crawl...[/cyan]")

        crawl_stats = {
            "sources_crawled": 0,
            "pages_downloaded": 0,
            "pdfs_downloaded": 0,
            "errors": 0,
            "start_time": time.time()
        }

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=self.max_concurrent),
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": self.user_agent}
        ) as session:

            for source_name, config in self.corpus_config.items():
                console.print(f"[yellow]Crawling {source_name}...[/yellow]")

                try:
                    source_stats = await self._crawl_source(
                        session, source_name, config, max_pages_per_source, include_pdfs
                    )

                    crawl_stats["sources_crawled"] += 1
                    crawl_stats["pages_downloaded"] += source_stats["pages"]
                    crawl_stats["pdfs_downloaded"] += source_stats["pdfs"]
                    crawl_stats["errors"] += source_stats["errors"]

                    console.print(f"[green]Completed {source_name}: {source_stats['pages']} pages, {source_stats['pdfs']} PDFs[/green]")

                except Exception as e:
                    logger.error(f"Error crawling {source_name}: {e}")
                    crawl_stats["errors"] += 1

                # Respectful delay between sources
                await asyncio.sleep(self.delay_between_requests * 2)

        crawl_stats["duration"] = time.time() - crawl_stats["start_time"]

        # Save crawl metadata
        metadata_file = self.output_dir / "crawl_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                "crawl_stats": crawl_stats,
                "crawled_urls": list(self.crawled_urls),
                "failed_urls": list(self.failed_urls),
                "corpus_config": self.corpus_config
            }, f, indent=2)

        console.print(f"[green]Crawl completed: {crawl_stats['pages_downloaded']} pages, {crawl_stats['pdfs_downloaded']} PDFs[/green]")
        return crawl_stats

    async def _crawl_source(
        self,
        session: aiohttp.ClientSession,
        source_name: str,
        config: Dict[str, Any],
        max_pages: int,
        include_pdfs: bool
    ) -> Dict[str, Any]:
        """Crawl a single source"""

        stats = {"pages": 0, "pdfs": 0, "errors": 0}
        urls_to_crawl = set(config["base_urls"])
        crawled_urls = set()

        source_dir = self.output_dir / source_name
        source_dir.mkdir(exist_ok=True)

        with Progress() as progress:
            task = progress.add_task(f"Crawling {source_name}", total=max_pages)

            while urls_to_crawl and len(crawled_urls) < max_pages:
                current_url = urls_to_crawl.pop()

                if current_url in crawled_urls or current_url in self.crawled_urls:
                    continue

                try:
                    # Check if URL matches allow/deny patterns
                    if not self._url_allowed(current_url, config):
                        continue

                    if current_url.lower().endswith('.pdf') and include_pdfs:
                        # Download PDF
                        success = await self._download_pdf(session, current_url, source_dir)
                        if success:
                            stats["pdfs"] += 1
                    else:
                        # Crawl HTML page
                        page_data = await self._crawl_page(session, current_url, source_dir)
                        if page_data:
                            stats["pages"] += 1

                            # Extract new URLs to crawl
                            new_urls = self._extract_links(page_data["content"], current_url, config)
                            urls_to_crawl.update(new_urls - crawled_urls)

                    crawled_urls.add(current_url)
                    self.crawled_urls.add(current_url)
                    progress.advance(task)

                    # Respectful delay
                    await asyncio.sleep(self.delay_between_requests)

                except Exception as e:
                    logger.error(f"Error crawling {current_url}: {e}")
                    self.failed_urls.add(current_url)
                    stats["errors"] += 1

        return stats

    async def _crawl_page(
        self,
        session: aiohttp.ClientSession,
        url: str,
        output_dir: Path
    ) -> Optional[Dict[str, Any]]:
        """Crawl a single HTML page"""

        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None

                content = await response.text()

                # Parse HTML
                soup = BeautifulSoup(content, 'html.parser')

                # Remove navigation, ads, etc.
                for element in soup(['nav', 'footer', 'aside', '.sidebar', '.navigation']):
                    element.decompose()

                # Extract main content
                main_content = self._extract_main_content(soup)

                # Generate filename
                url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                filename = f"{url_hash}_{self._url_to_filename(url)}.json"

                # Save page data
                page_data = {
                    "url": url,
                    "title": soup.title.string if soup.title else "",
                    "content": main_content,
                    "html": str(soup),
                    "crawled_at": time.time(),
                    "source_domain": urlparse(url).netloc
                }

                async with aiofiles.open(output_dir / filename, 'w') as f:
                    await f.write(json.dumps(page_data, indent=2))

                return page_data

        except Exception as e:
            logger.error(f"Error crawling page {url}: {e}")
            return None

    async def _download_pdf(
        self,
        session: aiohttp.ClientSession,
        url: str,
        output_dir: Path
    ) -> bool:
        """Download a PDF file"""

        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return False

                # Generate filename
                url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                filename = f"{url_hash}_{Path(url).name}"

                async with aiofiles.open(output_dir / filename, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)

                # Save metadata
                metadata = {
                    "url": url,
                    "filename": filename,
                    "downloaded_at": time.time(),
                    "size_bytes": len(await response.read()) if hasattr(response, 'read') else 0
                }

                metadata_file = output_dir / f"{filename}.meta.json"
                async with aiofiles.open(metadata_file, 'w') as f:
                    await f.write(json.dumps(metadata, indent=2))

                return True

        except Exception as e:
            logger.error(f"Error downloading PDF {url}: {e}")
            return False

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML"""

        # Try common content containers
        content_selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '.post-content',
            '.entry-content',
            '#content',
            '#main'
        ]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                return content_elem.get_text(strip=True)

        # Fallback to body
        body = soup.find('body')
        if body:
            return body.get_text(strip=True)

        return soup.get_text(strip=True)

    def _extract_links(
        self,
        content: str,
        base_url: str,
        config: Dict[str, Any]
    ) -> Set[str]:
        """Extract links from page content"""

        soup = BeautifulSoup(content, 'html.parser')
        links = set()

        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)

            # Basic URL validation
            if self._is_valid_url(absolute_url) and self._url_allowed(absolute_url, config):
                links.add(absolute_url)

        return links

    def _url_allowed(self, url: str, config: Dict[str, Any]) -> bool:
        """Check if URL matches allow/deny patterns"""

        parsed = urlparse(url)
        path = parsed.path

        # Check deny patterns first
        for pattern in config.get("deny_patterns", []):
            if pattern in path:
                return False

        # Check allow patterns
        allow_patterns = config.get("allow_patterns", ["/*"])
        for pattern in allow_patterns:
            if pattern == "/*" or pattern.rstrip('*') in path:
                return True

        return False

    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc and parsed.scheme in ['http', 'https'])
        except:
            return False

    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if not path:
            path = parsed.netloc

        # Clean up path
        filename = re.sub(r'[^\w\-.]', '_', path)
        return filename[:100]  # Limit length

    def get_crawled_documents(self) -> List[Dict[str, Any]]:
        """Get all crawled documents"""

        documents = []

        for source_dir in self.output_dir.iterdir():
            if source_dir.is_dir():
                for file_path in source_dir.glob("*.json"):
                    if file_path.name.endswith('.meta.json'):
                        continue

                    try:
                        with open(file_path, 'r') as f:
                            doc_data = json.load(f)
                            doc_data['source_type'] = source_dir.name
                            documents.append(doc_data)
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")

        console.print(f"[green]Found {len(documents)} crawled documents[/green]")
        return documents

    def update_corpus_config(self, config: Dict[str, Any]):
        """Update corpus configuration"""
        self.corpus_config.update(config)

        # Save updated config
        config_file = self.output_dir / "corpus_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(self.corpus_config, f, indent=2)

    def get_crawl_stats(self) -> Dict[str, Any]:
        """Get crawling statistics"""
        return {
            "crawled_urls_count": len(self.crawled_urls),
            "failed_urls_count": len(self.failed_urls),
            "output_directory": str(self.output_dir),
            "sources_configured": len(self.corpus_config)
        }