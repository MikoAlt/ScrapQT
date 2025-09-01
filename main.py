# -*- coding: utf-8 -*-

"""
Refactored ScrapQT Main Window UI
This is a cleaned up and organized version of the main UI components
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QCompleter, QListWidget, QListWidgetItem, QMessageBox
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import urllib.parse
import webbrowser
import grpc
from database_manager import DatabaseManager
from src.scrapqt import services_pb2, services_pb2_grpc
from sentiment_dialog import SentimentAnalysisDialog
from product_detail_dialog import ProductDetailDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pengolahan_data import DataSortingScrapper


class ScraperWorkerThread(QThread):
    """Background thread for scraping operations"""

    scraping_started = pyqtSignal(str)  # query
    scraping_finished = pyqtSignal(str, int, bool)  # query, items_scraped, success
    scraping_error = pyqtSignal(str, str)  # query, error_message

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        """Run the scraping operation in background"""
        try:
            self.scraping_started.emit(self.query)

            # Connect to scraper service
            with grpc.insecure_channel('localhost:60002') as channel:
                scraper_stub = services_pb2_grpc.ScraperStub(channel)

                # Send scrape request
                request = services_pb2.ScrapeRequest(query=self.query)
                response = scraper_stub.Scrape(request)

                # Emit success signal
                self.scraping_finished.emit(self.query, response.items_scraped, True)

        except grpc.RpcError as e:
            error_msg = f"Failed to connect to scraper service: {e.details()}"
            self.scraping_error.emit(self.query, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during scraping: {str(e)}"
            self.scraping_error.emit(self.query, error_msg)


class FuzzySearchLineEdit(QtWidgets.QLineEdit):
    """Custom QLineEdit with fuzzy search dropdown functionality"""

    suggestion_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = None

        # Create dropdown list
        self.dropdown = QListWidget()
        self.dropdown.setWindowFlags(Qt.ToolTip)
        self.dropdown.hide()
        self.dropdown.itemClicked.connect(self._on_suggestion_clicked)

        # Timer for delayed search to avoid too many database calls
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._update_suggestions)

        # Connect text changes to trigger suggestions
        self.textChanged.connect(self._on_text_changed)

        # Style the dropdown
        self.dropdown.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #e3f2fd;
                max-height: 200px;
            }
            QListWidget::item {
                padding: 8px;
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

    def set_database_manager(self, db_manager):
        """Set the database manager for fuzzy search"""
        self.db_manager = db_manager

    def _on_text_changed(self, text):
        """Handle text changes with a delay to avoid excessive database calls"""
        if len(text.strip()) >= 2:  # Start suggesting after 2 characters
            self.search_timer.start(300)  # 300ms delay
        elif len(text.strip()) == 0 and self.hasFocus():  # Show all queries when empty and focused
            self._show_all_queries()
        else:
            self.dropdown.hide()

    def _show_all_queries(self):
        """Show all existing queries in the dropdown when search bar is empty and focused"""
        if not self.db_manager:
            return

        # Get all unique queries from database
        all_queries = self.db_manager.get_all_unique_queries()

        # Clear and populate dropdown
        self.dropdown.clear()

        if all_queries:
            for query in all_queries[:15]:  # Limit to 15 queries to avoid overwhelming dropdown
                item = QListWidgetItem(query)
                item.setToolTip(f"Search for: {query}")
                self.dropdown.addItem(item)

            # Position and show dropdown
            self._position_dropdown()
            self.dropdown.show()
        else:
            self.dropdown.hide()

    def _update_suggestions(self):
        """Update the suggestion dropdown"""
        if not self.db_manager:
            return

        text = self.text().strip()
        if len(text) < 2:
            self.dropdown.hide()
            return

        # Get fuzzy suggestions from database
        suggestions = self.db_manager.get_fuzzy_query_suggestions(text, limit=8)

        # Clear and populate dropdown
        self.dropdown.clear()

        if suggestions:
            for suggestion in suggestions:
                item = QListWidgetItem(suggestion)
                item.setToolTip(f"Search for: {suggestion}")
                self.dropdown.addItem(item)

            # Position and show dropdown
            self._position_dropdown()
            self.dropdown.show()
        else:
            self.dropdown.hide()

    def _position_dropdown(self):
        """Position the dropdown below the search bar"""
        pos = self.mapToGlobal(self.rect().bottomLeft())
        self.dropdown.move(pos)
        self.dropdown.resize(self.width(), min(200, self.dropdown.sizeHintForRow(0) * self.dropdown.count() + 4))

    def _on_suggestion_clicked(self, item):
        """Handle clicking on a suggestion"""
        suggestion = item.text()
        self.setText(suggestion)
        self.dropdown.hide()
        self.suggestion_selected.emit(suggestion)

    def keyPressEvent(self, event):
        """Handle keyboard navigation in dropdown"""
        if self.dropdown.isVisible():
            if event.key() == Qt.Key_Down:
                current_row = self.dropdown.currentRow()
                if current_row < self.dropdown.count() - 1:
                    self.dropdown.setCurrentRow(current_row + 1)
                return
            elif event.key() == Qt.Key_Up:
                current_row = self.dropdown.currentRow()
                if current_row > 0:
                    self.dropdown.setCurrentRow(current_row - 1)
                return
            elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                current_item = self.dropdown.currentItem()
                if current_item:
                    self._on_suggestion_clicked(current_item)
                    return
            elif event.key() == Qt.Key_Escape:
                self.dropdown.hide()
                return

        # Default handling for other keys
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        """Show all queries when focusing on empty search bar"""
        super().focusInEvent(event)
        if len(self.text().strip()) == 0:
            self._show_all_queries()

    def focusOutEvent(self, event):
        """Hide dropdown when focus is lost"""
        # Delay hiding to allow for clicking on suggestions
        QTimer.singleShot(200, self.dropdown.hide)
        super().focusOutEvent(event)


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
                # Get the current size of the label (accounting for padding)
                label_size = self.image_display_label.size()

                # Scale the image to fit the label while maintaining aspect ratio
                # Leave some padding around the image
                padding = 10
                target_size = QtCore.QSize(
                    label_size.width() - padding * 2,
                    label_size.height() - padding * 2
                )

                scaled_pixmap = pixmap.scaled(
                    target_size,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )

                self.image_display_label.setPixmap(scaled_pixmap)
                self.image_display_label.setText("")

                # Update stylesheet to maintain the border but remove background for the actual image
                self.image_display_label.setStyleSheet("""
                    QLabel {
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        background-color: white;
                    }
                """)
            else:
                self.image_display_label.setText("Failed to load image")
                self.image_display_label.setStyleSheet("""
                    QLabel {
                        color: #f44336; 
                        font-size: 14px;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        background-color: #f9f9f9;
                    }
                """)
        else:
            self.image_display_label.setText("Image not available")
            self.image_display_label.setStyleSheet("""
                QLabel {
                    color: #f44336; 
                    font-size: 14px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    background-color: #f9f9f9;
                }
            """)

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

    def _handle_label_resize(self):
        """Handle image label resize - rescale current image if any"""
        if (self.image_display_label and
                hasattr(self.image_display_label, 'pixmap') and
                self.image_display_label.pixmap() and
                not self.image_display_label.pixmap().isNull()):
            # Get original pixmap and rescale it
            current_pixmap = self.image_display_label.pixmap()

            # Get the current size of the label (accounting for padding)
            label_size = self.image_display_label.size()
            padding = 10
            target_size = QtCore.QSize(
                label_size.width() - padding * 2,
                label_size.height() - padding * 2
            )

            # Rescale the image
            scaled_pixmap = current_pixmap.scaled(
                target_size,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )

            self.image_display_label.setPixmap(scaled_pixmap)


class Ui_MainWindow(object):
    def __init__(self):
        """Initialize the UI with database manager"""
        self.db_manager = DatabaseManager()
        self.scraper_thread = None  # For background scraping operations
        self.scraping_timer = None  # For scraping animation
        self.scraping_query = ""  # Current scraping query
        self.scraping_dots = 0  # Animation counter
        self.current_chart_widget = None  # To hold the matplotlib canvas

    def setupUi(self, MainWindow):
        """Set up the main window UI components"""
        self._setup_main_window(MainWindow)
        self._setup_main_layout()
        self._setup_content_area()
        self._setup_connections()
        self.retranslateUi(MainWindow)

        # Set the central widget
        MainWindow.setCentralWidget(self.centralwidget)

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
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)  # Remove padding around main window
        self.gridLayout_3.setSpacing(0)  # Remove spacing
        self.gridLayout_3.setObjectName("gridLayout_3")

        self.Window = QtWidgets.QWidget(self.centralwidget)
        self.Window.setObjectName("Window")

        self.gridLayout = QtWidgets.QGridLayout(self.Window)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding around window content
        self.gridLayout.setSpacing(0)  # Remove spacing
        self.gridLayout.setObjectName("gridLayout")

        self.gridLayout_3.addWidget(self.Window, 0, 0, 1, 1)

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

        # Search bar with fuzzy search functionality
        self.search_bar = FuzzySearchLineEdit(self.head_content)
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

        # Add sentiment analysis button after search
        self._add_sentiment_button()

    def _add_sentiment_button(self):
        """Add sentiment analysis button to the header"""
        # Add some spacing before the button
        spacerItem3 = QtWidgets.QSpacerItem(
            20, 20,
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout_2.addItem(spacerItem3)

        # Sentiment analysis button
        self.sentiment_button = QtWidgets.QPushButton(self.head_content)
        self.sentiment_button.setMinimumSize(QtCore.QSize(120, 35))
        self.sentiment_button.setMaximumSize(QtCore.QSize(150, 35))
        self.sentiment_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                font: bold 10pt "Segoe UI";
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.sentiment_button.setText("Analyze")
        self.sentiment_button.setObjectName("sentiment_button")

        # Connect to sentiment analysis function
        self.sentiment_button.clicked.connect(self.open_sentiment_analysis)

        self.horizontalLayout_2.addWidget(self.sentiment_button)

        # Add clear database button after sentiment analysis
        self._add_clear_database_button()

    def _add_clear_database_button(self):
        """Add clear database button to the header"""
        # Add some spacing before the button
        spacerItem4 = QtWidgets.QSpacerItem(
            20, 20,
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout_2.addItem(spacerItem4)

        # Clear database button
        self.clear_db_button = QtWidgets.QPushButton(self.head_content)
        self.clear_db_button.setMinimumSize(QtCore.QSize(120, 35))
        self.clear_db_button.setMaximumSize(QtCore.QSize(150, 35))
        self.clear_db_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font: bold 10pt "Segoe UI";
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.clear_db_button.setText("🗑️ Clear DB")
        self.clear_db_button.setObjectName("clear_db_button")

        # Connect to clear database function
        self.clear_db_button.clicked.connect(self.clear_database)

        self.horizontalLayout_2.addWidget(self.clear_db_button)

    def _setup_main_content(self):
        """Set up the main content area with product information and table"""
        # Create main content widget
        self.main_content_widget = QtWidgets.QWidget(self.content)
        self.main_content_widget.setObjectName("main_content_widget")

        # Main vertical layout to hold the splitter
        self.main_vertical_layout = QtWidgets.QVBoxLayout(self.main_content_widget)
        self.main_vertical_layout.setContentsMargins(10, 10, 10, 10)  # Minimal padding
        self.main_vertical_layout.setSpacing(0)
        self.main_vertical_layout.setObjectName("main_vertical_layout")

        # Create main vertical splitter for 30/70 split (adjustable by mouse)
        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.main_splitter.setObjectName("main_splitter")

        # Set splitter handle style
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e8e8e8;
                border: none;
                height: 2px;
                margin: 1px 0px;
            }
            QSplitter::handle:hover {
                background-color: #0059ff;
                height: 3px;
            }
            QSplitter::handle:pressed {
                background-color: #004cd1;
                height: 3px;
            }
        """)

        # Add content sections
        self._setup_product_sections()
        self._setup_product_table()

        # Set initial splitter sizes (30% top, 70% bottom)
        self.main_splitter.setSizes([300, 700])  # Approximate 30/70 ratio
        self.main_splitter.setCollapsible(0, False)  # Don't allow top section to collapse
        self.main_splitter.setCollapsible(1, False)  # Don't allow bottom section to collapse

        # Add splitter to main layout
        self.main_vertical_layout.addWidget(self.main_splitter)

        # Add main content widget to content layout
        self.content_layout.addWidget(self.main_content_widget)

    def _on_chart_type_changed(self):
        '''Handler for user to select different chart type on the dropdown'''
        search = self.search_bar.text().strip()

        if search:
            self._update_comparison_chart(search)

    def _setup_product_sections(self):
        """Set up product image and comparison chart sections with 50/50 horizontal split"""
        # Create top section container (will be added to main splitter)
        self.top_section = QtWidgets.QWidget()
        self.top_section.setObjectName("top_section")
        self.top_section.setMinimumHeight(150)  # Minimum height for usability

        # Create horizontal splitter for 50/50 split (adjustable by mouse)
        self.horizontal_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.horizontal_splitter.setObjectName("horizontal_splitter")

        # Set horizontal splitter handle style
        self.horizontal_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e8e8e8;
                border: none;
                width: 2px;
                margin: 0px 1px;
            }
            QSplitter::handle:hover {
                background-color: #0059ff;
                width: 3px;
            }
            QSplitter::handle:pressed {
                background-color: #004cd1;
                width: 3px;
            }
        """)

        # Left side - Product Image section (50%)
        self.product_image_container = QtWidgets.QWidget()
        self.product_image_container.setObjectName("product_image_container")
        self.product_image_container.setMinimumWidth(200)  # Minimum width

        # Layout for product image section
        self.image_layout = QtWidgets.QVBoxLayout(self.product_image_container)
        self.image_layout.setContentsMargins(5, 5, 5, 5)
        self.image_layout.setSpacing(5)

        # Product image title
        self.gambar_produk_title = QtWidgets.QLabel(self.product_image_container)
        self.gambar_produk_title.setMaximumSize(QtCore.QSize(16777215, 30))
        self.gambar_produk_title.setStyleSheet("font: 87 12pt \"Segoe UI Black\";")
        self.gambar_produk_title.setObjectName("gambar_produk_title")
        self.image_layout.addWidget(self.gambar_produk_title)

        # Product image
        self.gambar_produk = QtWidgets.QLabel(self.product_image_container)
        self.gambar_produk.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
        """)
        self.gambar_produk.setText("")
        self.gambar_produk.setScaledContents(False)  # Don't scale contents - we'll handle it manually
        self.gambar_produk.setAlignment(QtCore.Qt.AlignCenter)  # Center the image
        self.gambar_produk.setObjectName("gambar_produk")
        self.image_layout.addWidget(self.gambar_produk, 1)  # Give it stretch factor 1

        # Right side - Comparison Chart section (50%)
        self.comparison_chart_container = QtWidgets.QWidget()
        self.comparison_chart_container.setObjectName("comparison_chart_container")
        self.comparison_chart_container.setMinimumWidth(200)  # Minimum width

        # Layout for comparison chart section
        self.chart_layout = QtWidgets.QVBoxLayout(self.comparison_chart_container)
        self.chart_layout.setContentsMargins(5, 5, 5, 5)
        self.chart_layout.setSpacing(5)

        #horizontal layout for title and dropdown
        chart_title_layout =QtWidgets.QHBoxLayout()
        chart_title_layout.setContentsMargins(0, 0, 0, 0)

        # Comparison chart title
        self.grafik_perbandingan_title = QtWidgets.QLabel(self.comparison_chart_container)
        self.grafik_perbandingan_title.setMaximumSize(QtCore.QSize(16777215, 30))
        self.grafik_perbandingan_title.setStyleSheet("font: 87 12pt \"Segoe UI Black\";")
        self.grafik_perbandingan_title.setObjectName("grafik_perbandingan_title")
        chart_title_layout.addWidget(self.grafik_perbandingan_title)

        # Putting Dropdown push to the right
        chart_title_layout.addStretch()

        # Configuration of the dropdown for selected chart
        self.chart_type_dropdown = QtWidgets.QComboBox(self.comparison_chart_container)
        self.chart_type_dropdown.addItems(["Bar Chart", "Box Plot"])
        self.chart_type_dropdown.setMinimumSize(QtCore.QSize(120, 25))
        self.chart_type_dropdown.setStyleSheet("""
                   QComboBox {
                       border: 1px solid #ccc;
                       border-radius: 4px;
                       padding: 1px 18px 1px 3px;
                       min-width: 6em;
                       background-color: white;
                   }
                   QComboBox::drop-down {
                       subcontrol-origin: padding;
                       subcontrol-position: top right;
                       width: 20px;
                       border-left-width: 1px;
                       border-left-color: darkgray;
                       border-left-style: solid;
                       border-top-right-radius: 3px;
                       border-bottom-right-radius: 3px;
                   }
               """)
        chart_title_layout.addWidget(self.chart_type_dropdown)
        self.chart_layout.addLayout(chart_title_layout)
        self.chart_type_dropdown.currentIndexChanged.connect(self._on_chart_type_changed)

        # Comparison chart placeholder
        self.grafik_perbandingan = QtWidgets.QLabel(self.comparison_chart_container)
        self.grafik_perbandingan.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
            }
        """)
        self.grafik_perbandingan.setText("Chart will be displayed here")
        self.grafik_perbandingan.setAlignment(QtCore.Qt.AlignCenter)
        self.grafik_perbandingan.setScaledContents(False)
        self.grafik_perbandingan.setObjectName("grafik_perbandingan")
        self.chart_layout.addWidget(self.grafik_perbandingan, 1)  # Give it stretch factor 1

        self.current_chart_widget = self.grafik_perbandingan

        # Add both containers to horizontal splitter (50/50 split, adjustable)
        self.horizontal_splitter.addWidget(self.product_image_container)
        self.horizontal_splitter.addWidget(self.comparison_chart_container)

        # Set initial sizes (50/50)
        self.horizontal_splitter.setSizes([500, 500])
        self.horizontal_splitter.setCollapsible(0, False)  # Don't allow left section to collapse
        self.horizontal_splitter.setCollapsible(1, False)  # Don't allow right section to collapse

        # Create layout for top section and add horizontal splitter
        top_layout = QtWidgets.QVBoxLayout(self.top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(5)
        top_layout.addWidget(self.horizontal_splitter)

        # Add top section to main vertical splitter
        self.main_splitter.addWidget(self.top_section)

        # Add product description title (will be above the table)
        self.table_section = QtWidgets.QWidget()
        self.table_section.setObjectName("table_section")

        self.table_layout = QtWidgets.QVBoxLayout(self.table_section)
        self.table_layout.setContentsMargins(5, 5, 5, 5)
        self.table_layout.setSpacing(5)

        self.deskripsi_produk_title = QtWidgets.QLabel(self.table_section)
        self.deskripsi_produk_title.setMaximumSize(QtCore.QSize(16777215, 30))
        self.deskripsi_produk_title.setStyleSheet("font: 87 12pt \"Segoe UI Black\";")
        self.deskripsi_produk_title.setObjectName("deskripsi_produk_title")
        self.table_layout.addWidget(self.deskripsi_produk_title)

    def _setup_product_table(self):
        """Set up the product data table (70% of vertical space)"""
        self.tabel_produk = ProductTableWidget(self.table_section)

        # Set size policy for table - expanding
        table_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.tabel_produk.setSizePolicy(table_policy)
        self.tabel_produk.setMinimumSize(QtCore.QSize(0, 200))

        # Set table styling
        self.tabel_produk.setStyleSheet("""
            QTableView {
                border-radius: 8px;
                border: 1px solid #ddd;
                background-color: white;
            }

            QHeaderView::section {
                border: none;
                border-bottom: 2px solid #0059ff;
                background-color: #f8f9fa;
                text-align: left;
                padding: 8px 12px;
                font-family: "Segoe UI Semibold";
                font-weight: 600;
                color: #333;
            }

            QHeaderView::section:hover {
                background-color: #e3f2fd;
                color: #1976d2;
            }

            QHeaderView::section:pressed {
                background-color: #bbdefb;
            }

            QHeaderView::up-arrow {
                color: #0059ff;
                width: 12px;
                height: 12px;
                margin-right: 5px;
            }

            QHeaderView::down-arrow {
                color: #0059ff;
                width: 12px;
                height: 12px;
                margin-right: 5px;
            }

            QTableView::item {
                border-bottom: 1px solid #f0f0f0;
                padding: 8px 12px;
                background-color: white;
            }

            QTableView::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }

            QTableView::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.tabel_produk.setObjectName("tabel_produk")

        # Set up table structure
        self._setup_table_columns()
        self._configure_table_behavior()

        # Connect the image display label to the table for hover previews
        self.tabel_produk.set_image_display_label(self.gambar_produk)

        # Enable context menu for table
        self.tabel_produk.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tabel_produk.customContextMenuRequested.connect(self._show_context_menu)

        # Connect cell click events for View button
        self.tabel_produk.cellClicked.connect(self._handle_cell_click)

        # Set initial placeholder text for the image label
        self.gambar_produk.clear()
        self.gambar_produk.setText("Hover over a product to see its image")
        self.gambar_produk.setAlignment(QtCore.Qt.AlignCenter)
        self.gambar_produk.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 12px;
                font-style: italic;
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
        """)

        # Add refresh button above the table
        self._add_refresh_button()

        # Add table to table layout
        self.table_layout.addWidget(self.tabel_produk, 1)  # Give it stretch factor 1

        # Add table section to main vertical splitter
        self.main_splitter.addWidget(self.table_section)

    def _add_refresh_button(self):
        """Add a refresh button above the table"""
        # Create button container
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 5, 0, 5)

        # Add spacer to push button to the right
        spacer = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        button_layout.addItem(spacer)

        # Create refresh button
        self.refresh_button = QtWidgets.QPushButton("🔄 Refresh Table")
        self.refresh_button.setMinimumSize(QtCore.QSize(120, 30))
        self.refresh_button.setMaximumSize(QtCore.QSize(150, 30))
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 5px;
                font: bold 10pt "Segoe UI";
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.refresh_button.setObjectName("refresh_button")

        # Connect refresh functionality
        self.refresh_button.clicked.connect(self._handle_manual_refresh)

        button_layout.addWidget(self.refresh_button)

        # Add button container to table layout (before the table)
        self.table_layout.addWidget(button_container)

    def _setup_table_columns(self):
        """Set up table columns and headers"""
        self.tabel_produk.setColumnCount(6)
        self.tabel_produk.setRowCount(0)

        # Set column headers
        headers = [
            "Nama Produk", "Platform", "Rating",
            "Amount", "Sentiment", "Action"
        ]

        for i, header in enumerate(headers):
            item = QtWidgets.QTableWidgetItem(header)
            self.tabel_produk.setHorizontalHeaderItem(i, item)

    def _configure_table_behavior(self):
        """Configure table resizing and scroll behavior"""
        # Set table to resize columns automatically and fill full width
        self.tabel_produk.horizontalHeader().setStretchLastSection(True)
        self.tabel_produk.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        # Ensure table uses full available width and maintains minimum sizes
        self.tabel_produk.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Set minimum section sizes to prevent columns from becoming too small
        header = self.tabel_produk.horizontalHeader()
        header.setMinimumSectionSize(80)  # Minimum column width

        # Enable interactive sorting - Qt will handle click behavior automatically
        self.tabel_produk.setSortingEnabled(True)

        # Configure sorting behavior
        header.setSortIndicatorShown(True)  # Show sort arrows in headers
        header.setSectionsClickable(True)  # Enable clicking on headers

        # Connect to custom sort handler to disable Action column sorting
        header.sectionClicked.connect(self._handle_header_click)

        # Ensure the table maintains its size policy
        self.tabel_produk.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

    def _setup_connections(self):
        """Set up signal-slot connections"""
        # Connect search functionality
        self.search_button.clicked.connect(self._handle_search)
        self.search_bar.returnPressed.connect(self._handle_search)

        # Connect fuzzy search functionality
        self.search_bar.set_database_manager(self.db_manager)
        self.search_bar.suggestion_selected.connect(self._handle_suggestion_selected)

    def _update_comparison_chart(self, search):
        """Generate and display the comparison chart for the search term."""
        try:

            data = DataSortingScrapper(search)
            chart_type = self.chart_type_dropdown.currentText()

            if chart_type == 'Bar Chart':
                figure = data.bar_chart()
            elif chart_type == 'Box Plot':
                figure = data.box_plot()
            else:
                figure = None

            # Remove the previous widget (placeholder or old chart)
            if self.current_chart_widget:
                self.current_chart_widget.deleteLater()
                self.current_chart_widget = None

            if figure:
                # Create and add the new chart canvas
                canvas = FigureCanvas(figure)
                self.chart_layout.addWidget(canvas)
                self.current_chart_widget = canvas  # Update the tracker
            else:
                # If no data, show a placeholder message
                self._set_chart_placeholder("Not enough data to generate a chart.")

        except Exception as e:
            print(f"Error generating chart: {e}")
            self._set_chart_placeholder("An error occurred while generating the chart.")

    def _clear_comparison_chart(self, message="Chart will be displayed here"):
        """Clears the comparison chart area and shows a placeholder message."""
        self._set_chart_placeholder(message)

    def _set_chart_placeholder(self, message):
        '''Removes current chart and then displays a new chart Qlabel'''
        if self.current_chart_widget:
            self.current_chart_widget.deleteLater()
            self.current_chart_widget = None

        #Creating new chart
        placeholder = QtWidgets.QLabel(self.comparison_chart_container)
        placeholder.setStyleSheet("""
            QLabel{
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
            }
        """)
        placeholder.setText(message)
        placeholder.setAlignment(QtCore.Qt.AlignCenter)
        placeholder.setWordWrap(True)
        self.chart_layout.addWidget(placeholder, 1)
        self.current_chart_widget = placeholder


    def _handle_manual_refresh(self):
        """Handle manual refresh button click"""
        try:
            # Disable refresh button during refresh
            self.refresh_button.setEnabled(False)
            self.refresh_button.setText("🔄 Refreshing...")

            # Check if we're currently showing search results or all products
            search_term = self.search_bar.text().strip()
            if search_term:
                # Refresh search results
                products = self.db_manager.search_products(search_term)
                self._populate_table(products)
                self._update_comparison_chart(search_term)  # Refresh chart
                print(f"Manual refresh: {len(products)} products found for '{search_term}'")
            else:
                # Refresh all products
                self._load_data_from_database()
                self._clear_comparison_chart()  # Clear chart

            # Update the image display to reflect the table refresh
            self.gambar_produk.setText("Hover over a product to see its image")
            self.gambar_produk.setStyleSheet("""
                QLabel {
                    color: #999;
                    font-size: 12px;
                    font-style: italic;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    background-color: #f9f9f9;
                }
            """)

            print("Table refreshed manually")

        except Exception as e:
            print(f"Error during manual refresh: {e}")
            QtWidgets.QMessageBox.warning(
                self.centralwidget.parent(),
                "Refresh Error",
                f"Failed to refresh table:\n{str(e)}"
            )
        finally:
            # Re-enable refresh button
            self.refresh_button.setEnabled(True)
            self.refresh_button.setText("🔄 Refresh Table")

    def _handle_header_click(self, logical_index):
        """Handle header clicks, but prevent sorting on Action column"""
        if logical_index == 5:  # Action column (index 5)
            return  # Do nothing for Action column
        # For all other columns, Qt's built-in sorting will handle it automatically

    def _handle_suggestion_selected(self, suggestion):
        """Handle when a fuzzy search suggestion is selected"""
        # Automatically trigger search when suggestion is selected
        self._handle_search()

    def _handle_cell_click(self, row, column):
        """Handle cell clicks, specifically for the View button"""
        if column == 5:  # Action column (View button)
            if hasattr(self, 'current_products') and row < len(self.current_products):
                product = self.current_products[row]
                self._open_product_details(product)

    def _show_context_menu(self, position):
        """Show context menu for table items"""
        item = self.tabel_produk.itemAt(position)
        if item is None:
            return

        row = item.row()
        if not hasattr(self, 'current_products') or row >= len(self.current_products):
            return

        product = self.current_products[row]

        # Create context menu
        context_menu = QtWidgets.QMenu(self)

        # View Details action
        details_action = context_menu.addAction("📋 View Details")
        details_action.triggered.connect(lambda: self._open_product_details(product))

        # Open in Browser action
        browser_action = context_menu.addAction("🌐 Open in Browser")
        browser_action.triggered.connect(lambda: self._open_in_browser(product))

        # Copy Link action
        copy_action = context_menu.addAction("📎 Copy Link")
        copy_action.triggered.connect(lambda: self._copy_product_link(product))

        # Show the menu
        context_menu.exec_(self.tabel_produk.mapToGlobal(position))

    def _open_product_details(self, product):
        """Open product details dialog"""
        try:
            dialog = ProductDetailDialog(product, self.centralwidget.parent())

            # Connect the product_deleted signal to refresh the table
            dialog.product_deleted.connect(self._on_product_deleted)

            dialog.exec_()
        except Exception as e:
            print(f"Error opening product details: {e}")
            QtWidgets.QMessageBox.critical(
                self.centralwidget.parent(),
                "Error",
                f"Failed to open product details:\n{str(e)}"
            )

    def _on_product_deleted(self, product_id):
        """Handle when a product is deleted from the detail dialog"""
        print(f"Product {product_id} was deleted, refreshing table...")

        # Check if we're currently showing search results or all products
        search_term = self.search_bar.text().strip()
        if search_term:
            # Refresh search results
            products = self.db_manager.search_products(search_term)
            self._populate_table(products)
            self._update_comparison_chart(search_term)  # Refresh chart
            print(f"Refreshed search results: {len(products)} products found")
        else:
            # Refresh all products
            self._load_data_from_database()
            self._clear_comparison_chart()  # Clear chart

        # Update the image display to reflect the table refresh
        self.gambar_produk.setText("Hover over a product to see its image")
        self.gambar_produk.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 12px;
                font-style: italic;
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
        """)

    def _open_in_browser(self, product):
        """Open product link directly in browser"""
        link = product.get('link')
        if link:
            try:
                webbrowser.open(link)
                print(f"Opened product in browser: {link}")
            except Exception as e:
                print(f"Error opening browser: {e}")
                QtWidgets.QMessageBox.warning(
                    self.centralwidget.parent(),
                    "Browser Error",
                    f"Could not open link in browser:\n{str(e)}"
                )
        else:
            QtWidgets.QMessageBox.information(
                self.centralwidget.parent(),
                "No Link",
                "No product link is available for this item."
            )

    def _copy_product_link(self, product):
        """Copy product link to clipboard"""
        link = product.get('link')
        if link:
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(link)
            print(f"Copied product link to clipboard: {link}")

            # Show temporary message (you could also use a status bar or tooltip)
            QtWidgets.QMessageBox.information(
                self.centralwidget.parent(),
                "Link Copied",
                "Product link copied to clipboard!"
            )
        else:
            QtWidgets.QMessageBox.information(
                self.centralwidget.parent(),
                "No Link",
                "No product link is available to copy."
            )

    def _handle_search(self):
        """Handle search button click or Enter key press"""
        search_term = self.search_bar.text().strip()
        if search_term:
            products = self.db_manager.search_products(search_term)

            if len(products) > 0:
                # Store current splitter sizes before populating table
                current_sizes = None
                if hasattr(self, 'main_splitter'):
                    current_sizes = self.main_splitter.sizes()

                # Found products - display them
                self._populate_table(products)
                self._update_comparison_chart(search_term)  # Call to update chart
                print(f"Search for '{search_term}': Found {len(products)} products in matching queries")

                # Restore splitter sizes to prevent layout changes
                if current_sizes and hasattr(self, 'main_splitter'):
                    self.main_splitter.setSizes(current_sizes)

                # Update image display to show search feedback
                self.gambar_produk.setText("Hover over a product to see its image")
                self.gambar_produk.setStyleSheet("""
                    QLabel {
                        color: #999;
                        font-size: 12px;
                        font-style: italic;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        background-color: #f9f9f9;
                    }
                """)
            else:
                # No products found - prompt user to scrape
                self._prompt_for_scraping(search_term)
                self._clear_comparison_chart()  # Clear chart
        else:
            self._load_data_from_database()
            self._clear_comparison_chart()  # Clear chart

    def _prompt_for_scraping(self, query):
        """Show popup asking if user wants to scrape for the query"""
        # Update image display to show no results
        self.gambar_produk.setText(f"No products found for query: '{query}'")
        self.gambar_produk.setStyleSheet("""
            QLabel {
                color: #f44336;
                font-size: 14px;
                font-style: italic;
            }
        """)

        # Create message box
        msg_box = QMessageBox()
        msg_box.setWindowTitle("No Results Found")
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText(f"No products found for '{query}'.")
        msg_box.setInformativeText("Would you like to scrape the web for new products matching this query?")

        # Add custom buttons
        scrape_button = msg_box.addButton("Scrape Now", QMessageBox.YesRole)
        cancel_button = msg_box.addButton("Cancel", QMessageBox.NoRole)

        # Style the message box
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #1565c0;
            }
            QMessageBox QPushButton[text="Cancel"] {
                background-color: #757575;
            }
            QMessageBox QPushButton[text="Cancel"]:hover {
                background-color: #616161;
            }
        """)

        # Show message box and handle response
        msg_box.exec_()

        if msg_box.clickedButton() == scrape_button:
            self._start_scraping(query)

    def _start_scraping(self, query):
        """Start scraping process in background thread"""
        print(f"Starting scraping for query: '{query}'")

        # Update UI to show scraping in progress with animated dots
        self.scraping_query = query
        self.scraping_dots = 0
        self._update_scraping_animation()

        # Start animation timer
        self.scraping_timer = QTimer()
        self.scraping_timer.timeout.connect(self._update_scraping_animation)
        self.scraping_timer.start(500)  # Update every 500ms

        # Disable search controls during scraping
        self.search_bar.setEnabled(False)
        self.search_button.setEnabled(False)

        # Start scraper thread
        self.scraper_thread = ScraperWorkerThread(query)
        self.scraper_thread.scraping_started.connect(self._on_scraping_started)
        self.scraper_thread.scraping_finished.connect(self._on_scraping_finished)
        self.scraper_thread.scraping_error.connect(self._on_scraping_error)
        self.scraper_thread.start()

    def _update_scraping_animation(self):
        """Update the scraping animation with dots"""
        self.scraping_dots = (self.scraping_dots + 1) % 4
        dots = "." * self.scraping_dots
        self.gambar_produk.setText(f"Scraping products for '{self.scraping_query}'{dots}\nPlease wait...")
        self.gambar_produk.setStyleSheet("""
            QLabel {
                color: #1976d2;
                font-size: 14px;
                font-weight: bold;
            }
        """)

    def _on_scraping_started(self, query):
        """Handle scraping started signal"""
        print(f"Scraping started for: {query}")

    def _on_scraping_finished(self, query, items_scraped, success):
        """Handle scraping finished signal"""
        # Stop animation timer
        if hasattr(self, 'scraping_timer'):
            self.scraping_timer.stop()

        # Re-enable search controls
        self.search_bar.setEnabled(True)
        self.search_button.setEnabled(True)

        if success and items_scraped > 0:
            print(f"Scraping completed: {items_scraped} items found for '{query}'")

            # Show success message
            self.gambar_produk.setText(f"✓ Found {items_scraped} new products!\nScraping completed.")
            self.gambar_produk.setStyleSheet("""
                QLabel {
                    color: #4caf50;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)

            # Prompt user to refresh the table
            self._prompt_for_refresh(query, items_scraped)

        else:
            self._on_scraping_error(query, f"No products found during scraping")

    def _on_scraping_error(self, query, error_message):
        """Handle scraping error signal"""
        # Stop animation timer
        if hasattr(self, 'scraping_timer'):
            self.scraping_timer.stop()

        # Re-enable search controls
        self.search_bar.setEnabled(True)
        self.search_button.setEnabled(True)

        print(f"Scraping failed for '{query}': {error_message}")

        # Show error message
        self.gambar_produk.setText(f"✗ Scraping failed:\n{error_message}")
        self.gambar_produk.setStyleSheet("""
            QLabel {
                color: #f44336;
                font-size: 12px;
                font-style: italic;
            }
        """)

        # Show error dialog
        QMessageBox.warning(
            None,
            "Scraping Failed",
            f"Failed to scrape products for '{query}'.\n\nError: {error_message}\n\nPlease make sure the scraper service is running."
        )

    def _prompt_for_refresh(self, query, items_scraped):
        """Prompt user to refresh the table after successful scraping"""
        # Create message box
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Scraping Completed")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"Successfully scraped {items_scraped} new products for '{query}'!")
        msg_box.setInformativeText("Would you like to refresh the table to see the new results?")

        # Add custom buttons
        refresh_button = msg_box.addButton("Refresh Now", QMessageBox.YesRole)
        later_button = msg_box.addButton("Refresh Later", QMessageBox.NoRole)

        # Style the message box
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #45a049;
            }
            QMessageBox QPushButton[text="Refresh Later"] {
                background-color: #757575;
            }
            QMessageBox QPushButton[text="Refresh Later"]:hover {
                background-color: #616161;
            }
        """)

        # Show message box and handle response
        msg_box.exec_()

        if msg_box.clickedButton() == refresh_button:
            # User chose to refresh immediately
            print("User chose to refresh table after scraping")
            self._refresh_search_results(query)
        else:
            # User chose to refresh later
            print("User chose to refresh table later")
            # Update image display to indicate refresh is available
            self.gambar_produk.setText(
                f"✓ Found {items_scraped} new products for '{query}'!\nClick 'Refresh Table' to see results.")
            self.gambar_produk.setStyleSheet("""
                QLabel {
                    color: #4caf50;
                    font-size: 12px;
                    font-weight: bold;
                    border: 1px solid #4caf50;
                    border-radius: 8px;
                    background-color: #f1f8e9;
                    padding: 5px;
                }
            """)

    def _refresh_search_results(self, query):
        """Refresh search results after scraping"""
        # Search again to show new results
        products = self.db_manager.search_products(query)
        if len(products) > 0:
            self._populate_table(products)
            self._update_comparison_chart(query)  # Update chart with new results
            print(f"Refreshed search results: Found {len(products)} products for '{query}'")

            # Reset image display
            self.gambar_produk.setText("Hover over a product to see its image")
            self.gambar_produk.setStyleSheet("""
                QLabel {
                    color: #999;
                    font-size: 12px;
                    font-style: italic;
                }
            """)
        else:
            # Still no results - show message
            self.gambar_produk.setText(f"No products found for '{query}' even after scraping")
            self.gambar_produk.setStyleSheet("""
                QLabel {
                    color: #f44336;
                    font-size: 12px;
                    font-style: italic;
                }
            """)
            self._clear_comparison_chart()

    def closeEvent(self, event):
        """Handle application closing - cleanup background threads"""
        if self.scraper_thread and self.scraper_thread.isRunning():
            self.scraper_thread.quit()
            self.scraper_thread.wait()
        event.accept()

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event) if hasattr(super(), 'resizeEvent') else None

        # Trigger image rescaling if there's a current image displayed
        if (hasattr(self, 'tabel_produk') and
                hasattr(self.tabel_produk, '_handle_label_resize')):
            # Use a timer to avoid excessive calls during resize
            if not hasattr(self, '_resize_timer'):
                self._resize_timer = QTimer()
                self._resize_timer.setSingleShot(True)
                self._resize_timer.timeout.connect(self.tabel_produk._handle_label_resize)

            self._resize_timer.start(100)  # 100ms delay

    def open_sentiment_analysis(self):
        """Open sentiment analysis configuration dialog"""
        try:
            # Find the main window widget - it's the parent of our central widget
            main_window = self.centralwidget.parent()
            dialog = SentimentAnalysisDialog(main_window)
            result = dialog.exec_()

            if result == QtWidgets.QDialog.Accepted:
                # Sentiment analysis completed successfully
                print("Sentiment analysis completed successfully")

                # Optionally refresh the product table to show updated sentiment scores
                if hasattr(self, 'current_products') and self.current_products:
                    # If we have current search results, refresh them
                    current_query = self.search_bar.text().strip()
                    if current_query:
                        products = self.db_manager.search_products(current_query)
                        self._populate_table(products)
                        print("Product table refreshed with new sentiment scores")

        except Exception as e:
            print(f"Error opening sentiment analysis dialog: {e}")
            # Use None as parent to avoid the type error
            QMessageBox.critical(
                None,
                "Error",
                f"Failed to open sentiment analysis dialog:\n\n{e}"
            )

    def clear_database(self):
        """Clear all data from the database with confirmation"""
        try:
            # Create confirmation dialog
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Clear Database")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("⚠️ Clear Database Warning")
            msg_box.setInformativeText(
                "This will permanently delete ALL data from the database:\n\n"
                "• All scraped products\n"
                "• All search queries\n"
                "• All sentiment analysis results\n\n"
                "This action cannot be undone!\n\n"
                "Are you sure you want to continue?"
            )

            # Add custom buttons
            clear_button = msg_box.addButton("🗑️ Clear Database", QMessageBox.YesRole)
            cancel_button = msg_box.addButton("Cancel", QMessageBox.NoRole)

            # Style the message box
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                    font-size: 14px;
                }
                QMessageBox QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 12px;
                    min-width: 100px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #d32f2f;
                }
                QMessageBox QPushButton[text="Cancel"] {
                    background-color: #757575;
                }
                QMessageBox QPushButton[text="Cancel"]:hover {
                    background-color: #616161;
                }
            """)

            # Show message box and handle response
            result = msg_box.exec_()

            if msg_box.clickedButton() == clear_button:
                # User confirmed - proceed with clearing database
                print("User confirmed database clearing")

                # Disable the clear button during operation
                self.clear_db_button.setEnabled(False)
                self.clear_db_button.setText("🗑️ Clearing...")

                # Clear the database
                if self.db_manager.clear_all_data():
                    print("Database cleared successfully")

                    # Refresh the UI to show empty state
                    self._load_data_from_database()
                    self._clear_comparison_chart("Database Cleared")  # Clear chart

                    # Reset image display
                    self.gambar_produk.setText("Database cleared!\nAll products have been removed.")
                    self.gambar_produk.setStyleSheet("""
                        QLabel {
                            color: #4caf50;
                            font-size: 14px;
                            font-weight: bold;
                            border: 1px solid #4caf50;
                            border-radius: 8px;
                            background-color: #e8f5e8;
                            padding: 10px;
                        }
                    """)

                    # Clear search bar
                    self.search_bar.clear()

                    # Show success message
                    QMessageBox.information(
                        self.centralwidget.parent(),
                        "Database Cleared",
                        "✅ Database has been successfully cleared!\n\n"
                        "All products, queries, and sentiment data have been removed."
                    )

                else:
                    # Database clearing failed
                    print("Failed to clear database")
                    QMessageBox.critical(
                        self.centralwidget.parent(),
                        "Clear Database Failed",
                        "❌ Failed to clear the database.\n\n"
                        "There may have been an error during the operation. "
                        "Please check the console for more details."
                    )

                # Re-enable the clear button
                self.clear_db_button.setEnabled(True)
                self.clear_db_button.setText("🗑️ Clear DB")

            else:
                print("User canceled database clearing")

        except Exception as e:
            print(f"Error in clear database operation: {e}")
            QMessageBox.critical(
                self.centralwidget.parent(),
                "Error",
                f"Failed to clear database:\n\n{e}"
            )

            # Re-enable the clear button in case of error
            if hasattr(self, 'clear_db_button'):
                self.clear_db_button.setEnabled(True)
                self.clear_db_button.setText("🗑️ Clear DB")

    def _load_data_from_database(self):
        """Load all products from database and populate table"""
        try:
            # Store current splitter sizes before populating table
            current_sizes = None
            if hasattr(self, 'main_splitter'):
                current_sizes = self.main_splitter.sizes()

            products = self.db_manager.get_all_products()
            self._populate_table(products)

            # Restore splitter sizes to prevent layout changes
            if current_sizes and hasattr(self, 'main_splitter'):
                self.main_splitter.setSizes(current_sizes)

            print(f"Loaded {len(products)} products from database")
        except Exception as e:
            print(f"Error loading data from database: {e}")

    def _populate_table(self, products):
        """Populate the table with product data"""
        # Store products for use in click handlers and other functionality
        self.current_products = products

        # Temporarily disable sorting during population to prevent layout issues
        self.tabel_produk.setSortingEnabled(False)

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

            # Rating - create custom item for proper numeric sorting
            rating = product.get('review_score')
            if rating:
                rating_text = f"{rating:.1f}"
                rating_item = QtWidgets.QTableWidgetItem()
                rating_item.setText(rating_text)
                rating_item.setData(QtCore.Qt.DisplayRole, rating_text)
                rating_item.setData(QtCore.Qt.UserRole, rating)  # Store numeric value for sorting
            else:
                rating_item = QtWidgets.QTableWidgetItem()
                rating_item.setText("N/A")
                rating_item.setData(QtCore.Qt.DisplayRole, "N/A")
                rating_item.setData(QtCore.Qt.UserRole, -1)  # N/A values sort to bottom
            self.tabel_produk.setItem(row, 2, rating_item)

            # Amount (Price) - create custom item for proper numeric sorting
            price = product.get('price')
            if price and price > 0:
                amount_text = f"${price:.2f}"
                amount_item = QtWidgets.QTableWidgetItem()
                amount_item.setText(amount_text)
                amount_item.setData(QtCore.Qt.DisplayRole, amount_text)
                amount_item.setData(QtCore.Qt.UserRole, price)  # Store numeric value for sorting
            else:
                amount_item = QtWidgets.QTableWidgetItem()
                amount_item.setText("N/A")
                amount_item.setData(QtCore.Qt.DisplayRole, "N/A")
                amount_item.setData(QtCore.Qt.UserRole, -1)  # N/A values sort to bottom
            self.tabel_produk.setItem(row, 3, amount_item)

            # Sentiment - create custom item for proper numeric sorting
            sentiment = product.get('sentiment_score')
            if sentiment is not None:
                # Sentiment scores are normalized from -1 (very negative) to 1 (very positive)
                if sentiment >= 0.3:
                    status_text = f"Positive ({sentiment:.2f})"
                elif sentiment >= -0.3:
                    status_text = f"Neutral ({sentiment:.2f})"
                else:
                    status_text = f"Negative ({sentiment:.2f})"

                status_item = QtWidgets.QTableWidgetItem()
                status_item.setText(status_text)
                status_item.setData(QtCore.Qt.DisplayRole, status_text)
                status_item.setData(QtCore.Qt.UserRole, sentiment)  # Store numeric value for sorting
            else:
                status_text = "Unanalyzed"
                status_item = QtWidgets.QTableWidgetItem()
                status_item.setText(status_text)
                status_item.setData(QtCore.Qt.DisplayRole, status_text)
                status_item.setData(QtCore.Qt.UserRole, -999)  # Unanalyzed sorts to bottom

            self.tabel_produk.setItem(row, 4, status_item)

            # Action (View Link) - make non-sortable
            action_item = QtWidgets.QTableWidgetItem("View")
            action_item.setData(QtCore.Qt.UserRole, 0)  # Neutral sort value
            # Keep default flags but note that sorting is handled by header click handler
            self.tabel_produk.setItem(row, 5, action_item)

        # Re-enable sorting after population - Qt will handle click events automatically
        self.tabel_produk.setSortingEnabled(True)

        # Ensure the table maintains its size and splitter proportions
        # Don't call resizeColumnsToContents() as it conflicts with stretch behavior
        # The columns are already set to stretch in _configure_table_behavior()

        # Ensure the splitter maintains proper proportions after data changes
        if hasattr(self, 'main_splitter'):
            # Maintain the splitter sizes to prevent shrinking
            current_sizes = self.main_splitter.sizes()
            if len(current_sizes) == 2 and sum(current_sizes) > 0:
                # Keep the proportional sizes but ensure they're reasonable
                total_size = sum(current_sizes)
                if current_sizes[1] < total_size * 0.5:  # If table section is less than 50%
                    # Reset to a good proportion
                    new_top = int(total_size * 0.3)
                    new_bottom = total_size - new_top
                    self.main_splitter.setSizes([new_top, new_bottom])

    def retranslateUi(self, MainWindow):
        """Set up UI text and translations"""
        _translate = QtCore.QCoreApplication.translate

        # Window title
        MainWindow.setWindowTitle(_translate("MainWindow", "ScrapQT - Product Scraping Tool"))

        # Search bar placeholder
        self.search_bar.setPlaceholderText(_translate("MainWindow", "Type to search queries (fuzzy search)..."))

        # Section titles
        self.gambar_produk_title.setText(_translate("MainWindow", "Product Image"))
        self.deskripsi_produk_title.setText(_translate("MainWindow", "Product Description"))
        self.grafik_perbandingan_title.setText(_translate("MainWindow", "Comparison Chart"))

        # Table headers
        headers = [
            "Product Name", "Platform", "Rating",
            "Amount", "Sentiment", "Action"
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
    import subprocess
    import os
    import atexit
    import time


    def start_servers():
        """Start the application servers"""
        print("Starting application servers...")
        try:
            # Get the project root directory
            project_root = os.path.dirname(os.path.abspath(__file__))
            run_servers_script = os.path.join(project_root, 'scripts', 'run_servers.py')

            # Use the virtual environment Python
            venv_python = os.path.join(project_root, '.venv', 'Scripts', 'python.exe')

            if os.path.exists(venv_python) and os.path.exists(run_servers_script):
                result = subprocess.run([venv_python, run_servers_script],
                                        cwd=project_root,
                                        capture_output=True,
                                        text=True)
                if result.returncode == 0:
                    print("Servers started successfully")
                    print(result.stdout)
                    time.sleep(2)  # Give servers time to fully start
                    return True
                else:
                    print(f"Failed to start servers: {result.stderr}")
                    return False
            else:
                print("Server scripts or virtual environment not found")
                print("Please run 'python scripts/install.py' first")
                return False
        except Exception as e:
            print(f"Error starting servers: {e}")
            return False


    def stop_servers():
        """Stop the application servers"""
        print("Stopping application servers...")
        try:
            # Get the project root directory
            project_root = os.path.dirname(os.path.abspath(__file__))
            stop_servers_script = os.path.join(project_root, 'scripts', 'stop_servers.py')

            # Use the virtual environment Python
            venv_python = os.path.join(project_root, '.venv', 'Scripts', 'python.exe')

            if os.path.exists(venv_python) and os.path.exists(stop_servers_script):
                result = subprocess.run([venv_python, stop_servers_script],
                                        cwd=project_root,
                                        capture_output=True,
                                        text=True)
                if result.returncode == 0:
                    print("Servers stopped successfully")
                    print(result.stdout)
                else:
                    print(f"Note: Stop servers result: {result.stderr}")
            else:
                print("Stop servers script not found")
        except Exception as e:
            print(f"Error stopping servers: {e}")


    # Register cleanup function to run on exit
    atexit.register(stop_servers)


    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print("\nReceived interrupt signal. Shutting down...")
        stop_servers()
        sys.exit(0)


    signal.signal(signal.SIGINT, signal_handler)

    # Start servers before launching UI
    servers_started = start_servers()
    if not servers_started:
        print("Warning: Servers may not have started properly.")
        print("You can try running 'python scripts/run_servers.py' manually.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting...")
            sys.exit(1)

    # Create application
    app = QtWidgets.QApplication(sys.argv)

    # Create main window
    MainWindow = QtWidgets.QMainWindow()

    # Enable window resizing and make it responsive
    MainWindow.setWindowFlags(QtCore.Qt.Window)

    # Set up UI
    ui = Ui_MainWindow()  # Now includes database initialization
    ui.setupUi(MainWindow)

    # Configure main window
    MainWindow.setCentralWidget(ui.centralwidget)

    # Show window and start application
    MainWindow.show()
    sys.exit(app.exec_())