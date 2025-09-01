#!/usr/bin/env python3
"""
Tokopedia Product Data Scraper
Takes a product URL and extracts all data needed for the database
"""

import json
import time
import hashlib
import argparse
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from database_manager import DatabaseManager
from db_config import DB_CONFIG


class TokopediaProductScraper:
    """Extract product data from Tokopedia product pages"""
    
    def __init__(self):
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
    
    def _clean_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and formatting
        price_clean = re.sub(r'[^\d,.]', '', price_text)
        price_clean = price_clean.replace(',', '').replace('.', '')
        
        try:
            # Tokopedia prices are in Rupiah, usually without decimal
            return float(price_clean) if price_clean else None
        except:
            return None
    
    def _extract_rating(self, rating_text: str) -> Optional[float]:
        """Extract numeric rating from text"""
        if not rating_text:
            return None
        
        # Look for rating pattern like "4.5" or "4,5"
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
        
        # Look for numbers in review text
        count_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:rb|ribu|k|juta)?', review_text.lower())
        if count_match:
            count_str = count_match.group(1)
            try:
                count = float(count_str)
                # Handle "rb/ribu" (thousands) and "juta" (millions) multipliers
                if 'rb' in review_text.lower() or 'ribu' in review_text.lower() or 'k' in review_text.lower():
                    count *= 1000
                elif 'juta' in review_text.lower():
                    count *= 1000000
                return int(count)
            except:
                return None
        return None
    
    def scrape_product(self, url: str) -> Dict[str, Any]:
        """Scrape product data from URL - direct page extraction only"""
        try:
            self.driver = self._setup_driver()
            print(f"� Extracting data from: {url}")
            
            # Go directly to the product page
            self.driver.get(url)
            time.sleep(3)
            
            # Get page source for BeautifulSoup parsing
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract product data using multiple selector strategies
            product_data = {
                'link': url,
                'ecommerce': 'Tokopedia',
                'url_hash': hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
            }
            
            # Extract title
            title_selectors = [
                '[data-testid="lblPDPDetailProductName"]',
                'h1[data-testid*="product"]',
                'h1',
                '.css-1os9jjn',
                '[data-testid*="title"]'
            ]
            
            title = None
            for selector in title_selectors:
                elements = soup.select(selector)
                if elements:
                    title = elements[0].get_text(strip=True)
                    break
            
            if not title:
                # Try Selenium selectors if BeautifulSoup fails
                for selector in title_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        title = element.text.strip()
                        if title:
                            break
                    except:
                        continue
            
            product_data['title'] = title or 'Unknown Product'
            print(f"  📝 Title: {product_data['title']}")
            
            # Extract price
            price_selectors = [
                '[data-testid="lblPDPDetailProductPrice"]',
                '.price',
                '[data-testid*="price"]',
                '.css-1ksb19c',
                '.css-h66vau'
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
            print(f"  💰 Price: {price}")
            
            # Extract rating and review count - try more specific selectors
            rating_selectors = [
                '[data-testid="lblPDPDetailProductRatingNumber"]',
                '[data-testid*="rating"]',
                '.rating',
                '[data-testid*="review"]',
                '.css-153qjw7',
                '.css-t70v7i',
                '[class*="rating"]'
            ]
            
            review_count_selectors = [
                '[data-testid="lblPDPDetailProductRatingCounter"]', 
                '[data-testid*="review-count"]',
                '[data-testid*="counter"]',
                '.review-count',
                '[class*="review"]'
            ]
            
            review_score = None
            review_count = None
            
            # Try rating extraction
            for selector in rating_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    print(f"    🔍 Found rating text: '{text}'")
                    rating = self._extract_rating(text)
                    if rating:
                        review_score = rating
                        break
                if review_score:
                    break
            
            # Try review count extraction  
            for selector in review_count_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    print(f"    🔍 Found review count text: '{text}'")
                    count = self._extract_review_count(text)
                    if count:
                        review_count = count
                        break
                if review_count:
                    break
            
            product_data['review_score'] = review_score
            product_data['review_count'] = review_count
            print(f"  ⭐ Rating: {review_score} ({review_count} reviews)")
            
            # Extract description
            desc_selectors = [
                '[data-testid="lblPDPDescriptionProduk"]',
                '.description',
                '[data-testid*="description"]',
                '.css-1k1relq'
            ]
            
            description = None
            for selector in desc_selectors:
                elements = soup.select(selector)
                if elements:
                    description = elements[0].get_text(strip=True)[:500]  # Limit description length
                    break
            
            product_data['description'] = description
            print(f"  📄 Description: {description[:100] if description else 'None'}...")
            
            # Extract image URL - ensure it's complete
            img_selectors = [
                'img[data-testid*="PDPMainImage"]',
                'img[data-testid*="product"]',
                '.product-image img',
                'img[src*="images.tokopedia.net"]',
                'img[alt*="product"]',
                'img[src*="tokopedia"]'
            ]
            
            image_url = None
            for selector in img_selectors:
                elements = soup.select(selector)
                if elements:
                    src = elements[0].get('src')
                    if src:
                        # Ensure complete URL
                        if src.startswith('//'):
                            image_url = 'https:' + src
                        elif src.startswith('/'):
                            image_url = 'https://www.tokopedia.com' + src
                        elif src.startswith('http'):
                            image_url = src
                        
                        if image_url and 'tokopedia' in image_url:
                            print(f"    🔍 Found image: {image_url}")
                            break
            
            product_data['image_url'] = image_url
            print(f"  🖼️  Image: {image_url if image_url else 'None'}")
            
            # Determine if product is used (simple heuristic)
            title_lower = (title or '').lower()
            desc_lower = (description or '').lower()
            is_used = any(keyword in title_lower + ' ' + desc_lower for keyword in 
                         ['bekas', 'second', 'preloved', 'used', 'seken'])
            
            product_data['is_used'] = is_used
            print(f"  🏷️  Used: {is_used}")
            
            return product_data
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return {
                'link': url,
                'ecommerce': 'Tokopedia',
                'title': f'Error: {str(e)}',
                'url_hash': hashlib.sha256(url.encode('utf-8')).hexdigest()[:16],
                'price': None,
                'review_score': None,
                'review_count': None,
                'description': None,
                'image_url': None,
                'is_used': False
            }
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_to_database(self, product_data: Dict[str, Any], query_text: str) -> bool:
        """Save product data to database"""
        try:
            db = DatabaseManager()
            
            # First, ensure query exists
            with DB_CONFIG.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert or get query
                cursor.execute("INSERT OR IGNORE INTO queries (query_text) VALUES (?)", (query_text,))
                cursor.execute("SELECT id FROM queries WHERE query_text = ?", (query_text,))
                query_id = cursor.fetchone()[0]
                
                # Insert product
                cursor.execute("""
                    INSERT OR IGNORE INTO products 
                    (title, price, review_score, review_count, link, ecommerce, is_used, 
                     description, query_id, image_url, url_hash, sentiment_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_data['title'],
                    product_data['price'],
                    product_data['review_score'],
                    product_data['review_count'],
                    product_data['link'],
                    product_data['ecommerce'],
                    product_data['is_used'],
                    product_data['description'],
                    query_id,
                    product_data['image_url'],
                    product_data['url_hash'],
                    None  # sentiment_score will be filled later
                ))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    print(f"✅ Saved to database: {product_data['title']}")
                    return True
                else:
                    print(f"⚠️  Product already exists in database: {product_data['title']}")
                    return False
                    
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Debug Tokopedia Product Data Extraction')
    parser.add_argument('url', help='Product URL to extract data from')
    parser.add_argument('--query', default='debug', help='Query name for context')
    parser.add_argument('--output', help='Save JSON output to file (optional)')
    
    args = parser.parse_args()
    
    scraper = TokopediaProductScraper()
    
    print(f"� Debug Mode - Product Data Extraction")
    print(f"🔗 URL: {args.url}")
    print(f"� Query Context: {args.query}")
    print("-" * 60)
    
    # Extract product data (no database operations)
    product_data = scraper.scrape_product(args.url)
    
    # Save to JSON if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON saved to: {args.output}")
    
    print("-" * 60)
    print(f"✅ Extraction completed!")
    print(f"📊 Product: {product_data['title']}")
    print(f"💰 Price: Rp {product_data['price']:,.0f}" if product_data['price'] else "💰 Price: Not found")
    print(f"⭐ Rating: {product_data['review_score']} ({product_data['review_count']} reviews)")
    print(f"�️  Image: {product_data['image_url'] if product_data['image_url'] else 'Not found'}")
    print(f"📄 Description: {product_data['description'][:100] if product_data['description'] else 'Not found'}...")
    print(f"🏷️  Used: {product_data['is_used']}")
    
    return product_data


if __name__ == "__main__":
    main()
