#!/usr/bin/env python3
"""
Tokopedia Scraper - Simplified URL Collector
Just finds product URLs using homepage search - nothing else
"""

import json
import time
import hashlib
import argparse
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class TokopediaURLFinder:
    """Simple Tokopedia URL finder"""
    
    def __init__(self):
        self.base_url = "https://www.tokopedia.com"
        self.driver = None
    
    def _setup_driver(self):
        """Setup hidden Chrome browser"""
        options = Options()
        options.add_argument("--window-position=-2000,-2000")  # Hide window
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.minimize_window()
        
        return driver
    
    def _is_product_link(self, href: str) -> bool:
        """Check if URL is a product link"""
        if not href or '/search' in href or 'ta.tokopedia.com' in href:
            return False
        
        if href.startswith('/'):
            href = urljoin(self.base_url, href)
        
        if 'tokopedia.com' not in href:
            return False
        
        path_parts = [part for part in urlparse(href).path.split('/') if part]
        return len(path_parts) >= 2  # store-name/product-name pattern
    
    def _search_homepage(self, query: str) -> bool:
        """Search via homepage"""
        try:
            print(f"🏠 Going to homepage...")
            self.driver.get("https://www.tokopedia.com")
            time.sleep(3)
            
            # Find search input
            selectors = [
                'input[aria-label="Cari di Tokopedia"]',
                'input[placeholder="Cari di Tokopedia"]',
                'input[type="search"]'
            ]
            
            search_input = None
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        search_input = element
                        break
                if search_input:
                    break
            
            if not search_input:
                return False
            
            # Type and submit
            search_input.clear()
            for char in query:
                search_input.send_keys(char)
                time.sleep(0.05)
            
            search_input.send_keys(Keys.RETURN)
            time.sleep(3)
            return True
            
        except:
            return False
    
    def find_urls(self, query: str, max_urls: int = 30) -> List[str]:
        """Find product URLs"""
        urls = set()
        
        try:
            self.driver = self._setup_driver()
            print(f"🔍 Finding URLs for: '{query}'")
            
            # Search
            if not self._search_homepage(query):
                # Fallback to direct URL
                search_url = f"{self.base_url}/search?q={query.replace(' ', '+')}"
                self.driver.get(search_url)
                time.sleep(3)
            
            # Scroll and collect URLs
            attempts = 0
            while len(urls) < max_urls and attempts < 20:
                links = self.driver.find_elements(By.TAG_NAME, "a")
                
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        if self._is_product_link(href):
                            clean_url = urlparse(href)._replace(query='').geturl()
                            urls.add(clean_url)
                            
                            if len(urls) >= max_urls:
                                break
                    except:
                        continue
                
                if len(urls) >= max_urls:
                    break
                
                # Scroll for more
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                attempts += 1
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return list(urls)[:max_urls]


def main():
    parser = argparse.ArgumentParser(description='Find Tokopedia Product URLs')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--max-urls', type=int, default=30, help='Max URLs to find')
    parser.add_argument('--output', default='urls.json', help='Output file')
    
    args = parser.parse_args()
    
    finder = TokopediaURLFinder()
    urls = finder.find_urls(args.query, args.max_urls)
    
    if urls:
        # Save as simple list of URLs
        with open(args.output, 'w') as f:
            json.dump(urls, f, indent=2)
        
        print(f"✅ Found {len(urls)} URLs")
        print(f"📄 Saved to: {args.output}")
        
        # Show first few
        for i, url in enumerate(urls[:5], 1):
            print(f"  {i}. {url}")
    else:
        print("❌ No URLs found")


if __name__ == "__main__":
    main()
