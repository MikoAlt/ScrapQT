#!/usr/bin/env python3
"""
Product Detail Dialog for ScrapQT - Compact Version
Shows detailed product information with image, description, and actions in a compact layout
"""

import webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame, QGridLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class ProductDetailDialog(QDialog):
    """Compact dialog to show detailed product information"""
    
    # Signal to notify parent when a product is deleted
    product_deleted = QtCore.pyqtSignal(int)  # Emits product_id when deleted
    
    def __init__(self, product_data, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._on_image_loaded)
        self.current_reply = None
        
        self.setWindowTitle(f"Product Details - {product_data.get('title', 'Unknown Product')}")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        self.resize(700, 500)
        
        # Make dialog resizable
        self.setWindowFlags(Qt.Dialog | Qt.WindowSystemMenuHint | 
                           Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        self._setup_ui()
        self._load_product_data()
        self._load_product_image()
    
    def _setup_ui(self):
        """Set up the compact dialog UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Title
        title_label = QLabel(self.product_data.get('title', 'Unknown Product'))
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 8px 0;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        title_label.setWordWrap(True)
        main_layout.addWidget(title_label)
        
        # Main content area - horizontal layout
        content_widget = QtWidgets.QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 10, 0, 0)
        content_layout.setSpacing(15)
        
        # LEFT SIDE - Image (40% width)
        image_container = QFrame()
        image_container.setFrameStyle(QFrame.StyledPanel)
        image_container.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
        """)
        image_container.setMinimumSize(200, 200)
        image_container.setMaximumSize(250, 300)
        
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(8, 8, 8, 8)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("Loading...")
        self.image_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 12px;
                border: none;
            }
        """)
        image_layout.addWidget(self.image_label)
        
        content_layout.addWidget(image_container)
        
        # RIGHT SIDE - Product Info (60% width)
        info_widget = QtWidgets.QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)
        
        # Platform info
        platform_label = QLabel(f"Platform: {self.product_data.get('ecommerce', 'Unknown')}")
        platform_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666;
                font-style: italic;
            }
        """)
        info_layout.addWidget(platform_label)
        
        # Product details in a compact grid
        details_frame = QFrame()
        details_frame.setFrameStyle(QFrame.StyledPanel)
        details_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                padding: 8px;
            }
        """)
        
        details_grid = QGridLayout(details_frame)
        details_grid.setContentsMargins(10, 10, 10, 10)
        details_grid.setSpacing(6)
        
        # Compact info rows
        row = 0
        self._add_compact_info_row(details_grid, row, "Price:", f"${self.product_data.get('price', 0):.2f}" if self.product_data.get('price') else "N/A")
        row += 1
        self._add_compact_info_row(details_grid, row, "Rating:", f"{self.product_data.get('review_score', 0):.1f}/5.0" if self.product_data.get('review_score') else "N/A")
        row += 1
        self._add_compact_info_row(details_grid, row, "Reviews:", str(self.product_data.get('review_count', 0)) if self.product_data.get('review_count') else "0")
        row += 1
        
        # Sentiment with color
        sentiment = self.product_data.get('sentiment_score')
        if sentiment is not None:
            if sentiment >= 0.3:
                sentiment_text = f"Positive ({sentiment:.2f})"
                sentiment_color = "#4caf50"
            elif sentiment >= -0.3:
                sentiment_text = f"Neutral ({sentiment:.2f})"
                sentiment_color = "#ff9800"
            else:
                sentiment_text = f"Negative ({sentiment:.2f})"
                sentiment_color = "#f44336"
        else:
            sentiment_text = "Unanalyzed"
            sentiment_color = "#757575"
            
        self._add_compact_info_row(details_grid, row, "Sentiment:", sentiment_text, sentiment_color)
        row += 1
        self._add_compact_info_row(details_grid, row, "Condition:", "New" if not self.product_data.get('is_used') else "Used")
        row += 1
        self._add_compact_info_row(details_grid, row, "Scraped:", self.product_data.get('scraped_at', 'Unknown')[:10] if self.product_data.get('scraped_at') else 'Unknown')
        
        info_layout.addWidget(details_frame)
        
        # Description (if available)
        if self.product_data.get('description'):
            desc_label = QLabel("Description:")
            desc_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #333; margin-top: 5px;")
            info_layout.addWidget(desc_label)
            
            desc_text = QTextEdit()
            desc_text.setPlainText(self.product_data.get('description', ''))
            desc_text.setReadOnly(True)
            desc_text.setMaximumHeight(80)
            desc_text.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #f9f9f9;
                    font-size: 11px;
                    color: #555;
                    padding: 5px;
                }
            """)
            info_layout.addWidget(desc_text)
        
        info_layout.addStretch()
        content_layout.addWidget(info_widget, 1)
        
        main_layout.addWidget(content_widget, 1)
        
        # BOTTOM - Action buttons
        button_frame = QFrame()
        button_frame.setFrameStyle(QFrame.StyledPanel)
        button_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: #f8f8f8;
                padding: 8px;
            }
        """)
        
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(10, 8, 10, 8)
        button_layout.setSpacing(10)
        
        # Open Browser button
        browser_button = QPushButton("🌐 Open Browser")
        browser_button.setStyleSheet(self._get_compact_button_style("#1976d2"))
        browser_button.clicked.connect(self._open_in_browser)
        button_layout.addWidget(browser_button)
        
        # Copy Link button
        copy_button = QPushButton("📎 Copy Link")
        copy_button.setStyleSheet(self._get_compact_button_style("#757575"))
        copy_button.clicked.connect(self._copy_link)
        button_layout.addWidget(copy_button)
        
        # Delete Product button
        delete_button = QPushButton("🗑️ Delete Product")
        delete_button.setStyleSheet(self._get_compact_button_style("#f44336"))
        delete_button.clicked.connect(self._delete_product)
        button_layout.addWidget(delete_button)
        
        button_layout.addStretch()
        
        # Close button
        close_button = QPushButton("Close")
        close_button.setStyleSheet(self._get_compact_button_style("#424242"))
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        main_layout.addWidget(button_frame)
    
    def _add_compact_info_row(self, grid_layout, row, label_text, value_text, value_color=None):
        """Add a compact info row to the grid"""
        # Label
        label = QLabel(label_text)
        label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #555;
                padding: 3px 5px;
            }
        """)
        grid_layout.addWidget(label, row, 0, Qt.AlignRight)
        
        # Value
        value = QLabel(value_text)
        value_style = f"""
            QLabel {{
                font-size: 11px;
                color: {value_color if value_color else '#333'};
                padding: 3px 5px;
            }}
        """
        value.setStyleSheet(value_style)
        grid_layout.addWidget(value, row, 1, Qt.AlignLeft)
    
    def _get_compact_button_style(self, bg_color):
        """Get compact button style"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(bg_color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(bg_color, 0.3)};
            }}
        """
    
    def _darken_color(self, hex_color, factor=0.2):
        """Darken a hex color by a factor"""
        # Simple color darkening - remove # and convert to int
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * (1 - factor)) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def _load_product_data(self):
        """Load and populate product data"""
        # Data is already loaded in __init__, just used in UI creation
        pass
    
    def _load_product_image(self):
        """Load product image from URL"""
        image_url = self.product_data.get('image_url')
        if image_url and image_url.strip():
            try:
                request = QNetworkRequest(QtCore.QUrl(image_url))
                request.setRawHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                self.current_reply = self.network_manager.get(request)
            except Exception as e:
                print(f"Error loading image: {e}")
                self.image_label.setText("Image not available")
        else:
            self.image_label.setText("No image available")
    
    def _on_image_loaded(self, reply):
        """Handle image loading completion"""
        if reply.error() == QNetworkReply.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                # Scale image to fit the container while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("Image format not supported")
        else:
            self.image_label.setText("Failed to load image")
        
        reply.deleteLater()
    
    def _open_in_browser(self):
        """Open product link in browser"""
        link = self.product_data.get('link')
        if link:
            try:
                webbrowser.open(link)
                print(f"Opened product in browser: {link}")
            except Exception as e:
                print(f"Error opening browser: {e}")
                QtWidgets.QMessageBox.warning(self, "Browser Error", f"Could not open link in browser:\n{str(e)}")
        else:
            QtWidgets.QMessageBox.information(self, "No Link", "No product link is available for this item.")
    
    def _copy_link(self):
        """Copy product link to clipboard"""
        link = self.product_data.get('link')
        if link:
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(link)
            print(f"Copied product link to clipboard: {link}")
            QtWidgets.QMessageBox.information(self, "Link Copied", "Product link copied to clipboard!")
        else:
            QtWidgets.QMessageBox.information(self, "No Link", "No product link is available to copy.")
    
    def _delete_product(self):
        """Delete product from database"""
        # Show confirmation dialog
        reply = QtWidgets.QMessageBox.question(
            self, 
            "Delete Product", 
            f"Are you sure you want to delete '{self.product_data.get('title', 'this product')}'?\n\nThis action cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                # Get product ID
                product_id = self.product_data.get('id')
                if product_id:
                    # Import database manager (assuming it's available)
                    from database_manager import DatabaseManager
                    db_manager = DatabaseManager()
                    
                    # Delete the product
                    success = db_manager.delete_product(product_id)
                    if success:
                        # Emit signal to notify parent that product was deleted
                        self.product_deleted.emit(product_id)
                        
                        QtWidgets.QMessageBox.information(self, "Success", "Product deleted successfully!")
                        self.accept()  # Close dialog
                    else:
                        QtWidgets.QMessageBox.warning(self, "Error", "Failed to delete product from database.")
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", "Product ID not found. Cannot delete product.")
            except Exception as e:
                print(f"Error deleting product: {e}")
                QtWidgets.QMessageBox.critical(self, "Error", f"An error occurred while deleting the product:\n{str(e)}")
                # Show more detailed error information for debugging
                if "FOREIGN KEY" in str(e):
                    QtWidgets.QMessageBox.information(
                        self, 
                        "Database Constraint", 
                        "This product has related data that prevents deletion. The database schema has been updated to handle this - please try again."
                    )
    
    def resizeEvent(self, event):
        """Handle dialog resize to rescale image"""
        super().resizeEvent(event)
        # Trigger image rescaling if we have a pixmap
        if hasattr(self.image_label, 'pixmap') and self.image_label.pixmap():
            # Re-scale the image to fit new size
            original_pixmap = self.image_label.pixmap()
            scaled_pixmap = original_pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
