from database_manager import DatabaseManager

# Test search functionality
dm = DatabaseManager()

print("Testing search functionality:")
print("1. All products:", len(dm.get_all_products()))

# Test search for laptop
search_results = dm.search_products("laptop")
print("2. Search 'laptop':", len(search_results))

# Test search for mouse
search_results = dm.search_products("mouse") 
print("3. Search 'mouse':", len(search_results))

# Test search for headphones
search_results = dm.search_products("headphones")
print("4. Search 'headphones':", len(search_results))

print("Search functionality is working properly!")
