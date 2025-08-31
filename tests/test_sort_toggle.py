#!/usr/bin/env python3
"""
Test script to verify sort toggling works correctly
"""

import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

class SortTestWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sort Toggle Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setRowCount(4)
        
        # Set headers
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Score"])
        
        # Add test data
        test_data = [
            ["Apple", 10.5, 85],
            ["Banana", 5.2, 92],
            ["Cherry", 15.8, 78],
            ["Date", 3.1, 88]
        ]
        
        for row, (name, value, score) in enumerate(test_data):
            # Name column (text)
            name_item = QTableWidgetItem(name)
            self.table.setItem(row, 0, name_item)
            
            # Value column (numeric)
            value_item = QTableWidgetItem(f"{value}")
            value_item.setData(QtCore.Qt.UserRole, value)
            self.table.setItem(row, 1, value_item)
            
            # Score column (numeric)
            score_item = QTableWidgetItem(f"{score}")
            score_item.setData(QtCore.Qt.UserRole, score)
            self.table.setItem(row, 2, score_item)
        
        # Enable sorting
        self.table.setSortingEnabled(True)
        header = self.table.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        
        # Connect to track sorting
        header.sectionClicked.connect(self.on_header_clicked)
        
        layout.addWidget(self.table)
        
    def on_header_clicked(self, logical_index):
        """Track header clicks"""
        header = self.table.horizontalHeader()
        current_order = header.sortIndicatorOrder()
        column_name = self.table.horizontalHeaderItem(logical_index).text()
        order_name = "Ascending" if current_order == QtCore.Qt.AscendingOrder else "Descending"
        print(f"Clicked column {logical_index} ({column_name}) - Current order: {order_name}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = SortTestWidget()
    widget.show()
    
    print("Sort Toggle Test")
    print("================")
    print("Instructions:")
    print("1. Click on any column header to sort")
    print("2. Click the same header again to reverse the sort")
    print("3. Watch the console output to see the sort order changes")
    print("4. Look for the up/down arrow in the column header")
    print("\nExpected behavior:")
    print("- First click: Ascending order (up arrow)")
    print("- Second click: Descending order (down arrow)")
    print("- Third click: Ascending order again (up arrow)")
    
    sys.exit(app.exec_())
