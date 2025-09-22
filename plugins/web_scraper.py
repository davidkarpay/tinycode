"""
Web Scraper Plugin

Provides web scraping and content extraction capabilities.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any
import time
from pathlib import Path

from tiny_code.plugin_system import PluginBase, PluginMetadata, PluginCommand
from tiny_code.safety_config import SafetyLevel


class WebScraperPlugin(PluginBase):
    """Plugin for web scraping and content extraction"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="web_scraper",
            version="1.0.0",
            description="Web scraping and content extraction tools",
            author="TinyCode Team",
            safety_level=SafetyLevel.STANDARD,
            commands=["scrape", "extract-links", "download-page", "scrape-table"],
            dependencies=[]
        )

    def initialize(self) -> bool:
        # Default headers to appear more like a real browser
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Register commands
        self.register_command(PluginCommand(
            name="scrape",
            description="Scrape content from a webpage",
            handler=self._scrape_command,
            safety_level=SafetyLevel.STANDARD
        ))

        self.register_command(PluginCommand(
            name="extract-links",
            description="Extract all links from a webpage",
            handler=self._extract_links_command,
            safety_level=SafetyLevel.STANDARD
        ))

        self.register_command(PluginCommand(
            name="download-page",
            description="Download complete webpage to file",
            handler=self._download_page_command,
            safety_level=SafetyLevel.STANDARD
        ))

        self.register_command(PluginCommand(
            name="scrape-table",
            description="Extract table data from webpage",
            handler=self._scrape_table_command,
            safety_level=SafetyLevel.STANDARD
        ))

        return True

    def _make_request(self, url: str, headers: Dict[str, str] = None) -> requests.Response:
        """Make HTTP request with error handling"""
        if headers is None:
            headers = self.default_headers

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch {url}: {str(e)}")

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        return text

    def _scrape_command(self, url: str, selector: str = None, output_file: str = None) -> str:
        """Handle scrape command"""
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            if selector:
                # Extract specific elements using CSS selector
                elements = soup.select(selector)
                if not elements:
                    return f"No elements found for selector: {selector}"

                content = []
                for elem in elements:
                    text = self._clean_text(elem.get_text())
                    if text:
                        content.append(text)

                result = "\n".join(content)
            else:
                # Extract main content (remove scripts, styles, nav, footer, etc.)
                for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    tag.decompose()

                # Try to find main content area
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article'))

                if main_content:
                    result = self._clean_text(main_content.get_text())
                else:
                    # Fall back to body content
                    body = soup.find('body')
                    result = self._clean_text(body.get_text()) if body else self._clean_text(soup.get_text())

            # Save to file if requested
            if output_file:
                Path(output_file).write_text(result, encoding='utf-8')
                return f"✅ Content scraped from {url} and saved to {output_file}\n\nPreview:\n{result[:500]}..."

            return f"✅ Content scraped from {url}:\n\n{result}"

        except Exception as e:
            return f"❌ Error scraping {url}: {str(e)}"

    def _extract_links_command(self, url: str, filter_pattern: str = None, output_file: str = None) -> str:
        """Handle extract-links command"""
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = self._clean_text(link.get_text())

                # Convert relative URLs to absolute
                full_url = urljoin(url, href)

                # Apply filter if provided
                if filter_pattern and not re.search(filter_pattern, full_url, re.IGNORECASE):
                    continue

                links.append({
                    'url': full_url,
                    'text': text,
                    'original_href': href
                })

            # Sort by URL
            links.sort(key=lambda x: x['url'])

            # Format output
            result_lines = [f"Found {len(links)} links on {url}:\n"]
            for link in links:
                result_lines.append(f"• {link['text'][:50]}{'...' if len(link['text']) > 50 else ''}")
                result_lines.append(f"  {link['url']}")
                result_lines.append("")

            result = "\n".join(result_lines)

            # Save to file if requested
            if output_file:
                # Save as JSON for programmatic use
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(links, f, indent=2, ensure_ascii=False)
                return f"✅ Extracted {len(links)} links from {url} and saved to {output_file}"

            return result

        except Exception as e:
            return f"❌ Error extracting links from {url}: {str(e)}"

    def _download_page_command(self, url: str, output_file: str) -> str:
        """Handle download-page command"""
        try:
            response = self._make_request(url)

            # Save the complete HTML
            with open(output_file, 'wb') as f:
                f.write(response.content)

            file_size = len(response.content)
            return f"✅ Downloaded {url} to {output_file} ({file_size:,} bytes)"

        except Exception as e:
            return f"❌ Error downloading {url}: {str(e)}"

    def _scrape_table_command(self, url: str, table_selector: str = "table", output_file: str = None) -> str:
        """Handle scrape-table command"""
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            tables = soup.select(table_selector)
            if not tables:
                return f"No tables found for selector: {table_selector}"

            all_tables_data = []

            for i, table in enumerate(tables):
                table_data = []

                # Extract headers
                headers = []
                header_row = table.find('tr')
                if header_row:
                    for th in header_row.find_all(['th', 'td']):
                        headers.append(self._clean_text(th.get_text()))

                # Extract rows
                rows = table.find_all('tr')[1:]  # Skip header row
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_data = []
                    for cell in cells:
                        row_data.append(self._clean_text(cell.get_text()))
                    if row_data:  # Only add non-empty rows
                        table_data.append(row_data)

                all_tables_data.append({
                    'table_index': i,
                    'headers': headers,
                    'rows': table_data
                })

            # Format output
            result_lines = [f"Extracted {len(all_tables_data)} table(s) from {url}:\n"]

            for table_info in all_tables_data:
                result_lines.append(f"Table {table_info['table_index']}:")
                if table_info['headers']:
                    result_lines.append(f"Headers: {' | '.join(table_info['headers'])}")

                result_lines.append(f"Rows: {len(table_info['rows'])}")
                if table_info['rows']:
                    # Show first few rows as preview
                    for i, row in enumerate(table_info['rows'][:3]):
                        result_lines.append(f"  Row {i+1}: {' | '.join(row)}")
                    if len(table_info['rows']) > 3:
                        result_lines.append(f"  ... and {len(table_info['rows']) - 3} more rows")

                result_lines.append("")

            result = "\n".join(result_lines)

            # Save to file if requested
            if output_file:
                # Save as JSON for programmatic use
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_tables_data, f, indent=2, ensure_ascii=False)
                return f"✅ Extracted table data from {url} and saved to {output_file}"

            return result

        except Exception as e:
            return f"❌ Error scraping tables from {url}: {str(e)}"