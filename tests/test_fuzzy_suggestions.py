#!/usr/bin/env python3

from database_manager import DatabaseManager

def test_fuzzy_suggestions():
    """Test the fuzzy search suggestions functionality"""
    db = DatabaseManager()
    
    # Test different partial search terms
    test_terms = ["gam", "key", "mouse", "smart", "wire", "lap"]
    
    print("=== Testing Fuzzy Query Suggestions ===\n")
    
    for term in test_terms:
        print(f"Search term: '{term}'")
        suggestions = db.get_fuzzy_query_suggestions(term, limit=5)
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
        else:
            print("  No suggestions found")
        print()

if __name__ == "__main__":
    test_fuzzy_suggestions()
