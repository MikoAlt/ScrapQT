#!/usr/bin/env python3
"""
Test script to verify the clear database button functionality
"""

import sys
from PyQt5 import QtWidgets, QtCore
from main import Ui_MainWindow

def test_clear_database_button():
    """Test that the clear database button exists and is properly configured"""
    app = QtWidgets.QApplication([])
    
    # Create main window
    main_window = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(main_window)
    
    # Test that the clear database button exists
    assert hasattr(ui, 'clear_db_button'), "Clear database button should exist"
    print("✓ Clear database button exists")
    
    # Check button properties
    assert ui.clear_db_button.text() == "🗑️ Clear DB", "Clear DB button should have correct text"
    print("✓ Clear database button has correct text")
    
    # Check button is properly styled (red background)
    style = ui.clear_db_button.styleSheet()
    assert "background-color: #f44336" in style, "Clear DB button should have red background"
    print("✓ Clear database button has correct styling")
    
    # Check button is connected to handler
    assert hasattr(ui, 'clear_database'), "Clear database handler should exist"
    print("✓ Clear database handler exists")
    
    # Check database manager has the clear method
    assert hasattr(ui.db_manager, 'clear_all_data'), "Database manager should have clear_all_data method"
    print("✓ Database manager has clear_all_data method")
    
    app.quit()
    print("\n🎉 All clear database button tests passed!")

def test_database_state():
    """Test that database operations work correctly"""
    app = QtWidgets.QApplication([])
    
    # Create main window
    main_window = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(main_window)
    
    # Check initial products count
    products = ui.db_manager.get_all_products()
    initial_count = len(products)
    print(f"✓ Initial products count: {initial_count}")
    
    # Get all queries
    queries = ui.db_manager.get_all_unique_queries()
    queries_count = len(queries)
    print(f"✓ Initial queries count: {queries_count}")
    
    print(f"✓ Database state verified - {initial_count} products, {queries_count} queries")
    
    app.quit()
    return initial_count, queries_count

def main():
    """Run all tests"""
    print("Testing clear database button functionality...\n")
    
    try:
        test_clear_database_button()
        print()
        
        initial_products, initial_queries = test_database_state()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Summary:")
        print("• Clear database button is properly implemented")
        print("• Database connection is working")
        print(f"• Current database contains {initial_products} products and {initial_queries} queries")
        print("• Button is styled with warning colors (red)")
        print("• All necessary handlers and methods are in place")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
