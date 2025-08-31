# -*- coding: utf-8 -*-

"""
Refactored ScrapQT Main Window UI
This is a cleaned up and organized version of the main UI components
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QCompleter, QListWidget, QListWidgetItem
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, QStringListModel, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import urllib.parse
from database_manager import DatabaseManager


class QuerySuggestionCompleter(QtWidgets.QWidget):
    """Custom dropdown widget for query suggestions with fuzzy search"""
    
    suggestion_selected = QtCore.pyqtSignal(str, int)  # query_text, query_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create suggestion list
        self.suggestion_list = QListWidget()
        self.suggestion_list.setMaximumHeight(200)
        self.suggestion_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 2px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        
        layout.addWidget(self.suggestion_list)
        
        # Connect signals
        self.suggestion_list.itemClicked.connect(self._on_item_clicked)
        self.suggestion_list.itemActivated.connect(self._on_item_clicked)
        
        self.db_manager = DatabaseManager()
        
    def show_suggestions(self, search_term: str, position: QtCore.QPoint):
        """Show suggestions based on the search term"""
        suggestions = self.db_manager.fuzzy_search_queries(search_term, limit=8)
        
        if not suggestions:
            self.hide()
            return
        
        # Clear previous suggestions
        self.suggestion_list.clear()
        
        # Add suggestions to list
        for suggestion in suggestions:
            query_text = suggestion['query_text']
            product_count = suggestion['product_count']
            score = suggestion.get('similarity_score', 0)
            
            # Create item text with metadata
            item_text = f"{query_text}"
            if product_count > 0:
                item_text += f" ({product_count} products)"
            
            item = QListWidgetItem(item_text)
            item.setData(QtCore.Qt.UserRole, suggestion)  # Store full suggestion data
            
            # Add visual indicator for match quality
            if score >= 80:
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))
            elif score >= 50:
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogOkButton))
            else:
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon))
            
            self.suggestion_list.addItem(item)
        
        # Position and show the widget
        self.move(position)
        self.resize(300, min(200, len(suggestions) * 35 + 10))
        self.show()
        self.raise_()
        
    def _on_item_clicked(self, item):
        """Handle suggestion selection"""
        suggestion = item.data(QtCore.Qt.UserRole)
        if suggestion:
            self.suggestion_selected.emit(suggestion['query_text'], suggestion['id'])
        self.hide()
        
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == QtCore.Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)


class ProductTableWidget(QtWidgets.QTableWidget):
    """Custom table widget with image hover preview in main UI"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._show_image_preview)
        
        self.current_hover_row = -1
        self.current_image_url = ""
        self.setMouseTracking(True)
        
        # Reference to the main image label (will be set by parent)
        self.image_display_label = None
        
        # Network manager for loading images
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._on_image_loaded)
        self.current_reply = None
        
    def set_image_display_label(self, label):
        """Set the QLabel where images should be displayed"""
        self.image_display_label = label
        
    def mouseMoveEvent(self, event):
        """Handle mouse move to show/hide image preview"""
        super().mouseMoveEvent(event)
        
        item = self.itemAt(event.pos())
        if item:
            row = item.row()
            if row != self.current_hover_row:
                self.current_hover_row = row
                # Get image URL for this row
                self.current_image_url = self._get_image_url_for_row(row)
                
                if self.current_image_url and self.image_display_label:
                    # Start timer to show image after a short delay
                    self.hover_timer.start(200)  # 200ms delay
                else:
                    self.hover_timer.stop()
        else:
            if self.current_hover_row != -1:
                self.current_hover_row = -1
                self.hover_timer.stop()
                # Reset to placeholder when not hovering
                self._reset_image_display()
    
    def leaveEvent(self, event):
        """Reset image when mouse leaves the table"""
        super().leaveEvent(event)
        self.hover_timer.stop()
        self.current_hover_row = -1
        self._reset_image_display()
        
    def _show_image_preview(self):
        """Load and show the image preview in the main UI"""
        if self.current_image_url and self.current_hover_row >= 0 and self.image_display_label:
            # Cancel any ongoing request
            if self.current_reply:
                self.current_reply.abort()
                
            # Show loading text
            self.image_display_label.setText("Loading image...")
            self.image_display_label.setAlignment(QtCore.Qt.AlignCenter)
            self.image_display_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 14px;
                    border: 2px dashed #ccc;
                    border-radius: 8px;
                    background-color: #f9f9f9;
                }
            """)
            
            # Load the image
            request = QNetworkRequest(QtCore.QUrl(self.current_image_url))
            request.setRawHeader(b"User-Agent", b"Mozilla/5.0 ScrapQT Image Loader")
            self.current_reply = self.network_manager.get(request)
    
    def _on_image_loaded(self, reply):
        """Handle image loading completion"""
        if not self.image_display_label:
            reply.deleteLater()
            return
            
        if reply.error() == QNetworkReply.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                # Scale the image to fit the label while maintaining aspect ratio
                label_size = self.image_display_label.size()
                scaled_pixmap = pixmap.scaled(
                    label_size, 
                    QtCore.Qt.KeepAspectRatio, 
                    QtCore.Qt.SmoothTransformation
                )
                self.image_display_label.setPixmap(scaled_pixmap)
                self.image_display_label.setText("")
                self.image_display_label.setStyleSheet("")  # Remove loading style
            else:
                self.image_display_label.setText("Failed to load image")
                self.image_display_label.setStyleSheet("color: #f44336; font-size: 14px;")
        else:
            self.image_display_label.setText("Image not available")
            self.image_display_label.setStyleSheet("color: #f44336; font-size: 14px;")
            
        reply.deleteLater()
        if self.current_reply == reply:
            self.current_reply = None
    
    def _reset_image_display(self):
        """Reset the image display to placeholder"""
        if self.image_display_label:
            self.image_display_label.clear()
            self.image_display_label.setText("Hover over a product to see its image")
            self.image_display_label.setAlignment(QtCore.Qt.AlignCenter)
            self.image_display_label.setStyleSheet("""
                QLabel {
                    color: #999;
                    font-size: 12px;
                    font-style: italic;
                }
            """)
    
    def _get_image_url_for_row(self, row):
        """Get the image URL for the specified row"""
        # This will be set by the parent class
        if hasattr(self, '_products_data') and row < len(self._products_data):
            return self._products_data[row].get('image_url', '')
        return ""
    
    def set_products_data(self, products):
        """Set the products data for image URL lookup"""
        self._products_data = products


class Ui_MainWindow(object):
    def __init__(self):
        """Initialize the UI with database manager"""
        self.db_manager = DatabaseManager()
        
    def setupUi(self, MainWindow):
        """Set up the main window UI components"""
        self._setup_main_window(MainWindow)
        self._setup_main_layout()
        self._setup_content_area()
        self._setup_connections()
        self.retranslateUi(MainWindow)
        
        # Load initial data
        self._load_data_from_database()

    def _setup_main_window(self, MainWindow):
        """Configure the main window properties"""
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1146, 768)
        
        # Set size policy for responsive design
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        
        # Set minimum size and remove maximum size constraint for unlimited scaling
        MainWindow.setMinimumSize(QtCore.QSize(800, 600))
        MainWindow.setStyleSheet("QMainWindow { background-color: white; }")

    def _setup_main_layout(self):
        """Set up the main layout structure"""
        self.centralwidget = QtWidgets.QWidget()
        self.centralwidget.setObjectName("centralwidget")
        
        self.gridLayout_3 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_3.setObjectName("gridLayout_3")
        
        self.Window = QtWidgets.QWidget(self.centralwidget)
        self.Window.setObjectName("Window")
        
        self.gridLayout = QtWidgets.QGridLayout(self.Window)
        self.gridLayout.setObjectName("gridLayout")
        
        self.gridLayout_3.addWidget(self.Window, 0, 0, 2, 2)

    def _setup_content_area(self):
        """Set up the main content area with header and content sections"""
        # Create content container
        self.content = QtWidgets.QWidget(self.Window)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Expanding
        )
        sizePolicy.setHorizontalStretch(1)  # Give content area stretch priority
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.content.sizePolicy().hasHeightForWidth())
        self.content.setSizePolicy(sizePolicy)
        self.content.setObjectName("content")

        # Create main vertical layout for content
        self.content_layout = QtWidgets.QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Set up header and main content
        self._setup_header()
        self._setup_main_content()

        # Add to main grid (full width since no sidebars)
        self.gridLayout.addWidget(self.content, 0, 0, 1, 1)

    def _setup_header(self):
        """Set up the header section with menu, logo, and search"""
        # Create header container
        self.header = QtWidgets.QWidget(self.content)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.header.sizePolicy().hasHeightForWidth())
        self.header.setSizePolicy(sizePolicy)
        self.header.setMinimumSize(QtCore.QSize(0, 80))
        self.header.setMaximumSize(QtCore.QSize(16777215, 80))
        self.header.setStyleSheet("background-color: rgb(0, 89, 255);")
        self.header.setObjectName("header")

        # Header layout
        self.gridLayout_4 = QtWidgets.QGridLayout(self.header)
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_4.setObjectName("gridLayout_4")

        # Header content
        self._setup_header_content()

        # Add header to content layout
        self.content_layout.addWidget(self.header)

    def _setup_header_content(self):
        """Set up the header content with menu, logo, and search functionality"""
        self.head_content = QtWidgets.QWidget(self.header)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, 
            QtWidgets.QSizePolicy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.head_content.sizePolicy().hasHeightForWidth())
        self.head_content.setSizePolicy(sizePolicy)
        self.head_content.setMinimumSize(QtCore.QSize(0, 55))
        self.head_content.setStyleSheet("QWidget { background-color: rgb(0, 89, 255); }")
        self.head_content.setObjectName("head_content")

        # Header layout
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.head_content)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        # Add header components
        self._add_home_logo()
        self._add_search_section()

        self.gridLayout_4.addWidget(self.head_content, 0, 0, 1, 1)

    def _add_home_logo(self):
        """Add the main application logo"""
        self.scrap_home_logo = QtWidgets.QPushButton(self.head_content)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, 
            QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrap_home_logo.sizePolicy().hasHeightForWidth())
        self.scrap_home_logo.setSizePolicy(sizePolicy)
        self.scrap_home_logo.setStyleSheet("border: none;")
        self.scrap_home_logo.setText("")
        
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/resource/ScrapQt.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.scrap_home_logo.setIcon(icon5)
        self.scrap_home_logo.setIconSize(QtCore.QSize(200, 100))
        self.scrap_home_logo.setObjectName("scrap_home_logo")
        
        self.horizontalLayout_2.addWidget(self.scrap_home_logo)

    def _add_search_section(self):
        """Add the search bar and search button"""
        # Add spacer before search
        spacerItem2 = QtWidgets.QSpacerItem(
            40, 20, 
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout_2.addItem(spacerItem2)

        # Search layout
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        # Search bar
        self.search_bar = QtWidgets.QLineEdit(self.head_content)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.search_bar.sizePolicy().hasHeightForWidth())
        self.search_bar.setSizePolicy(sizePolicy)
        self.search_bar.setMinimumSize(QtCore.QSize(200, 0))
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: rgb(255, 212, 0);
                color: darkblue;
                border: 1px solid gray;
                padding: 5px;
            }
        """)
        self.search_bar.setText("")
        self.search_bar.setObjectName("search_bar")
        self.horizontalLayout.addWidget(self.search_bar)

        # Search button
        self.search_button = QtWidgets.QPushButton(self.head_content)
        self.search_button.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.search_button.setText("")
        
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/resource/Search.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.search_button.setIcon(icon6)
        self.search_button.setIconSize(QtCore.QSize(25, 25))
        self.search_button.setObjectName("search_button")
        self.horizontalLayout.addWidget(self.search_button)

        self.horizontalLayout_2.addLayout(self.horizontalLayout)

    def _setup_main_content(self):
        """Set up the main content area with product information and table"""
        # Create main content widget
        self.main_content_widget = QtWidgets.QWidget(self.content)
        self.main_content_widget.setObjectName("main_content_widget")
        
        # Content grid layout
        self.gridLayout_2 = QtWidgets.QGridLayout(self.main_content_widget)
        self.gridLayout_2.setContentsMargins(0, 5, 0, 5)  # Remove side margins but keep top/bottom
        self.gridLayout_2.setObjectName("gridLayout_2")

        # Add content sections
        self._setup_product_sections()
        self._setup_product_table()

        # Add main content widget to content layout
        self.content_layout.addWidget(self.main_content_widget)

    def _setup_product_sections(self):
        """Set up product image and comparison chart sections"""
        # Product image title
        self.gambar_produk_title = QtWidgets.QLabel(self.main_content_widget)
        self.gambar_produk_title.setMaximumSize(QtCore.QSize(16777215, 40))
        self.gambar_produk_title.setStyleSheet("font: 87 12pt \"Segoe UI Black\";")
        self.gambar_produk_title.setObjectName("gambar_produk_title")
        self.gridLayout_2.addWidget(self.gambar_produk_title, 0, 1, 1, 1)

        # Comparison chart title
        self.grafik_perbandingan_title = QtWidgets.QLabel(self.main_content_widget)
        self.grafik_perbandingan_title.setMaximumSize(QtCore.QSize(16777215, 40))
        self.grafik_perbandingan_title.setStyleSheet("font: 87 12pt \"Segoe UI Black\";")
        self.grafik_perbandingan_title.setObjectName("grafik_perbandingan_title")
        self.gridLayout_2.addWidget(self.grafik_perbandingan_title, 0, 2, 1, 1)

        # Product image
        self.gambar_produk = QtWidgets.QLabel(self.main_content_widget)
        self.gambar_produk.setStyleSheet("image: url(:/resource/Placeholder.jpg);")
        self.gambar_produk.setText("")
        self.gambar_produk.setScaledContents(True)  # Enable image scaling
        self.gambar_produk.setObjectName("gambar_produk")
        self.gridLayout_2.addWidget(self.gambar_produk, 1, 1, 1, 1)

        # Comparison chart
        self.grafik_perbandingan = QtWidgets.QLabel(self.main_content_widget)
        self.grafik_perbandingan.setStyleSheet("image: url(:/resource/Placeholder.jpg);")
        self.grafik_perbandingan.setText("")
        self.grafik_perbandingan.setScaledContents(True)  # Enable image scaling
        self.grafik_perbandingan.setObjectName("grafik_perbandingan")
        self.gridLayout_2.addWidget(self.grafik_perbandingan, 1, 2, 1, 1)

        # Add vertical spacer
        spacerItem3 = QtWidgets.QSpacerItem(
            20, 20, 
            QtWidgets.QSizePolicy.Minimum, 
            QtWidgets.QSizePolicy.Fixed
        )
        self.gridLayout_2.addItem(spacerItem3, 2, 0, 1, 3)

        # Product description title
        self.deskripsi_produk_title = QtWidgets.QLabel(self.main_content_widget)
        self.deskripsi_produk_title.setMaximumSize(QtCore.QSize(16777215, 40))
        self.deskripsi_produk_title.setStyleSheet("font: 87 12pt \"Segoe UI Black\";")
        self.deskripsi_produk_title.setObjectName("deskripsi_produk_title")
        self.gridLayout_2.addWidget(self.deskripsi_produk_title, 3, 0, 1, 3)

        # Add another vertical spacer
        spacerItem4 = QtWidgets.QSpacerItem(
            20, 5, 
            QtWidgets.QSizePolicy.Minimum, 
            QtWidgets.QSizePolicy.Fixed
        )
        self.gridLayout_2.addItem(spacerItem4, 5, 0, 1, 3)

    def _setup_product_table(self):
        """Set up the product data table"""
        self.tabel_produk = ProductTableWidget(self.main_content_widget)
        
        # Set size policy for full expansion
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Expanding
        )
        sizePolicy.setHorizontalStretch(1)  # Give table priority for horizontal expansion
        sizePolicy.setVerticalStretch(1)  # Allow table to expand vertically
        sizePolicy.setHeightForWidth(self.tabel_produk.sizePolicy().hasHeightForWidth())
        self.tabel_produk.setSizePolicy(sizePolicy)
        self.tabel_produk.setMinimumSize(QtCore.QSize(0, 200))

        # Set table styling
        self.tabel_produk.setStyleSheet("""
            QTableView {
                border-radius: 3px;
                border: 1px solid #f0f0f0;
            }
            
            QHeaderView::section {
                border: none;
                border-bottom: 1px solid #d0c6ff;
                text-align: left;
                padding: 3px 5px;
                font-family: Segoe UI Semibold;
                font-size: 12;
            }
            
            QTableWidget {
                color: #000;
                padding-left: 3px;
            }
        """)
        
        self.tabel_produk.setObjectName("tabel_produk")
        
        # Set up table structure
        self._setup_table_columns()
        self._configure_table_behavior()
        
        # Connect the image display label to the table for hover previews
        self.tabel_produk.set_image_display_label(self.gambar_produk)
        
        # Set initial placeholder text for the image label
        self.gambar_produk.clear()
        self.gambar_produk.setText("Hover over a product to see its image")
        self.gambar_produk.setAlignment(QtCore.Qt.AlignCenter)
        self.gambar_produk.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 12px;
                font-style: italic;
            }
        """)

        # Add table to layout (spanning all columns for full width)
        self.gridLayout_2.addWidget(self.tabel_produk, 4, 0, 1, 3)

    def _setup_table_columns(self):
        """Set up table columns and headers"""
        self.tabel_produk.setColumnCount(6)
        self.tabel_produk.setRowCount(0)
        
        # Set column headers
        headers = [
            "Nama Produk", "Platform", "Rating", 
            "Amount", "Status", "Action"
        ]
        
        for i, header in enumerate(headers):
            item = QtWidgets.QTableWidgetItem()
            self.tabel_produk.setHorizontalHeaderItem(i, item)

    def _configure_table_behavior(self):
        """Configure table resizing and scroll behavior"""
        # Set table to resize columns automatically and fill full width
        self.tabel_produk.horizontalHeader().setStretchLastSection(True)
        self.tabel_produk.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        # Ensure table uses full available width
        self.tabel_produk.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def _setup_connections(self):
        """Set up signal-slot connections"""
        # Connect search functionality
        self.search_button.clicked.connect(self._handle_search)
        self.search_bar.returnPressed.connect(self._handle_search)
        
        # Set up fuzzy search autocomplete
        self.suggestion_completer = QuerySuggestionCompleter()
        self.suggestion_completer.suggestion_selected.connect(self._handle_suggestion_selected)
        self.search_bar.textChanged.connect(self._handle_text_changed)
        
        # Install event filter on search bar to handle focus events
        # This will be set up by the main window after UI initialization
        
        # Timer for delayed search suggestions
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._show_search_suggestions)
        
        # Store reference to main window for event filtering (set later)
        self.main_window = None
        
    def set_main_window(self, main_window):
        """Set the main window reference and install event filter"""
        self.main_window = main_window
        self.search_bar.installEventFilter(main_window)
        
    def _handle_text_changed(self):
        """Handle text changes in search bar with delay for suggestions"""
        # Stop any previous timer
        self.search_timer.stop()
        
        search_text = self.search_bar.text().strip()
        if len(search_text) >= 2:  # Start suggesting after 2 characters
            # Start timer for delayed suggestion display
            self.search_timer.start(300)  # 300ms delay
        else:
            self.suggestion_completer.hide()
            
    def _show_search_suggestions(self):
        """Show search suggestions dropdown"""
        search_text = self.search_bar.text().strip()
        if len(search_text) >= 2:
            # Calculate position for suggestion dropdown
            search_bar_global = self.search_bar.mapToGlobal(QtCore.QPoint(0, self.search_bar.height()))
            self.suggestion_completer.show_suggestions(search_text, search_bar_global)
        
    def _handle_suggestion_selected(self, query_text, query_id):
        """Handle when a suggestion is selected"""
        # Update search bar with selected query
        self.search_bar.setText(query_text)
        
        # Load products for the selected query
        products = self.db_manager.get_products_by_query_id(query_id)
        self._populate_table(products)
        print(f"Loaded {len(products)} products for query: '{query_text}'")
        
    def _handle_search(self):
        """Handle search button click or Enter key press with fuzzy matching"""
        search_term = self.search_bar.text().strip()
        
        if not search_term:
            self._load_data_from_database()
            return
        
        # Hide suggestions when searching
        self.suggestion_completer.hide()
        
        # First, try to find exact or fuzzy match in queries
        matching_queries = self.db_manager.fuzzy_search_queries(search_term, limit=1)
        
        if matching_queries and matching_queries[0].get('similarity_score', 0) >= 70:
            # High confidence match - load products for that query
            best_match = matching_queries[0]
            products = self.db_manager.get_products_by_query_id(best_match['id'])
            self._populate_table(products)
            print(f"Found query match: '{best_match['query_text']}' - Loaded {len(products)} products")
            
            # Update search bar to show the matched query
            if best_match['query_text'] != search_term:
                self.search_bar.setText(best_match['query_text'])
        else:
            # No good query match - fall back to product search
            products = self.db_manager.search_products(search_term)
            self._populate_table(products)
            print(f"Product search for '{search_term}' - Found {len(products)} products")
    
    def _load_data_from_database(self):
        """Load all products from database and populate table"""
        try:
            products = self.db_manager.get_all_products()
            self._populate_table(products)
            print(f"Loaded {len(products)} products from database")
        except Exception as e:
            print(f"Error loading data from database: {e}")
        
class MainWindowHandler(QtWidgets.QMainWindow):
    """Main window with event handling for fuzzy search"""
    
    def __init__(self):
        super().__init__()
        self.ui = None
        
    def set_ui(self, ui):
        """Set the UI reference"""
        self.ui = ui
        ui.set_main_window(self)
        
    def eventFilter(self, obj, event):
        """Handle events for search bar focus management"""
        if self.ui and obj == self.ui.search_bar:
            if event.type() == QtCore.QEvent.FocusOut:
                # Hide suggestions when search bar loses focus (with small delay)
                QtCore.QTimer.singleShot(150, self.ui.suggestion_completer.hide)
            elif event.type() == QtCore.QEvent.KeyPress:
                if event.key() == QtCore.Qt.Key_Down:
                    # Navigate to suggestions with down arrow
                    if self.ui.suggestion_completer.isVisible():
                        self.ui.suggestion_completer.suggestion_list.setFocus()
                    return True
                elif event.key() == QtCore.Qt.Key_Escape:
                    # Hide suggestions with escape
                    self.ui.suggestion_completer.hide()
                    return True
        return super().eventFilter(obj, event)
        
    def _handle_text_changed(self):
        """Handle text changes in search bar with delay for suggestions"""
        # Stop any previous timer
        self.search_timer.stop()
        
        search_text = self.search_bar.text().strip()
        if len(search_text) >= 2:  # Start suggesting after 2 characters
            # Start timer for delayed suggestion display
            self.search_timer.start(300)  # 300ms delay
        else:
            self.suggestion_completer.hide()
            
    def _show_search_suggestions(self):
        """Show search suggestions dropdown"""
        search_text = self.search_bar.text().strip()
        if len(search_text) >= 2:
            # Calculate position for suggestion dropdown
            search_bar_global = self.search_bar.mapToGlobal(QtCore.QPoint(0, self.search_bar.height()))
            self.suggestion_completer.show_suggestions(search_text, search_bar_global)
        
    def _handle_suggestion_selected(self, query_text, query_id):
        """Handle when a suggestion is selected"""
        # Update search bar with selected query
        self.search_bar.setText(query_text)
        
        # Load products for the selected query
        products = self.db_manager.get_products_by_query_id(query_id)
        self._populate_table(products)
        print(f"Loaded {len(products)} products for query: '{query_text}'")
        
    def _handle_search(self):
        """Handle search button click or Enter key press with fuzzy matching"""
        search_term = self.search_bar.text().strip()
        
        if not search_term:
            self._load_data_from_database()
            return
        
        # Hide suggestions when searching
        self.suggestion_completer.hide()
        
        # First, try to find exact or fuzzy match in queries
        matching_queries = self.db_manager.fuzzy_search_queries(search_term, limit=1)
        
        if matching_queries and matching_queries[0].get('similarity_score', 0) >= 70:
            # High confidence match - load products for that query
            best_match = matching_queries[0]
            products = self.db_manager.get_products_by_query_id(best_match['id'])
            self._populate_table(products)
            print(f"Found query match: '{best_match['query_text']}' - Loaded {len(products)} products")
            
            # Update search bar to show the matched query
            if best_match['query_text'] != search_term:
                self.search_bar.setText(best_match['query_text'])
        else:
            # No good query match - fall back to product search
            products = self.db_manager.search_products(search_term)
            self._populate_table(products)
            print(f"Product search for '{search_term}' - Found {len(products)} products")
    
    def _load_data_from_database(self):
        """Load all products from database and populate table"""
        try:
            products = self.db_manager.get_all_products()
            self._populate_table(products)
            print(f"Loaded {len(products)} products from database")
        except Exception as e:
            print(f"Error loading data from database: {e}")
    
    def _populate_table(self, products):
        """Populate the table with product data"""
        self.tabel_produk.setRowCount(len(products))
        # Set products data for image hover functionality
        self.tabel_produk.set_products_data(products)
        
        for row, product in enumerate(products):
            # Product Name
            name_item = QtWidgets.QTableWidgetItem(product.get('title', ''))
            self.tabel_produk.setItem(row, 0, name_item)
            
            # Platform
            platform_item = QtWidgets.QTableWidgetItem(product.get('ecommerce', ''))
            self.tabel_produk.setItem(row, 1, platform_item)
            
            # Rating
            rating = product.get('review_score')
            rating_text = f"{rating:.1f}" if rating else "N/A"
            rating_item = QtWidgets.QTableWidgetItem(rating_text)
            self.tabel_produk.setItem(row, 2, rating_item)
            
            # Amount (Price)
            price = product.get('price')
            if price and price > 0:
                amount_text = f"${price:.2f}"
            else:
                amount_text = "N/A"
            amount_item = QtWidgets.QTableWidgetItem(amount_text)
            self.tabel_produk.setItem(row, 3, amount_item)
            
            # Status (Sentiment)
            sentiment = product.get('sentiment_score')
            if sentiment:
                if sentiment >= 7:
                    status_text = "Positive"
                elif sentiment >= 4:
                    status_text = "Neutral"
                else:
                    status_text = "Negative"
            else:
                status_text = "Unanalyzed"
            status_item = QtWidgets.QTableWidgetItem(status_text)
            self.tabel_produk.setItem(row, 4, status_item)
            
            # Action (View Link)
            action_item = QtWidgets.QTableWidgetItem("View")
            self.tabel_produk.setItem(row, 5, action_item)
        
        # Auto-resize columns to content
        self.tabel_produk.resizeColumnsToContents()

    def retranslateUi(self, MainWindow):
        """Set up UI text and translations"""
        _translate = QtCore.QCoreApplication.translate
        
        # Window title
        MainWindow.setWindowTitle(_translate("MainWindow", "ScrapQT - Product Scraping Tool"))
        
        # Search bar placeholder
        self.search_bar.setPlaceholderText(_translate("MainWindow", "Search here..."))
        
        # Section titles
        self.gambar_produk_title.setText(_translate("MainWindow", "Product Image"))
        self.deskripsi_produk_title.setText(_translate("MainWindow", "Product Description"))
        self.grafik_perbandingan_title.setText(_translate("MainWindow", "Comparison Chart"))
        
        # Table headers
        headers = [
            "Product Name", "Platform", "Rating", 
            "Amount", "Status", "Action"
        ]
        
        for i, header in enumerate(headers):
            item = self.tabel_produk.horizontalHeaderItem(i)
            if item:
                item.setText(_translate("MainWindow", header))


# Import resources
import asset_rc


if __name__ == "__main__":
    import sys
    import signal
    
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Create application
    app = QtWidgets.QApplication(sys.argv)
    
    # Create main window with event handling
    MainWindow = MainWindowHandler()
    
    # Enable window resizing and make it responsive
    MainWindow.setWindowFlags(QtCore.Qt.Window)
    
    # Set up UI
    ui = Ui_MainWindow()  # Now includes database initialization
    ui.setupUi(MainWindow)
    MainWindow.set_ui(ui)  # Connect UI with main window for event handling
    
    # Configure main window
    MainWindow.setCentralWidget(ui.centralwidget)
    
    # Show window and start application
    MainWindow.show()
    sys.exit(app.exec_())
