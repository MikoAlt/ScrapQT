"""
Configuration Manager for ScrapQT
Handles API keys and application settings with persistent storage
"""

import os
import json
import hashlib
from typing import Optional, Dict, List
from pathlib import Path


class ConfigManager:
    """Manages application configuration and API keys"""
    
    def __init__(self):
        """Initialize the configuration manager"""
        # Create config directory
        self.config_dir = Path.home() / ".scrapqt"
        self.config_dir.mkdir(exist_ok=True)
        
        # Config files
        self.config_file = self.config_dir / "config.json"
        self.api_keys_file = self.config_dir / "api_keys.json"
        
        # Load existing configuration
        self.config = self._load_config()
        self.api_keys = self._load_api_keys()
        
        # Session storage for actual API keys (in memory only)
        self._session_keys = {}  # key_id -> actual_api_key
    
    def _load_config(self) -> Dict:
        """Load general configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Return default config
        return {
            "last_used_api_key_id": None,
            "sentiment_analysis_enabled": True,
            "auto_save_api_keys": True
        }
    
    def _load_api_keys(self) -> Dict:
        """Load saved API keys"""
        if self.api_keys_file.exists():
            try:
                with open(self.api_keys_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Return empty api keys dict
        return {
            "keys": {},  # key_id -> {name, key_hash, created_at}
            "next_id": 1
        }
    
    def _save_config(self):
        """Save general configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _save_api_keys(self):
        """Save API keys configuration"""
        try:
            with open(self.api_keys_file, 'w') as f:
                json.dump(self.api_keys, f, indent=2)
        except Exception as e:
            print(f"Error saving API keys: {e}")
    
    def _hash_api_key(self, api_key: str) -> str:
        """Create a hash of the API key for identification"""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """
        Simple encryption for API key storage (for local use only)
        Uses base64 encoding with a simple XOR cipher
        """
        import base64
        
        # Simple XOR encryption with a static key derived from machine info
        key_bytes = hashlib.sha256(f"{os.environ.get('USERNAME', 'default')}{os.environ.get('COMPUTERNAME', 'local')}".encode()).digest()
        
        encrypted = bytearray()
        for i, byte in enumerate(api_key.encode()):
            encrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt an API key from storage
        """
        import base64
        
        try:
            # Same XOR key as encryption
            key_bytes = hashlib.sha256(f"{os.environ.get('USERNAME', 'default')}{os.environ.get('COMPUTERNAME', 'local')}".encode()).digest()
            
            encrypted_bytes = base64.b64decode(encrypted_key.encode())
            decrypted = bytearray()
            
            for i, byte in enumerate(encrypted_bytes):
                decrypted.append(byte ^ key_bytes[i % len(key_bytes)])
            
            return decrypted.decode()
        except Exception:
            return None  # Failed to decrypt
    
    def save_api_key(self, api_key: str, name: Optional[str] = None) -> str:
        """
        Save an API key with optional name
        
        Args:
            api_key: The actual API key
            name: Optional human-readable name
            
        Returns:
            key_id: Unique identifier for the saved key
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")
        
        # Generate key hash for identification
        key_hash = self._hash_api_key(api_key)
        
        # Check if key already exists
        for key_id, key_data in self.api_keys["keys"].items():
            if key_data["key_hash"] == key_hash:
                return key_id  # Return existing key ID
        
        # Create new key entry
        key_id = str(self.api_keys["next_id"])
        self.api_keys["next_id"] += 1
        
        # Generate name if not provided
        if not name:
            name = f"API Key {key_id}"
        
        # Save key data (store the actual encrypted key for persistence)
        self.api_keys["keys"][key_id] = {
            "name": name,
            "key_hash": key_hash,
            "encrypted_key": self._encrypt_api_key(api_key),  # Store encrypted
            "created_at": None,  # You could add timestamp here
            "last_used": None
        }
        
        # Also store in session memory for immediate use
        self._session_keys[key_id] = api_key
        
        # Update last used key
        self.config["last_used_api_key_id"] = key_id
        
        # Save to files
        self._save_api_keys()
        self._save_config()
        
        return key_id
    
    def get_saved_api_keys(self) -> List[Dict[str, str]]:
        """
        Get list of saved API keys (metadata only)
        
        Returns:
            List of dicts with key_id, name, and last_used info
        """
        result = []
        for key_id, key_data in self.api_keys["keys"].items():
            result.append({
                "key_id": key_id,
                "name": key_data["name"],
                "key_hash": key_data["key_hash"][:8] + "...",  # Show partial hash
                "last_used": key_data.get("last_used"),
                "created_at": key_data.get("created_at")
            })
        
        # Sort by last used, then by ID
        result.sort(key=lambda x: (x["last_used"] or "", x["key_id"]), reverse=True)
        return result
    
    def mark_api_key_used(self, key_id: str):
        """Mark an API key as recently used"""
        if key_id in self.api_keys["keys"]:
            from datetime import datetime
            self.api_keys["keys"][key_id]["last_used"] = datetime.now().isoformat()
            self.config["last_used_api_key_id"] = key_id
            self._save_api_keys()
            self._save_config()
    
    def get_last_used_key_id(self) -> Optional[str]:
        """Get the ID of the last used API key"""
        return self.config.get("last_used_api_key_id")
    
    def remove_api_key(self, key_id: str) -> bool:
        """
        Remove a saved API key
        
        Args:
            key_id: ID of the key to remove
            
        Returns:
            True if key was removed, False if not found
        """
        if key_id in self.api_keys["keys"]:
            del self.api_keys["keys"][key_id]
            
            # Clear last used if it was this key
            if self.config.get("last_used_api_key_id") == key_id:
                self.config["last_used_api_key_id"] = None
            
            self._save_api_keys()
            self._save_config()
            return True
        
        return False
    
    def validate_api_key_format(self, api_key: str) -> bool:
        """
        Basic validation of Gemini API key format
        
        Args:
            api_key: The API key to validate
            
        Returns:
            True if format looks valid
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Basic Gemini API key format check
        api_key = api_key.strip()
        if len(api_key) < 20:  # Too short
            return False
        
        # Gemini API keys typically start with specific prefixes
        if not api_key.startswith("AI"):
            return False
        
        return True
    
    def get_session_api_key(self, key_id: str) -> Optional[str]:
        """
        Get the actual API key (from session memory or disk storage)
        
        Args:
            key_id: ID of the key to retrieve
            
        Returns:
            The actual API key if available, None otherwise
        """
        # First check session memory
        if key_id in self._session_keys:
            return self._session_keys[key_id]
        
        # If not in session, try to load from disk storage
        if key_id in self.api_keys["keys"]:
            key_data = self.api_keys["keys"][key_id]
            encrypted_key = key_data.get("encrypted_key")
            
            if encrypted_key:
                decrypted_key = self._decrypt_api_key(encrypted_key)
                if decrypted_key:
                    # Store in session for faster future access
                    self._session_keys[key_id] = decrypted_key
                    return decrypted_key
        
        return None
    
    def store_session_api_key(self, key_id: str, api_key: str):
        """
        Store an API key in session memory and update disk storage
        
        Args:
            key_id: ID of the key
            api_key: The actual API key
        """
        self._session_keys[key_id] = api_key
        
        # Also update the disk storage if this key exists
        if key_id in self.api_keys["keys"]:
            self.api_keys["keys"][key_id]["encrypted_key"] = self._encrypt_api_key(api_key)
            self._save_api_keys()
    
    def get_api_key_by_id(self, key_id: str) -> Optional[str]:
        """
        Get API key by ID (alias for get_session_api_key for backwards compatibility)
        """
        return self.get_session_api_key(key_id)
    
    def clear_all_api_keys(self) -> bool:
        """
        Clear all saved API keys from both session and persistent storage
        
        Returns:
            True if keys were cleared successfully, False otherwise
        """
        try:
            # Clear session memory
            self._session_keys.clear()
            
            # Clear persistent storage
            self.api_keys["keys"] = {}
            self.api_keys["next_id"] = 1
            
            # Clear any references in config
            if "last_used_api_key_id" in self.config:
                del self.config["last_used_api_key_id"]
            
            # Save changes to disk
            self._save_api_keys()
            self._save_config()
            
            print("All API keys have been cleared successfully")
            return True
            
        except Exception as e:
            print(f"Error clearing API keys: {e}")
            return False
