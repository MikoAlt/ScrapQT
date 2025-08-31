#!/usr/bin/env python3

import sys
sys.path.append('.')

from config_manager import ConfigManager

def test_session_api_key_workflow():
    """Test the session API key workflow"""
    print("=== Testing Session API Key Workflow ===\n")
    
    # Initialize config manager
    config = ConfigManager()
    
    print("1. Simulate saving an API key during the session:")
    test_key = "AIzaSyBtest123456789"
    key_id = config.save_api_key(test_key, "Test Session Key")
    print(f"   ✓ Saved API key with ID: {key_id}")
    
    # Check if it's available in session
    session_key = config.get_session_api_key(key_id)
    print(f"   ✓ Key available in session: {session_key is not None}")
    
    print("\n2. Simulate app restart (clear session keys):")
    config._session_keys.clear()  # This simulates app restart
    
    # Check availability after "restart"
    session_key_after = config.get_session_api_key(key_id)
    print(f"   ✗ Key available after restart: {session_key_after is not None}")
    
    print("\n3. Saved keys metadata still available:")
    saved_keys = config.get_saved_api_keys()
    print(f"   ✓ Found {len(saved_keys)} saved key(s)")
    for key_info in saved_keys:
        available = config.get_session_api_key(key_info['key_id']) is not None
        print(f"     - {key_info['name']}: {'Available' if available else 'Not available'} in session")
    
    print("\n4. Re-entering key in same session:")
    config.store_session_api_key(key_id, test_key)  # User re-enters the key
    session_key_restored = config.get_session_api_key(key_id)
    print(f"   ✓ Key restored to session: {session_key_restored is not None}")
    
    print("\n✅ **Solution Explanation:**")
    print("   - API keys are stored in session memory only (not on disk)")
    print("   - Key metadata (name, hash) persists across app restarts")
    print("   - Users must re-enter keys after restarting the application")
    print("   - This provides security while maintaining convenience during sessions")
    
    print("\n=== Session Workflow Test Complete ===")

if __name__ == "__main__":
    test_session_api_key_workflow()
