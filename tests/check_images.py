from database_manager import DatabaseManager

dm = DatabaseManager()
products = dm.get_all_products()
print(f'Total products: {len(products)}')
for i, p in enumerate(products):
    print(f'{i+1}. {p["title"]} - Image: {p.get("image_url", "None")}')
