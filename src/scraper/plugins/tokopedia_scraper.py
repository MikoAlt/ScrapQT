#!/usr/bin/env python3
"""
Tokopedia Scraper Plugin for ScrapQT
Integrates the complete Tokopedia scraper with the ScrapQT plugin system
"""
import sys
import os
import time
import re
import hashlib
import random
import threading
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.scraper.base_scraper import BaseScraper

# Import Selenium components (these will only be imported when the plugin is actually used)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class TokopediaScraper(BaseScraper):
    """
    Tokopedia scraper plugin for ScrapQT system.
    Finds URLs + Extracts product data with parallel processing.
    """
    
    def __init__(self, max_workers: int = 5):  # Reduced workers for plugin environment
        super().__init__()
        self.base_url = "https://www.tokopedia.com"
        self.max_workers = max_workers
        self._lock = threading.Lock()  # Thread safety for progress updates
    
    @property
    def ecommerce_name(self) -> str:
        return "Tokopedia"
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        if not SELENIUM_AVAILABLE:
            print("Selenium and related dependencies not available for Tokopedia scraper")
            return False
        return True
    
    def _setup_driver(self):
        """Setup hidden Chrome browser (invisible but not headless, like the original)"""
        if not self._check_dependencies():
            return None
        
        try:
            options = Options()
            options.add_argument("--window-position=-2000,-2000")  # Hide window off-screen
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("useAutomationExtension", False)
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.minimize_window()  # Minimize the window to make it invisible
            
            return driver
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            return None
    
    def _is_product_link(self, href: str) -> bool:
        """Check if URL is a product link"""
        if not href or '/search' in href or 'ta.tokopedia.com' in href:
            return False
        
        # Blacklist specific domains and paths
        blacklisted_patterns = [
            'seller.tokopedia.com',
            'help.tokopedia.com',
            'blog.tokopedia.com',
            '/help/',
            '/blog/',
            '/ta/',
            '/edu/',
            '/discovery/'  # Filter out discovery/promo pages
        ]
        
        # Check for blacklisted patterns
        for pattern in blacklisted_patterns:
            if pattern in href:
                return False
        
        if href.startswith('/'):
            href = urljoin(self.base_url, href)
        
        if 'tokopedia.com' not in href:
            return False
        
        path_parts = [part for part in urlparse(href).path.split('/') if part]
        return len(path_parts) >= 2  # store-name/product-name pattern
    
    def _search_homepage(self, driver, query: str) -> bool:
        """Search via homepage"""
        try:
            print(f"Searching Tokopedia homepage for: '{query}'")
            driver.get("https://www.tokopedia.com")
            time.sleep(3)
            
            # Find search input
            selectors = [
                'input[aria-label="Cari di Tokopedia"]',
                'input[placeholder="Cari di Tokopedia"]',
                'input[type="search"]'
            ]
            
            search_input = None
            for selector in selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
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
            
        except Exception as e:
            print(f"Error in homepage search: {e}")
            return False
    
    def _find_urls(self, query: str, max_urls: int = 50) -> List[str]:
        """Find product URLs for a query (reduced from complete scraper for plugin efficiency)"""
        if not self._check_dependencies():
            return []
        
        urls = set()
        driver = None
        
        try:
            driver = self._setup_driver()
            if not driver:
                return []
                
            print(f"Finding URLs for: '{query}' (max: {max_urls})")
            
            # Search
            if not self._search_homepage(driver, query):
                # Fallback to direct URL
                search_url = f"{self.base_url}/search?q={query.replace(' ', '+')}"
                print(f"  Fallback to direct search: {search_url}")
                driver.get(search_url)
                time.sleep(3)
            
            # Scroll and collect URLs (reduced iterations for plugin efficiency)
            attempts = 0
            while len(urls) < max_urls and attempts < 20:  # Reduced from 50 to 20
                links = driver.find_elements(By.TAG_NAME, "a")
                
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        if href and self._is_product_link(href):
                            urls.add(href)
                    except:
                        continue
                
                if len(urls) >= max_urls:
                    break
                
                # Scroll for more
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                attempts += 1
            
            print(f"  Found {len(urls)} URLs")
            return list(urls)[:max_urls]
            
        except Exception as e:
            print(f"Error finding URLs: {e}")
            return []
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _clean_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        price_clean = re.sub(r'[^\d,.]', '', price_text)
        price_clean = price_clean.replace(',', '').replace('.', '')
        
        try:
            return float(price_clean) if price_clean else None
        except:
            return None
    
    def _extract_rating(self, rating_text: str) -> Optional[float]:
        """Extract numeric rating from text"""
        if not rating_text:
            return None
        
        rating_match = re.search(r'(\d+[.,]\d+|\d+)', rating_text)
        if rating_match:
            rating_str = rating_match.group(1).replace(',', '.')
            try:
                return float(rating_str)
            except:
                return None
        return None
    
    def _extract_review_count(self, review_text: str) -> Optional[int]:
        """Extract review count from text"""
        if not review_text:
            return None
        
        count_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:rb|ribu|k|juta)?', review_text.lower())
        if count_match:
            count_str = count_match.group(1)
            try:
                count = float(count_str)
                if 'rb' in review_text.lower() or 'ribu' in review_text.lower() or 'k' in review_text.lower():
                    count *= 1000
                elif 'juta' in review_text.lower():
                    count *= 1000000
                return int(count)
            except:
                return None
        return None
    
    def _extract_product_data(self, url: str, index: int = 0, total: int = 0) -> Dict[str, Any]:
        """Extract product data from URL - thread-safe version"""
        if not self._check_dependencies():
            return self._create_error_product(url, "Dependencies not available")
        
        driver = None
        try:
            # Create separate driver instance for each thread
            driver = self._setup_driver()
            if not driver:
                return self._create_error_product(url, "Failed to setup driver")
            
            with self._lock:
                print(f"[{index}/{total}] Extracting: {url[:60]}...")
            
            driver.get(url)
            time.sleep(2)  # Reduced sleep for efficiency
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            product_data = {
                'link': url,
                'ecommerce': self.ecommerce_name,
                'url_hash': hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
            }
            
            # Extract title
            title_selectors = [
                '[data-testid="lblPDPDetailProductName"]',
                'h1[data-testid*="product"]',
                'h1'
            ]
            
            title = None
            for selector in title_selectors:
                elements = soup.select(selector)
                if elements:
                    title = elements[0].get_text(strip=True)
                    break
            
            product_data['title'] = title or 'Unknown Product'
            
            # Extract price
            price_selectors = [
                '[data-testid="lblPDPDetailProductPrice"]',
                '.price',
                '[data-testid*="price"]'
            ]
            
            price = None
            for selector in price_selectors:
                elements = soup.select(selector)
                if elements:
                    price_text = elements[0].get_text(strip=True)
                    price = self._clean_price(price_text)
                    if price:
                        break
            
            product_data['price'] = price or 0.0  # Use 0.0 instead of None
            
            # Extract rating and review count
            rating_selectors = [
                '[data-testid="lblPDPDetailProductRatingNumber"]',
                '[data-testid*="rating"]'
            ]
            
            review_count_selectors = [
                '[data-testid="lblPDPDetailProductRatingCounter"]', 
                '[data-testid*="counter"]'
            ]
            
            review_score = None
            review_count = None
            
            for selector in rating_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    rating = self._extract_rating(text)
                    if rating:
                        review_score = rating
                        break
                if review_score:
                    break
            
            for selector in review_count_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    count = self._extract_review_count(text)
                    if count:
                        review_count = count
                        break
                if review_count:
                    break
            
            product_data['review_score'] = review_score or 0.0  # Use 0.0 instead of None
            product_data['review_count'] = review_count or 0  # Use 0 instead of None
            
            # Extract description
            desc_selectors = [
                '[data-testid="lblPDPDescriptionProduk"]',
                '.description'
            ]
            
            description = None
            for selector in desc_selectors:
                elements = soup.select(selector)
                if elements:
                    description = elements[0].get_text(strip=True)[:500]  # Limit description length
                    break
            
            product_data['description'] = description or ''  # Use empty string instead of None
            
            # Extract image URL
            img_selectors = [
                'img[data-testid*="PDPMainImage"]',
                'img[src*="images.tokopedia.net"]'
            ]
            
            image_url = None
            for selector in img_selectors:
                elements = soup.select(selector)
                if elements:
                    image_url = elements[0].get('src')
                    break
            
            product_data['image_url'] = image_url or ''  # Use empty string instead of None
            
            # Determine if used by checking "Kondisi" field
            is_used = False
            try:
                kondisi_elements = soup.find_all(string=re.compile(r'Kondisi', re.IGNORECASE))
                
                kondisi_text = None
                for element in kondisi_elements:
                    parent = element.parent
                    if parent:
                        kondisi_text = parent.get_text(strip=True).lower()
                        break
                
                if kondisi_text:
                    is_used = any(keyword in kondisi_text for keyword in ['bekas', 'second', 'preloved'])
                else:
                    # Fallback to title/description search
                    title_lower = (title or '').lower()
                    desc_lower = (description or '').lower()
                    is_used = any(keyword in title_lower + ' ' + desc_lower for keyword in 
                                 ['bekas', 'second', 'preloved', 'used', 'seken'])
                    
            except Exception:
                # Final fallback
                title_lower = (title or '').lower()
                desc_lower = (description or '').lower()
                is_used = any(keyword in title_lower + ' ' + desc_lower for keyword in 
                             ['bekas', 'second', 'preloved', 'used', 'seken'])
            
            product_data['is_used'] = is_used
            
            # Validate that we got essential data
            if not product_data['title'] or product_data['title'] == 'Unknown Product':
                raise Exception("Failed to extract product title")
            
            # Thread-safe progress update
            with self._lock:
                print(f"    Success: {product_data['title'][:50]}...")
            
            return product_data
            
        except Exception as e:
            error_msg = str(e)
            with self._lock:
                print(f"    Error extracting {url[:50]}...: {error_msg}")
            
            return self._create_error_product(url, error_msg)
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _create_error_product(self, url: str, error_msg: str) -> Dict[str, Any]:
        """Create error product data for failed extractions"""
        return {
            'link': url,
            'ecommerce': self.ecommerce_name,
            'title': f'SCRAPE_ERROR: {error_msg[:100]}',
            'url_hash': hashlib.sha256(url.encode('utf-8')).hexdigest()[:16],
            'price': 0.0,  # Use 0.0 instead of None for compatibility
            'review_score': 0.0,
            'review_count': 0,
            'description': f'Error scraping product: {error_msg}',
            'image_url': '',
            'is_used': False,
            'scrape_error': True,
            'error_message': error_msg
        }
    
    def scrape(self, query: str) -> list[dict]:
        """
        Main scrape method required by BaseScraper.
        Finds URLs and extracts product data with parallel processing.
        """
        if not self._check_dependencies():
            print("Tokopedia scraper dependencies not available")
            return []
        
        start_time = time.time()
        max_products = 20  # Reasonable limit for plugin environment
        
        print(f"\nTOKOPEDIA SCRAPER PLUGIN")
        print(f"Query: {query}")
        print(f"Max products: {max_products}")
        print(f"Workers: {self.max_workers}")
        print("="*50)
        
        try:
            # Step 1: Find URLs
            print("\nPHASE 1: Finding Product URLs")
            urls = self._find_urls(query, max_products + 5)  # Get a few extra
            
            if not urls:
                print("No URLs found!")
                return []
            
            print(f"Found {len(urls)} product URLs")
            
            # Step 2: Extract data in parallel
            print(f"\nPHASE 2: Extracting Product Data (Parallel)")
            print(f"Using {self.max_workers} parallel workers...")
            
            all_products = []
            target_urls = urls[:max_products]  # Limit to requested amount
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all extraction tasks
                future_to_url = {
                    executor.submit(self._extract_product_data, url, i+1, len(target_urls)): url 
                    for i, url in enumerate(target_urls)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_url):
                    try:
                        result = future.result(timeout=30)  # 30 second timeout per product
                        # Only include successful products (filter out errors)
                        if not result.get('scrape_error', False):
                            all_products.append(result)
                    except Exception as e:
                        print(f"Thread execution error: {e}")
            
            # Final summary
            elapsed = time.time() - start_time
            print("\n" + "="*50)
            print(f"TOKOPEDIA SCRAPING COMPLETE")
            print(f"Products successfully extracted: {len(all_products)}")
            print(f"Total time: {elapsed:.1f} seconds")
            if all_products:
                print(f"Average: {elapsed/len(all_products):.1f} seconds per product")
            
            return all_products
            
        except Exception as e:
            print(f"Critical error in Tokopedia scraper: {e}")
            return []


# Plugin registration - this allows the plugin loader to find this class
def get_scraper():
    """Factory function to create the scraper instance"""
    return TokopediaScraper()


if __name__ == "__main__":
    # Test the plugin directly
    scraper = TokopediaScraper()
    print(f"Testing {scraper.ecommerce_name} scraper...")
    
    test_query = "smartphone"
    results = scraper.scrape(test_query)
    
    print(f"\nTEST RESULTS:")
    print(f"Query: {test_query}")
    print(f"Products found: {len(results)}")
    
    for i, product in enumerate(results[:3], 1):  # Show first 3 products
        print(f"\n{i}. {product.get('title', 'N/A')[:50]}...")
        print(f"   Price: Rp {product.get('price', 0):,.0f}")
        print(f"   Rating: {product.get('review_score', 'N/A')} ({product.get('review_count', 0)} reviews)")
        print(f"   URL: {product.get('link', 'N/A')[:60]}...")
