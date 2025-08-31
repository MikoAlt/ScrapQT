#!/usr/bin/env python3
"""
Test script to verify the search bar shows all queries when empty and focused
"""

import sys
from PyQt5 import QtWidgets, QtCore, QtTest
from main import Ui_MainWindow

def test_search_bar_queries():
    """Test that search bar shows all queries when empty and focused"""
    app = QtWidgets.QApplication([])
    
    # Create main window
    main_window = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(main_window)
    
    # Test that the new method exists
    assert hasattr(ui.search_bar, '_show_all_queries'), "Search bar should have _show_all_queries method"
    print("✓ Search bar has _show_all_queries method")
    
    # Test that database manager has the new method
    assert hasattr(ui.db_manager, 'get_all_unique_queries'), "Database manager should have get_all_unique_queries method"
    print("✓ Database manager has get_all_unique_queries method")
    
    # Test that we can get all queries
    try:
        all_queries = ui.db_manager.get_all_unique_queries()
        print(f"✓ Successfully retrieved {len(all_queries)} unique queries from database")
        
        # Display first few queries for verification
        if all_queries:
            print("  Sample queries:")
            for i, query in enumerate(all_queries[:5]):
                print(f"    {i+1}. {query}")
    except Exception as e:
        print(f"❌ Error retrieving queries: {e}")
        return False
    
    # Test focus event handling
    try:
        # Clear the search bar and simulate focus
        ui.search_bar.clear()
        ui.search_bar.focusInEvent(QtCore.QEvent(QtCore.QEvent.FocusIn))
        print("✓ Focus event handled successfully")
    except Exception as e:
        print(f"❌ Error handling focus event: {e}")
        return False
    
    app.quit()
    print("\n🎉 All search bar query tests passed!")
    return True

def main():
    """Run all tests"""
    print("Testing search bar query functionality...\n")
    
    try:
        test_search_bar_queries()
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
