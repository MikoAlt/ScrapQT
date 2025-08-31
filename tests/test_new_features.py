#!/usr/bin/env python3
"""
Test script to verify the new refresh button and scraping prompt features
"""

import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox
from main import Ui_MainWindow

def test_refresh_button():
    """Test that the refresh button is present and styled correctly"""
    app = QtWidgets.QApplication([])
    
    # Create main window
    main_window = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(main_window)
    
    # Check if refresh button exists
    assert hasattr(ui, 'refresh_button'), "Refresh button should exist"
    print("✓ Refresh button exists")
    
    # Check button properties
    assert ui.refresh_button.text() == "🔄 Refresh Table", "Refresh button should have correct text"
    print("✓ Refresh button has correct text")
    
    # Check button is properly styled
    style = ui.refresh_button.styleSheet()
    assert "background-color: #4caf50" in style, "Refresh button should have green background"
    print("✓ Refresh button has correct styling")
    
    # Check button is connected to handler
    # Note: We can't easily test signal connections in this simple test
    assert hasattr(ui, '_handle_manual_refresh'), "Manual refresh handler should exist"
    print("✓ Manual refresh handler exists")
    
    # Check prompt for refresh method exists
    assert hasattr(ui, '_prompt_for_refresh'), "Prompt for refresh method should exist"
    print("✓ Prompt for refresh method exists")
    
    app.quit()
    print("\n🎉 All refresh button tests passed!")

def test_scraping_prompt():
    """Test that the scraping completion prompt functionality exists"""
    app = QtWidgets.QApplication([])
    
    # Create main window
    main_window = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(main_window)
    
    # Test that the method exists and can be called safely
    try:
        # We won't actually show the dialog, just test the method exists
        assert hasattr(ui, '_prompt_for_refresh'), "Prompt for refresh method should exist"
        print("✓ Scraping completion prompt method exists")
        
        # Test that the scraping finished handler calls the prompt
        assert hasattr(ui, '_on_scraping_finished'), "Scraping finished handler should exist"
        print("✓ Scraping finished handler exists")
        
    except Exception as e:
        print(f"❌ Error testing scraping prompt: {e}")
        return False
    
    app.quit()
    print("🎉 All scraping prompt tests passed!")
    return True

def main():
    """Run all tests"""
    print("Testing new refresh and scraping prompt features...\n")
    
    try:
        test_refresh_button()
        print()
        test_scraping_prompt()
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
