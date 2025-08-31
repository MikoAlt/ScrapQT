import sys
import os
import random
import hashlib

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.scraper.base_scraper import BaseScraper

class PremiumScraper(BaseScraper):
    """
    A premium e-commerce scraper that focuses on high-end products.
    """
    
    def __init__(self):
        super().__init__()
        # Premium product templates
        self.premium_templates = {
            'laptop': [
                {'brand': 'AppleTech', 'model': 'MacBook Pro Max', 'specs': '64GB RAM, 2TB SSD, M2 Ultra', 'price_range': (2500, 6000)},
                {'brand': 'DellXPS', 'model': 'Creator Edition', 'specs': '32GB RAM, 1TB SSD, RTX 4090', 'price_range': (3000, 5000)},
                {'brand': 'ThinkPad', 'model': 'X1 Carbon Ultimate', 'specs': '32GB RAM, 1TB SSD, Intel i7', 'price_range': (2000, 3500)},
            ],
            'smartphone': [
                {'brand': 'iPhone', 'model': 'Pro Max 256GB', 'specs': '256GB, 6.7" ProMotion, Triple Camera', 'price_range': (1100, 1600)},
                {'brand': 'Samsung', 'model': 'Galaxy Ultra S24', 'specs': '512GB, 6.8" Dynamic AMOLED, S Pen', 'price_range': (1200, 1800)},
                {'brand': 'Google', 'model': 'Pixel Pro 8', 'specs': '256GB, 6.7" LTPO OLED, AI Camera', 'price_range': (900, 1400)},
            ],
            'mouse': [
                {'brand': 'Logitech', 'model': 'MX Master 3S', 'specs': 'Wireless, Precision Scroll, 4000 DPI', 'price_range': (80, 120)},
                {'brand': 'Razer', 'model': 'Basilisk V3 Pro', 'specs': 'Wireless, RGB, 30000 DPI, Pro Switches', 'price_range': (120, 160)},
            ],
            'keyboard': [
                {'brand': 'Keychron', 'model': 'K2 Wireless', 'specs': 'Hot-swap, Aluminum, Brown Switches', 'price_range': (80, 150)},
                {'brand': 'Corsair', 'model': 'K100 RGB', 'specs': 'Optical Switches, RGB, Premium Build', 'price_range': (200, 250)},
            ],
            'headset': [
                {'brand': 'Sony', 'model': 'WH-1000XM5', 'specs': 'ANC, Hi-Res Audio, 30hr Battery', 'price_range': (300, 400)},
                {'brand': 'Bose', 'model': 'QuietComfort Ultra', 'specs': 'Premium ANC, Spatial Audio, Comfort', 'price_range': (350, 450)},
            ]
        }
    
    @property
    def ecommerce_name(self) -> str:
        return "PremiumElectronics"
    
    def _get_product_category(self, query: str) -> str:
        """Determine product category from query"""
        query_lower = query.lower()
        for category in self.premium_templates.keys():
            if category in query_lower:
                return category
        
        # Default mapping for common terms
        if any(word in query_lower for word in ['gaming', 'computer', 'pc']):
            return 'laptop'
        elif any(word in query_lower for word in ['phone', 'mobile', 'iphone', 'samsung']):
            return 'smartphone'
        else:
            return random.choice(list(self.premium_templates.keys()))
    
    def scrape(self, query: str) -> list[dict]:
        """
        Simulates scraping premium product data.
        """
        print(f"Scraping {self.ecommerce_name} for '{query}'...")
        
        category = self._get_product_category(query)
        templates = self.premium_templates.get(category, self.premium_templates['laptop'])
        
        # Generate 2-4 premium products
        num_products = random.randint(2, 4)
        products = []
        
        # Use query hash for consistency
        query_hash = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
        random.seed(query_hash)
        
        for i in range(num_products):
            template = random.choice(templates)
            is_used = random.random() < 0.3  # 30% chance of being used for premium items
            
            product_seed = query_hash + i * 2000
            random.seed(product_seed)
            
            # Premium pricing
            min_price, max_price = template['price_range']
            price = random.uniform(min_price, max_price)
            if is_used:
                price *= random.uniform(0.7, 0.85)  # Smaller discount for premium used items
            price = round(price / 10) * 10  # Round to nearest $10
            
            # High review scores for premium products
            review_score = round(random.uniform(4.2, 4.9), 1)
            review_count = random.randint(50, 800)
            
            # Premium product title
            condition = "Certified Refurbished" if is_used else "Brand New"
            title = f"{template['brand']} {template['model']} - {condition}"
            
            # Premium description
            description = f"Premium {template['brand']} {template['model']} featuring {template['specs']}. "
            if is_used:
                description += "Certified refurbished with full warranty. "
            description += f"Exceptional build quality and performance. Highly rated by {review_count} verified customers."
            
            # Premium product URL
            product_id = f"premium-{category}-{abs(hash(f'{query}-{i}')) % 10000}"
            link = f'https://premiumelectronics.com/products/{product_id}'
            
            # Premium styling for images
            premium_colors = ['1A237E', '4A148C', 'BF360C', '1B5E20', 'E65100']
            color = premium_colors[i % len(premium_colors)]
            brand_code = template['brand'][:6].replace(' ', '')
            image_url = f'https://via.placeholder.com/500x400/{color}/white?text={brand_code}+Premium'
            
            products.append({
                'title': title,
                'price': price,
                'review_score': review_score,
                'review_count': review_count,
                'link': link,
                'is_used': is_used,
                'image_url': image_url,
                'description': description,
                'category': category,
                'brand': template['brand'],
                'model': template['model'],
                'specifications': template['specs']
            })
        
        random.seed()
        return products
