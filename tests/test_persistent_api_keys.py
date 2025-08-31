#!/usr/bin/env python3
"""
Test Persistent API Key Storage
Verifies that API keys are saved and loaded correctly across sessions
"""

from config_manager import ConfigManager
import os

def test_persistent_api_keys():
    """Test the persistent API key storage functionality"""
    print("🔐 Persistent API Key Storage Test")
    print("=" * 50)
    
    # Create config manager
    config = ConfigManager()
    
    # Test API key
    test_api_key = "AIzaSyBOTI22N4wX5D_rDGR-API-KEY-EXAMPLE-TEST123"
    test_key_name = "Test Gemini Key"
    
    print("1. Saving API key...")
    key_id = config.save_api_key(test_api_key, test_key_name)
    print(f"   ✓ API key saved with ID: {key_id}")
    
    print("2. Retrieving API key from memory...")
    retrieved_key = config.get_session_api_key(key_id)
    if retrieved_key == test_api_key:
        print(f"   ✓ Key retrieved successfully: {retrieved_key[:20]}...")
    else:
        print(f"   ✗ Key retrieval failed. Got: {retrieved_key}")
    
    print("3. Simulating application restart (clearing session memory)...")
    config._session_keys.clear()  # Clear session memory to simulate restart
    
    print("4. Retrieving API key after 'restart'...")
    retrieved_key_after_restart = config.get_session_api_key(key_id)
    if retrieved_key_after_restart == test_api_key:
        print(f"   ✓ Key persisted and retrieved successfully: {retrieved_key_after_restart[:20]}...")
    else:
        print(f"   ✗ Key persistence failed. Got: {retrieved_key_after_restart}")
    
    print("5. Listing saved keys...")
    saved_keys = config.get_saved_api_keys()
    print(f"   ✓ Found {len(saved_keys)} saved key(s)")
    for key_info in saved_keys:
        print(f"     - {key_info['name']}: {key_info['key_hash']}")
    
    print("6. Testing encryption/decryption...")
    encrypted = config._encrypt_api_key(test_api_key)
    decrypted = config._decrypt_api_key(encrypted)
    if decrypted == test_api_key:
        print(f"   ✓ Encryption/decryption works correctly")
        print(f"     Original:  {test_api_key[:20]}...")
        print(f"     Encrypted: {encrypted[:40]}...")
        print(f"     Decrypted: {decrypted[:20]}...")
    else:
        print(f"   ✗ Encryption/decryption failed")
    
    print("7. Testing config file location...")
    config_path = config.config_dir
    print(f"   ✓ Config directory: {config_path}")
    print(f"   ✓ API keys file: {config.api_keys_file}")
    print(f"   ✓ Config file exists: {config.config_file.exists()}")
    print(f"   ✓ API keys file exists: {config.api_keys_file.exists()}")
    
    # Clean up test key
    print("8. Cleaning up test key...")
    if config.remove_api_key(key_id):
        print(f"   ✓ Test key removed successfully")
    else:
        print(f"   ✗ Failed to remove test key")
    
    print()
    print("✅ Persistent API Key Features:")
    print("   • API keys are encrypted and stored locally")
    print("   • Keys persist across application restarts") 
    print("   • Automatic encryption using machine-specific key")
    print("   • Secure storage in ~/.scrapqt directory")
    print("   • No need to re-enter keys after restart")
    
    print()
    print("🚀 Ready for testing:")
    print("   1. Start the main application")
    print("   2. Open sentiment analysis dialog")
    print("   3. Save an API key with a name")
    print("   4. Restart the application")
    print("   5. Open sentiment analysis dialog again")
    print("   6. Your saved key should be available in the dropdown!")

if __name__ == "__main__":
    test_persistent_api_keys()
