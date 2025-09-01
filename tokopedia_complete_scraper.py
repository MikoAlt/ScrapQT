#!/usr/bin/env python3
"""
Tokopedia Complete Scraper
Finds URLs + Extracts product data in one pipeline
Ready for ScrapQT integration
"""

import json
import time
import hashlib
import argparse
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


class TokopediaCompleteScraper:
    """Complete Tokopedia scraper: URL finding + Parallel product data extraction"""
    
    def __init__(self, max_workers: int = 10):
        self.base_url = "https://www.tokopedia.com"
        self.driver = None
        self.max_workers = max_workers  # Number of parallel threads
        self._lock = threading.Lock()  # Thread safety for progress updates
    
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
        
        # Blacklist specific domains and paths
        blacklisted_patterns = [
            'seller.tokopedia.com',
            'help.tokopedia.com',
            'blog.tokopedia.com',
            '/help/',
            '/blog/',
            '/ta/',
            '/edu/',
            '/discovery/'  # Added to filter out discovery/promo pages
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
    
    def _search_homepage(self, query: str) -> bool:
        """Search via homepage"""
        try:
            print(f"🏠 Searching homepage for: '{query}'")
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
    
    def find_urls(self, query: str, max_urls: int = 120) -> List[str]:
        """Find product URLs for a query"""
        urls = set()
        
        try:
            self.driver = self._setup_driver()
            print(f"🔍 Finding URLs for: '{query}' (max: {max_urls})")
            
            # Search
            if not self._search_homepage(query):
                # Fallback to direct URL
                search_url = f"{self.base_url}/search?q={query.replace(' ', '+')}"
                print(f"  📋 Fallback to direct search: {search_url}")
                self.driver.get(search_url)
                time.sleep(3)
            
            # Scroll and collect URLs
            attempts = 0
            while len(urls) < max_urls and attempts < 50:  # Increased attempts for more products
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
            
            print(f"  ✅ Found {len(urls)} URLs")
            return list(urls)[:max_urls]
            
        except Exception as e:
            print(f"❌ Error finding URLs: {e}")
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
    
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
    
    def extract_product_data(self, url: str, index: int = 0, total: int = 0) -> Dict[str, Any]:
        """Extract product data from URL - thread-safe version"""
        driver = None
        try:
            # Create separate driver instance for each thread
            driver = self._setup_driver()
            
            with self._lock:
                print(f"[{index}/{total}] 📄 Extracting: {url[:60]}...")
            
            driver.get(url)
            time.sleep(2)  # Reduced sleep for parallel processing
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            product_data = {
                'link': url,
                'ecommerce': 'Tokopedia',
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
            
            product_data['price'] = price
            
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
            
            product_data['review_score'] = review_score
            product_data['review_count'] = review_count
            
            # Extract description
            desc_selectors = [
                '[data-testid="lblPDPDescriptionProduk"]',
                '.description'
            ]
            
            description = None
            for selector in desc_selectors:
                elements = soup.select(selector)
                if elements:
                    description = elements[0].get_text(strip=True)[:500]
                    break
            
            product_data['description'] = description
            
            # Extract image URL
            img_selectors = [
                'img[data-testid*="PDPMainImage"]',
                'img[src*="images.tokopedia.net"]'
            ]
            
            image_url = None
            for selector in img_selectors:
                elements = soup.select(selector)
                if elements:
                    src = elements[0].get('src')
                    if src:
                        if src.startswith('//'):
                            image_url = 'https:' + src
                        elif src.startswith('/'):
                            image_url = 'https://www.tokopedia.com' + src
                        elif src.startswith('http'):
                            image_url = src
                        
                        if image_url and 'tokopedia' in image_url:
                            break
            
            product_data['image_url'] = image_url
            
            # Determine if used by checking "Kondisi" field
            is_used = False
            try:
                # Look for condition information - more reliable than text search
                # Find elements that contain "Kondisi:" text (using 'string' instead of deprecated 'text')
                kondisi_elements = soup.find_all(string=re.compile(r'Kondisi', re.IGNORECASE))
                
                kondisi_text = None
                for element in kondisi_elements:
                    # Get the parent element and look for the condition value
                    parent = element.parent
                    if parent:
                        # Look for siblings or nearby elements with the condition value
                        next_elements = parent.find_all(['span', 'div'], class_=['main', 'condition'])
                        for elem in next_elements:
                            text = elem.get_text(strip=True).lower()
                            if text and text in ['baru', 'bekas', 'second', 'preloved']:
                                kondisi_text = text
                                break
                        
                        # Also check next siblings for condition text
                        if not kondisi_text:
                            # Look at parent's siblings for the condition value
                            for sibling in parent.find_next_siblings(['span', 'div']):
                                sibling_text = sibling.get_text(strip=True).lower()
                                if sibling_text and any(cond in sibling_text for cond in ['baru', 'bekas', 'second', 'preloved']):
                                    kondisi_text = sibling_text
                                    break
                        
                        if kondisi_text:
                            break
                
                # If we found kondisi field, check its value
                if kondisi_text:
                    is_used = any(keyword in kondisi_text for keyword in ['bekas', 'second', 'preloved'])
                    with self._lock:
                        print(f"    🔍 Kondisi: {kondisi_text} -> {'Used' if is_used else 'New'}")
                else:
                    # Fallback to text search in title and description
                    title_lower = (title or '').lower()
                    desc_lower = (description or '').lower()
                    is_used = any(keyword in title_lower + ' ' + desc_lower for keyword in 
                                ['bekas', 'second', 'preloved', 'used', 'seken'])
                    with self._lock:
                        print(f"    🔍 Kondisi: Not found, fallback -> {'Used' if is_used else 'New'}")
                    
            except Exception:
                # If kondisi detection fails, fallback to text search
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
                print(f"    ✅ {product_data['title'][:50]}...")
                if product_data['price']:
                    print(f"    💰 Rp {product_data['price']:,.0f}")
                else:
                    print(f"    💰 Price not available")
                if product_data['review_score']:
                    print(f"    ⭐ {product_data['review_score']} ({product_data['review_count']} reviews)")
                else:
                    print(f"    ⭐ No reviews yet")
            
            return product_data
            
        except Exception as e:
            error_msg = str(e)
            with self._lock:
                print(f"    ❌ Error extracting {url[:50]}...: {error_msg}")
            
            # Return error product data with minimal info
            return {
                'link': url,
                'ecommerce': 'Tokopedia',
                'title': f'SCRAPE_ERROR: {error_msg[:100]}',
                'url_hash': hashlib.sha256(url.encode('utf-8')).hexdigest()[:16],
                'price': None,
                'review_score': None,
                'review_count': None,
                'description': None,
                'image_url': None,
                'is_used': False,
                'scrape_error': True,  # Flag to identify failed scrapes
                'error_message': error_msg
            }
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass  # Ignore cleanup errors in parallel processing
    
    def scrape_complete(self, query: str, max_products: int = 100) -> List[Dict[str, Any]]:
        """Complete pipeline: Find URLs + Extract product data in parallel"""
        start_time = time.time()
        
        print(f"\n🚀 TOKOPEDIA PARALLEL SCRAPER")
        print(f"🔍 Query: {query}")
        print(f"📊 Max products: {max_products}")
        print(f"🧵 Workers: {self.max_workers}")
        print("="*60)
        
        try:
            # Step 1: Find URLs
            print("\n📍 PHASE 1: Finding Product URLs")
            urls = self.find_urls(query, max_products + 5)  # Get a few extra
            
            if not urls:
                print("❌ No URLs found!")
                return []
            
            print(f"✅ Found {len(urls)} product URLs")
            
            # Step 2: Extract data in parallel
            print(f"\n🔄 PHASE 2: Extracting Product Data (Parallel)")
            print(f"Using {self.max_workers} parallel workers...")
            
            all_products = []
            failed_products = []
            target_urls = urls[:max_products]  # Limit to requested amount
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all extraction tasks
                future_to_url = {
                    executor.submit(self.extract_product_data, url, i+1, len(target_urls)): url 
                    for i, url in enumerate(target_urls)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        product_data = future.result(timeout=60)  # 60 second timeout per product
                        if product_data:
                            if product_data.get('scrape_error', False):
                                failed_products.append(product_data)
                            else:
                                all_products.append(product_data)
                    except Exception as e:
                        print(f"❌ Critical failure extracting {url[:50]}...: {e}")
                        # Create error entry for critical failures
                        failed_products.append({
                            'link': url,
                            'ecommerce': 'Tokopedia',
                            'title': f'CRITICAL_ERROR: {str(e)[:100]}',
                            'url_hash': hashlib.sha256(url.encode('utf-8')).hexdigest()[:16],
                            'price': None,
                            'review_score': None,
                            'review_count': None,
                            'description': None,
                            'image_url': None,
                            'is_used': False,
                            'scrape_error': True,
                            'error_message': str(e)
                        })
            
            # Final summary
            elapsed = time.time() - start_time
            print("\n" + "="*60)
            print(f"✅ SCRAPING COMPLETE")
            print(f"📊 Products successfully extracted: {len(all_products)}")
            if failed_products:
                print(f"❌ Failed extractions: {len(failed_products)}")
                print(f"📊 Success rate: {len(all_products)/(len(all_products)+len(failed_products))*100:.1f}%")
            print(f"⏱️  Total time: {elapsed:.1f} seconds")
            if all_products:
                print(f"⚡ Average: {elapsed/len(all_products):.1f} seconds per successful product")
            
            # Return successful products only, but include failed ones for debugging if needed
            return all_products
            
        except Exception as e:
            print(f"❌ Critical error in scrape_complete: {e}")
            return []


def main():
    parser = argparse.ArgumentParser(description='Complete Tokopedia Scraper')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--max-products', type=int, default=100, help='Max products to scrape')
    parser.add_argument('--output', default='tokopedia_complete.json', help='Output file')
    
    args = parser.parse_args()
    
    scraper = TokopediaCompleteScraper()
    products = scraper.scrape_complete(args.query, args.max_products)
    
    if products:
        # Filter out error products for saving clean results
        clean_products = [p for p in products if not p.get('scrape_error', False)]
        error_products = [p for p in products if p.get('scrape_error', False)]
        
        # Save clean results
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(clean_products, f, indent=2, ensure_ascii=False)
        
        # Also save errors if any (for debugging)
        if error_products:
            error_output = args.output.replace('.json', '_errors.json')
            with open(error_output, 'w', encoding='utf-8') as f:
                json.dump(error_products, f, indent=2, ensure_ascii=False)
            print(f"⚠️  Errors saved to: {error_output}")
        
        print(f"📄 Results saved to: {args.output}")
        print(f"📊 Summary:")
        print(f"  - Total products: {len(clean_products)}")
        if error_products:
            print(f"  - Failed products: {len(error_products)}")
            print(f"  - Success rate: {len(clean_products)/(len(clean_products)+len(error_products))*100:.1f}%")
        
        if clean_products:
            valid_prices = [p['price'] for p in clean_products if p['price']]
            if valid_prices:
                print(f"  - Average price: Rp {sum(valid_prices)//len(valid_prices):,.0f}")
            else:
                print(f"  - Average price: N/A")
            print(f"  - Products with reviews: {len([p for p in clean_products if p['review_score']])}")
    else:
        print("❌ No products scraped successfully")


if __name__ == "__main__":
    main()
