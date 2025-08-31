#!/usr/bin/env python3

import sys
sys.path.append('.')

from config_manager import ConfigManager

def test_config_manager():
    """Test the configuration manager functionality"""
    print("=== Testing Configuration Manager ===\n")
    
    # Initialize config manager
    config = ConfigManager()
    
    print("1. Testing API Key Validation:")
    test_keys = [
        "AIzaSyBtester123456789",  # Valid format
        "sk-test123456789",        # Valid format  
        "invalid",                 # Invalid - too short
        "randomstring123456789",   # Invalid - wrong prefix
        "",                        # Invalid - empty
    ]
    
    for key in test_keys:
        is_valid = config.validate_api_key_format(key)
        print(f"   '{key}': {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    print("\n2. Testing API Key Storage:")
    
    # Save a test API key
    test_api_key = "AIzaSyBtester123456789"
    try:
        key_id = config.save_api_key(test_api_key, "Test Key 1")
        print(f"   ✓ Saved API key with ID: {key_id}")
    except Exception as e:
        print(f"   ✗ Failed to save API key: {e}")
        return
    
    # Save another key
    test_api_key2 = "AIzaSyBother987654321"
    try:
        key_id2 = config.save_api_key(test_api_key2, "Test Key 2")
        print(f"   ✓ Saved second API key with ID: {key_id2}")
    except Exception as e:
        print(f"   ✗ Failed to save second API key: {e}")
    
    print("\n3. Testing API Key Retrieval:")
    
    saved_keys = config.get_saved_api_keys()
    print(f"   Found {len(saved_keys)} saved keys:")
    for key_info in saved_keys:
        print(f"     - {key_info['name']} (ID: {key_info['key_id']}, Hash: {key_info['key_hash']})")
    
    print("\n4. Testing Last Used Key:")
    
    last_used = config.get_last_used_key_id()
    print(f"   Last used key ID: {last_used}")
    
    # Mark first key as used
    config.mark_api_key_used(key_id)
    print(f"   ✓ Marked key {key_id} as used")
    
    last_used_after = config.get_last_used_key_id()
    print(f"   Last used key ID after marking: {last_used_after}")
    
    print("\n5. Testing Key Removal:")
    
    # Remove the second key
    removed = config.remove_api_key(key_id2)
    print(f"   ✓ Removed key {key_id2}: {removed}")
    
    # Check remaining keys
    remaining_keys = config.get_saved_api_keys()
    print(f"   Remaining keys: {len(remaining_keys)}")
    for key_info in remaining_keys:
        print(f"     - {key_info['name']} (ID: {key_info['key_id']})")
    
    print("\n=== Configuration Manager Test Complete ===")

if __name__ == "__main__":
    test_config_manager()
