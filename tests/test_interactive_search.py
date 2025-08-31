#!/usr/bin/env python3
"""
Interactive test to verify search bar query dropdown functionality
"""

import sys
from PyQt5 import QtWidgets, QtCore
from main import Ui_MainWindow

def interactive_test():
    """Interactive test for search bar functionality"""
    app = QtWidgets.QApplication(sys.argv)
    
    # Create main window
    main_window = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(main_window)
    
    # Show window
    main_window.show()
    
    # Test database queries
    all_queries = ui.db_manager.get_all_unique_queries()
    print(f"Found {len(all_queries)} unique queries in database:")
    for i, query in enumerate(all_queries, 1):
        print(f"  {i}. {query}")
    
    print("\nInteractive test started!")
    print("Instructions:")
    print("1. Click on the search bar (it should be empty)")
    print("2. You should see a dropdown with all available queries")
    print("3. Click on any query to select it")
    print("4. Type some text and see fuzzy suggestions")
    print("5. Clear the text and click the search bar again to see all queries")
    print("\nClose the window when done testing.")
    
    # Start the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    interactive_test()
