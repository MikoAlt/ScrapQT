#!/usr/bin/env python3
"""
Product Detail Dialog for ScrapQT
Shows detailed product information with image, description, and actions
"""

import webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class ProductDetailDialog(QDialog):
    """Dialog to show detailed product information"""
    
    def __init__(self, product_data, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._on_image_loaded)
        self.current_reply = None
        
        self.setWindowTitle(f"Product Details - {product_data.get('title', 'Unknown Product')}")
        self.setModal(True)
        self.resize(600, 700)
        
        self._setup_ui()
        self._load_product_data()
        self._load_product_image()
    
    def _setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header section with title and platform
        self._create_header_section(layout)
        
        # Image section
        self._create_image_section(layout)
        
        # Product info section
        self._create_info_section(layout)
        
        # Description section
        self._create_description_section(layout)
        
        # Action buttons section
        self._create_action_buttons(layout)
    
    def _create_header_section(self, parent_layout):
        """Create header with title and platform"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        # Product title
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("color: #333; margin: 5px 0;")
        header_layout.addWidget(self.title_label)
        
        # Platform info
        self.platform_label = QLabel()
        platform_font = QFont()
        platform_font.setPointSize(12)
        self.platform_label.setFont(platform_font)
        self.platform_label.setStyleSheet("color: #666; margin: 2px 0;")
        header_layout.addWidget(self.platform_label)
        
        parent_layout.addWidget(header_frame)
    
    def _create_image_section(self, parent_layout):
        """Create product image section"""
        image_frame = QFrame()
        image_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
        """)
        image_frame.setFixedHeight(250)
        
        image_layout = QVBoxLayout(image_frame)
        image_layout.setContentsMargins(10, 10, 10, 10)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 14px;
                border: none;
            }
        """)
        self.image_label.setText("Loading image...")
        
        image_layout.addWidget(self.image_label)
        parent_layout.addWidget(image_frame)
    
    def _create_info_section(self, parent_layout):
        """Create product information grid"""
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
                padding: 15px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        
        # Create info grid
        grid_layout = QtWidgets.QGridLayout()
        grid_layout.setSpacing(10)
        
        # Price
        grid_layout.addWidget(self._create_info_label("Price:"), 0, 0)
        self.price_label = self._create_info_value("")
        grid_layout.addWidget(self.price_label, 0, 1)
        
        # Rating
        grid_layout.addWidget(self._create_info_label("Rating:"), 1, 0)
        self.rating_label = self._create_info_value("")
        grid_layout.addWidget(self.rating_label, 1, 1)
        
        # Review Count
        grid_layout.addWidget(self._create_info_label("Reviews:"), 2, 0)
        self.reviews_label = self._create_info_value("")
        grid_layout.addWidget(self.reviews_label, 2, 1)
        
        # Sentiment
        grid_layout.addWidget(self._create_info_label("Sentiment:"), 3, 0)
        self.sentiment_label = self._create_info_value("")
        grid_layout.addWidget(self.sentiment_label, 3, 1)
        
        # Condition
        grid_layout.addWidget(self._create_info_label("Condition:"), 4, 0)
        self.condition_label = self._create_info_value("")
        grid_layout.addWidget(self.condition_label, 4, 1)
        
        # Scraped date
        grid_layout.addWidget(self._create_info_label("Scraped:"), 5, 0)
        self.scraped_label = self._create_info_value("")
        grid_layout.addWidget(self.scraped_label, 5, 1)
        
        info_layout.addLayout(grid_layout)
        parent_layout.addWidget(info_frame)
    
    def _create_info_label(self, text):
        """Create an info label"""
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; color: #333;")
        return label
    
    def _create_info_value(self, text):
        """Create an info value label"""
        label = QLabel(text)
        label.setStyleSheet("color: #666;")
        label.setWordWrap(True)
        return label
    
    def _create_description_section(self, parent_layout):
        """Create description section"""
        desc_frame = QFrame()
        desc_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
        """)
        
        desc_layout = QVBoxLayout(desc_frame)
        desc_layout.setContentsMargins(15, 15, 15, 15)
        
        # Description title
        desc_title = QLabel("Description")
        desc_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-bottom: 10px;")
        desc_layout.addWidget(desc_title)
        
        # Description text
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(120)
        self.description_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: #f8f9fa;
                color: #666;
                font-size: 12px;
                padding: 10px;
            }
        """)
        desc_layout.addWidget(self.description_text)
        
        parent_layout.addWidget(desc_frame)
    
    def _create_action_buttons(self, parent_layout):
        """Create action buttons"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Open in Browser button
        self.browser_button = QPushButton("🌐 Open in Browser")
        self.browser_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        self.browser_button.clicked.connect(self._open_in_browser)
        button_layout.addWidget(self.browser_button)
        
        # Copy Link button
        self.copy_button = QPushButton("📋 Copy Link")
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
            QPushButton:pressed {
                background-color: #155724;
            }
        """)
        self.copy_button.clicked.connect(self._copy_link)
        button_layout.addWidget(self.copy_button)
        
        # Close button
        self.close_button = QPushButton("✖️ Close")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
            QPushButton:pressed {
                background-color: #383d41;
            }
        """)
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        parent_layout.addLayout(button_layout)
    
    def _load_product_data(self):
        """Load product data into UI elements"""
        # Title and platform
        self.title_label.setText(self.product_data.get('title', 'Unknown Product'))
        self.platform_label.setText(f"Platform: {self.product_data.get('ecommerce', 'Unknown')}")
        
        # Price
        price = self.product_data.get('price')
        price_text = f"${price:.2f}" if price else "Not available"
        self.price_label.setText(price_text)
        
        # Rating
        rating = self.product_data.get('review_score')
        rating_text = f"{rating:.1f}/5.0" if rating else "Not rated"
        self.rating_label.setText(rating_text)
        
        # Review count
        review_count = self.product_data.get('review_count')
        reviews_text = f"{review_count} reviews" if review_count else "No reviews"
        self.reviews_label.setText(reviews_text)
        
        # Sentiment
        sentiment = self.product_data.get('sentiment_score')
        if sentiment is not None:
            if sentiment >= 0.3:
                sentiment_text = f"Positive ({sentiment:.2f})"
            elif sentiment >= -0.3:
                sentiment_text = f"Neutral ({sentiment:.2f})"
            else:
                sentiment_text = f"Negative ({sentiment:.2f})"
        else:
            sentiment_text = "Not analyzed"
        self.sentiment_label.setText(sentiment_text)
        
        # Condition
        is_used = self.product_data.get('is_used')
        condition_text = "Used" if is_used else "New" if is_used is not None else "Unknown"
        self.condition_label.setText(condition_text)
        
        # Scraped date
        scraped_at = self.product_data.get('scraped_at')
        if scraped_at:
            try:
                from datetime import datetime
                if isinstance(scraped_at, str):
                    scraped_date = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                    scraped_text = scraped_date.strftime('%Y-%m-%d %H:%M')
                else:
                    scraped_text = str(scraped_at)
            except:
                scraped_text = str(scraped_at)
        else:
            scraped_text = "Unknown"
        self.scraped_label.setText(scraped_text)
        
        # Description
        description = self.product_data.get('description')
        if description:
            self.description_text.setPlainText(description)
        else:
            self.description_text.setPlainText("No description available.")
    
    def _load_product_image(self):
        """Load product image from URL"""
        image_url = self.product_data.get('image_url')
        if image_url:
            request = QNetworkRequest(QtCore.QUrl(image_url))
            request.setRawHeader(b"User-Agent", b"Mozilla/5.0 ScrapQT Product Viewer")
            self.current_reply = self.network_manager.get(request)
        else:
            self.image_label.setText("No image available")
    
    def _on_image_loaded(self, reply):
        """Handle image loading completion"""
        if reply.error() == QNetworkReply.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                # Scale image to fit the label
                label_size = self.image_label.size()
                scaled_pixmap = pixmap.scaled(
                    label_size.width() - 20, 
                    label_size.height() - 20,
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("Failed to load image")
        else:
            self.image_label.setText("Image not available")
        
        reply.deleteLater()
        if self.current_reply == reply:
            self.current_reply = None
    
    def _open_in_browser(self):
        """Open product link in default browser"""
        link = self.product_data.get('link')
        if link:
            try:
                webbrowser.open(link)
                print(f"Opened product link in browser: {link}")
            except Exception as e:
                print(f"Error opening browser: {e}")
                QtWidgets.QMessageBox.warning(
                    self, 
                    "Browser Error", 
                    f"Could not open link in browser:\n{str(e)}"
                )
        else:
            QtWidgets.QMessageBox.information(
                self, 
                "No Link", 
                "No product link is available for this item."
            )
    
    def _copy_link(self):
        """Copy product link to clipboard"""
        link = self.product_data.get('link')
        if link:
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(link)
            
            # Show temporary feedback
            original_text = self.copy_button.text()
            self.copy_button.setText("✅ Copied!")
            QTimer.singleShot(2000, lambda: self.copy_button.setText(original_text))
            
            print(f"Copied product link to clipboard: {link}")
        else:
            QtWidgets.QMessageBox.information(
                self, 
                "No Link", 
                "No product link is available to copy."
            )
