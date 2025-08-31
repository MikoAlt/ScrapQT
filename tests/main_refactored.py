# -*- coding: utf-8 -*-

"""
Refactored ScrapQT Main Window UI
This is a cleaned up and organized version of the main UI components
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        """Set up the main window UI components"""
        self._setup_main_window(MainWindow)
        self._setup_main_layout()
        self._setup_sidebars()
        self._setup_content_area()
        self._setup_connections()
        self.retranslateUi(MainWindow)

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

    def _setup_sidebars(self):
        """Set up both extended and collapsed sidebars"""
        self._setup_extended_sidebar()
        self._setup_short_sidebar()

    def _setup_extended_sidebar(self):
        """Set up the expanded sidebar with navigation buttons"""
        # Create extended sidebar container
        self.extended_sidebar = QtWidgets.QWidget(self.Window)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, 
            QtWidgets.QSizePolicy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.extended_sidebar.sizePolicy().hasHeightForWidth())
        self.extended_sidebar.setSizePolicy(sizePolicy)
        self.extended_sidebar.setMaximumWidth(150)
        self.extended_sidebar.setStyleSheet("background-color: rgb(0, 89, 255);")
        self.extended_sidebar.setObjectName("extended_sidebar")

        # Set up layout for extended sidebar
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.extended_sidebar)
        self.verticalLayout_4.setObjectName("verticalLayout_4")

        # Add logo section
        self._add_extended_sidebar_logo()
        
        # Add navigation buttons
        self._add_extended_sidebar_buttons()
        
        # Add exit button at bottom
        self._add_extended_sidebar_exit_button()
        
        # Add to main grid
        self.gridLayout.addWidget(self.extended_sidebar, 0, 1, 1, 1)

    def _add_extended_sidebar_logo(self):
        """Add logo to extended sidebar"""
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        
        self.scrrap_logo_extend = QtWidgets.QLabel(self.extended_sidebar)
        self.scrrap_logo_extend.setMinimumSize(QtCore.QSize(40, 40))
        self.scrrap_logo_extend.setMaximumSize(QtCore.QSize(40, 40))
        self.scrrap_logo_extend.setStyleSheet("image: url(:/resource/SQ_Logo.png);")
        self.scrrap_logo_extend.setText("")
        self.scrrap_logo_extend.setObjectName("scrrap_logo_extend")
        
        self.horizontalLayout_3.addWidget(self.scrrap_logo_extend)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)

    def _add_extended_sidebar_buttons(self):
        """Add navigation buttons to extended sidebar"""
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")

        # Home button
        self.home_button_extend = self._create_sidebar_button(
            name="home_button_extend",
            icon_path=":/resource/Home.png",
            text_color="rgb(255, 255, 255)",
            min_size=(0, 40)
        )
        self.verticalLayout_3.addWidget(self.home_button_extend)

        # Profile button
        self.profile_button_extend = self._create_sidebar_button(
            name="profile_button_extend",
            icon_path=":/resource/Profile.png",
            text_color="rgb(255, 255, 255)",
            min_size=(0, 40)
        )
        self.verticalLayout_3.addWidget(self.profile_button_extend)

        # Statistics button
        self.stat_button_extend = self._create_sidebar_button(
            name="stat_button_extend",
            icon_path=":/resource/Stats.png",
            text_color="rgb(255, 255, 255)",
            min_size=(0, 40)
        )
        self.verticalLayout_3.addWidget(self.stat_button_extend)

        # Add vertical spacer
        spacerItem = QtWidgets.QSpacerItem(
            20, 40, 
            QtWidgets.QSizePolicy.Minimum, 
            QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout_3.addItem(spacerItem)
        
        self.verticalLayout_4.addLayout(self.verticalLayout_3)

    def _add_extended_sidebar_exit_button(self):
        """Add exit button to extended sidebar"""
        self.exit_button_extend = self._create_sidebar_button(
            name="exit_button_extend",
            icon_path=":/resource/Close.png",
            text_color="rgb(255, 255, 255)",
            min_size=(0, 40)
        )
        self.verticalLayout_4.addWidget(self.exit_button_extend)

    def _setup_short_sidebar(self):
        """Set up the collapsed sidebar with icon-only buttons"""
        # Create short sidebar container
        self.short_sidebar = QtWidgets.QWidget(self.Window)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, 
            QtWidgets.QSizePolicy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.short_sidebar.sizePolicy().hasHeightForWidth())
        self.short_sidebar.setSizePolicy(sizePolicy)
        self.short_sidebar.setMaximumWidth(60)
        self.short_sidebar.setStyleSheet("background-color: rgb(0, 89, 255);")
        self.short_sidebar.setObjectName("short_sidebar")

        # Set up layout
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.short_sidebar)
        self.verticalLayout_2.setObjectName("verticalLayout_2")

        # Add logo
        self._add_short_sidebar_logo()
        
        # Add navigation buttons
        self._add_short_sidebar_buttons()
        
        # Add exit button
        self._add_short_sidebar_exit_button()
        
        # Add to main grid
        self.gridLayout.addWidget(self.short_sidebar, 0, 0, 1, 1)

    def _add_short_sidebar_logo(self):
        """Add logo to short sidebar"""
        self.scrap_logo = QtWidgets.QLabel(self.short_sidebar)
        self.scrap_logo.setMinimumSize(QtCore.QSize(40, 40))
        self.scrap_logo.setMaximumSize(QtCore.QSize(40, 40))
        self.scrap_logo.setStyleSheet("image: url(:/resource/SQ_Logo.png);")
        self.scrap_logo.setText("")
        self.scrap_logo.setObjectName("scrap_logo")
        self.verticalLayout_2.addWidget(self.scrap_logo)

    def _add_short_sidebar_buttons(self):
        """Add navigation buttons to short sidebar"""
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")

        # Home button (icon only)
        self.home_button = self._create_icon_button(
            name="home_button",
            icon_path=":/resource/Home.png",
            size=(40, 40)
        )
        self.verticalLayout.addWidget(self.home_button)

        # Profile button (icon only)
        self.profile_button = self._create_icon_button(
            name="profile_button",
            icon_path=":/resource/Profile.png",
            size=(40, 40)
        )
        self.verticalLayout.addWidget(self.profile_button)

        # Statistics button (icon only)
        self.stat_button = self._create_icon_button(
            name="stat_button",
            icon_path=":/resource/Stats.png",
            size=(40, 40)
        )
        self.verticalLayout.addWidget(self.stat_button)

        self.verticalLayout_2.addLayout(self.verticalLayout)

        # Add vertical spacer
        spacerItem1 = QtWidgets.QSpacerItem(
            20, 40, 
            QtWidgets.QSizePolicy.Minimum, 
            QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout_2.addItem(spacerItem1)

    def _add_short_sidebar_exit_button(self):
        """Add exit button to short sidebar"""
        self.exit_button = self._create_icon_button(
            name="exit_button",
            icon_path=":/resource/Close.png",
            size=(40, 40)
        )
        self.verticalLayout_2.addWidget(self.exit_button)

    def _create_sidebar_button(self, name, icon_path, text_color, min_size):
        """Helper method to create sidebar buttons with text"""
        button = QtWidgets.QPushButton()
        button.setObjectName(name)
        button.setEnabled(True)
        button.setMinimumSize(QtCore.QSize(min_size[0], min_size[1]))
        button.setLayoutDirection(QtCore.Qt.LeftToRight)
        button.setStyleSheet(f"color: {text_color};")
        
        # Set up icon
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        button.setIcon(icon)
        button.setIconSize(QtCore.QSize(25, 25))
        
        # Set button properties
        button.setCheckable(True)
        button.setAutoExclusive(True)
        
        return button

    def _create_icon_button(self, name, icon_path, size):
        """Helper method to create icon-only buttons"""
        button = QtWidgets.QPushButton()
        button.setObjectName(name)
        button.setEnabled(True)
        button.setMinimumSize(QtCore.QSize(size[0], size[1]))
        button.setMaximumSize(QtCore.QSize(size[0], size[1]))
        button.setLayoutDirection(QtCore.Qt.LeftToRight)
        button.setText("")
        
        # Set up icon
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        button.setIcon(icon)
        button.setIconSize(QtCore.QSize(25, 25))
        
        # Set button properties
        button.setCheckable(True)
        button.setAutoExclusive(True)
        
        return button

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

        # Add to main grid
        self.gridLayout.addWidget(self.content, 0, 2, 1, 1)

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
        self._add_menu_button()
        self._add_home_logo()
        self._add_search_section()

        self.gridLayout_4.addWidget(self.head_content, 0, 0, 1, 1)

    def _add_menu_button(self):
        """Add the hamburger menu button"""
        self.menu_button = QtWidgets.QPushButton(self.head_content)
        self.menu_button.setStyleSheet("border: none;")
        self.menu_button.setText("")
        
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/resource/Menu Icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.menu_button.setIcon(icon4)
        self.menu_button.setIconSize(QtCore.QSize(25, 25))
        self.menu_button.setCheckable(True)
        self.menu_button.setChecked(True)
        self.menu_button.setAutoExclusive(False)
        self.menu_button.setObjectName("menu_button")
        
        self.horizontalLayout_2.addWidget(self.menu_button)

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
        self.tabel_produk = QtWidgets.QTableWidget(self.main_content_widget)
        
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
        # Connect menu button to sidebar visibility toggle
        self.menu_button.toggled['bool'].connect(self.short_sidebar.setHidden)
        self.menu_button.toggled['bool'].connect(self.extended_sidebar.setVisible)

    def retranslateUi(self, MainWindow):
        """Set up UI text and translations"""
        _translate = QtCore.QCoreApplication.translate
        
        # Window title
        MainWindow.setWindowTitle(_translate("MainWindow", "ScrapQT - Product Scraping Tool"))
        
        # Extended sidebar button texts
        self.home_button_extend.setText(_translate("MainWindow", "Home"))
        self.profile_button_extend.setText(_translate("MainWindow", "Profile"))
        self.stat_button_extend.setText(_translate("MainWindow", "Statistic"))
        self.exit_button_extend.setText(_translate("MainWindow", "Exit"))
        
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
    
    # Create main window
    MainWindow = QtWidgets.QMainWindow()
    
    # Enable window resizing and make it responsive
    MainWindow.setWindowFlags(QtCore.Qt.Window)
    
    # Set up UI
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    
    # Configure main window
    MainWindow.setCentralWidget(ui.centralwidget)
    
    # Make table columns resize proportionally when window is resized
    ui.tabel_produk.resizeColumnsToContents()
    
    # Show window and start application
    MainWindow.show()
    sys.exit(app.exec_())
