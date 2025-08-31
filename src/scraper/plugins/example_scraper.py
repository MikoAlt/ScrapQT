import sys
import os
import random
import hashlib

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.scraper.base_scraper import BaseScraper

class ExampleScraper(BaseScraper):
    """
    An enhanced example scraper for a fictional e-commerce platform.
    Generates more realistic and diverse product data.
    """
    
    def __init__(self):
        super().__init__()
        # Product templates for different categories
        self.product_templates = {
            'laptop': [
                {'brand': 'TechPro', 'model': 'UltraBook X15', 'specs': '16GB RAM, 512GB SSD, RTX 4060'},
                {'brand': 'PowerMax', 'model': 'Gaming Beast G7', 'specs': '32GB RAM, 1TB SSD, RTX 4070'},
                {'brand': 'SlimTech', 'model': 'Business Elite', 'specs': '8GB RAM, 256GB SSD, Intel Iris'},
                {'brand': 'ProGamer', 'model': 'Destroyer XV', 'specs': '16GB RAM, 1TB HDD+256GB SSD, RTX 4080'},
            ],
            'smartphone': [
                {'brand': 'PhoneTech', 'model': 'Galaxy Pro Max', 'specs': '128GB, 6.7" Display, 108MP Camera'},
                {'brand': 'MobilePro', 'model': 'Ultra X12', 'specs': '256GB, 6.1" Display, 64MP Triple Camera'},
                {'brand': 'SmartDevices', 'model': 'Pixel Ultimate', 'specs': '512GB, 6.4" OLED, 50MP AI Camera'},
                {'brand': 'TechMobile', 'model': 'PowerPhone 15', 'specs': '128GB, 6.0" Display, 48MP Camera'},
            ],
            'mouse': [
                {'brand': 'GamerPro', 'model': 'Precision X1', 'specs': 'Wireless, RGB, 25600 DPI, Ergonomic'},
                {'brand': 'TechGrip', 'model': 'Elite Gaming', 'specs': 'Wired, Programmable, 16000 DPI, Lightweight'},
                {'brand': 'OfficeMax', 'model': 'Business Silent', 'specs': 'Wireless, Silent Click, 1600 DPI'},
                {'brand': 'ProGaming', 'model': 'Tournament Pro', 'specs': 'Wired, Mechanical Switches, 32000 DPI'},
            ],
            'keyboard': [
                {'brand': 'KeyMaster', 'model': 'Mechanical Pro', 'specs': 'RGB Backlit, Blue Switches, Full Size'},
                {'brand': 'TypeMax', 'model': 'Silent Worker', 'specs': 'Wireless, Brown Switches, Compact'},
                {'brand': 'GamerKeys', 'model': 'RGB Elite', 'specs': 'Mechanical, Red Switches, TKL, RGB'},
                {'brand': 'OfficeType', 'model': 'Business Pro', 'specs': 'Membrane, Quiet, Ergonomic Design'},
            ],
            'headset': [
                {'brand': 'AudioMax', 'model': 'Gaming Pro X', 'specs': '7.1 Surround, Noise Canceling, RGB'},
                {'brand': 'SoundTech', 'model': 'Studio Elite', 'specs': 'Hi-Fi, 50mm Drivers, Professional'},
                {'brand': 'GameAudio', 'model': 'Tournament', 'specs': 'Wireless, Low Latency, 20hr Battery'},
                {'brand': 'ProSound', 'model': 'Office Comfort', 'specs': 'Lightweight, Clear Mic, All-day Comfort'},
            ]
        }
        
        # Condition descriptions
        self.conditions = {
            False: ['Brand New', 'Factory Sealed', 'New in Box', 'Unopened'],
            True: ['Like New', 'Excellent Condition', 'Minor Wear', 'Good Condition', 'Refurbished']
        }
    
    @property
    def ecommerce_name(self) -> str:
        return "ExampleCommerce"
    
    def _get_product_category(self, query: str) -> str:
        """Determine product category from query"""
        query_lower = query.lower()
        for category in self.product_templates.keys():
            if category in query_lower or any(word in query_lower for word in [category]):
                return category
        
        # Default categories for common terms
        if 'gaming' in query_lower:
            return random.choice(['laptop', 'mouse', 'keyboard', 'headset'])
        elif 'phone' in query_lower or 'mobile' in query_lower:
            return 'smartphone'
        elif 'computer' in query_lower or 'pc' in query_lower:
            return 'laptop'
        else:
            return random.choice(list(self.product_templates.keys()))
    
    def _generate_realistic_price(self, category: str, is_used: bool, base_seed: int) -> float:
        """Generate realistic prices based on category and condition"""
        # Set seed for consistent pricing per product
        random.seed(base_seed)
        
        base_prices = {
            'laptop': (800, 3000),
            'smartphone': (200, 1500),
            'mouse': (20, 150),
            'keyboard': (30, 200),
            'headset': (25, 300)
        }
        
        min_price, max_price = base_prices.get(category, (50, 500))
        base_price = random.uniform(min_price, max_price)
        
        # Apply used condition discount
        if is_used:
            discount = random.uniform(0.15, 0.45)  # 15-45% discount for used
            base_price *= (1 - discount)
        
        # Round to reasonable price points
        if base_price < 100:
            return round(base_price * 2) / 2  # Round to nearest $0.50
        else:
            return round(base_price / 5) * 5  # Round to nearest $5
    
    def scrape(self, query: str) -> list[dict]:
        """
        Simulates scraping data for the given query with realistic product data.
        """
        print(f"Scraping {self.ecommerce_name} for '{query}'...")
        
        # Determine product category
        category = self._get_product_category(query)
        templates = self.product_templates.get(category, self.product_templates['laptop'])
        
        # Generate 3-6 products for variety
        num_products = random.randint(3, 6)
        products = []
        
        # Use query hash for consistent results per query
        query_hash = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
        random.seed(query_hash)
        
        for i in range(num_products):
            template = random.choice(templates)
            is_used = random.choice([True, False]) if i > 0 else False  # First item always new
            
            # Create unique seed for this product
            product_seed = query_hash + i * 1000
            
            # Generate product title
            condition_suffix = f" ({random.choice(self.conditions[is_used])})" if is_used else ""
            title = f"{template['brand']} {template['model']}{condition_suffix}"
            
            # Generate price
            price = self._generate_realistic_price(category, is_used, product_seed)
            
            # Generate review data
            random.seed(product_seed + 100)
            review_score = round(random.uniform(3.8, 4.9), 1)
            review_count = random.randint(15, 500)
            
            # Generate product URL
            product_id = f"{category}-{i+1}-{abs(hash(query)) % 10000}"
            link = f'https://examplecommerce.com/{category}/{product_id}?query={query.replace(" ", "+")}'
            
            # Generate description
            description = f"{template['brand']} {template['model']} - {template['specs']}. "
            if is_used:
                description += f"Pre-owned item in excellent working condition. "
            description += f"Perfect for {query}. Rated {review_score}/5 by {review_count} customers."
            
            # Generate image URL with product-specific colors
            colors = ['4CAF50', 'FF5722', '2196F3', 'FF9800', '9C27B0', '607D8B']
            color = colors[i % len(colors)]
            brand_short = template['brand'][:8].replace(' ', '+')
            image_url = f'https://via.placeholder.com/400x400/{color}/white?text={brand_short}+{template["model"][:10].replace(" ", "+")}'
            
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
        
        # Reset random seed
        random.seed()
        return products
