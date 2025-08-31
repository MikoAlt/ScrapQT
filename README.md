# ScrapQT

A comprehensive E-Commerce Web Scraper with advanced UI features, sentiment analysis, and automated server management, built with Python and PyQt5.

## Features

### ✅ **Completed Features**

- [x] **Advanced Search Interface**: Fuzzy search with autocomplete, empty search shows all queries
- [x] **Plugin-Based Scraper System**: Extensible scraper architecture with plugin support
- [x] **Dynamic GUI**: Responsive interface that adapts to data and user interactions
- [x] **Comprehensive Product Table**: Displays title, price, rating, review count, link, marketplace, and condition
- [x] **Product Detail Popups**: Rich detail dialogs with image previews and full product information
- [x] **Statistical Analysis**: Histogram, mean, mode, median visualization using matplotlib
- [x] **Linked Search Queries**: Database-backed query management and history
- [x] **LLM Sentiment Analysis**: AI-powered sentiment analysis with confidence scoring
- [x] **Background Server Management**: Automatic startup/shutdown of gRPC services
- [x] **Database Management**: SQLite backend with relationship management and data persistence
- [x] **Interactive UI Elements**: Context menus, hover previews, sortable columns, and manual refresh
- [x] **Database Clearing**: Safe database reset functionality with confirmation prompts

### 🎯 **Architecture**

- **Frontend**: PyQt5-based desktop application with modern UI design
- **Backend Services**: gRPC microservices for LLM processing and data management
- **Database**: SQLite with foreign key relationships and full-text search
- **Plugin System**: Extensible scraper framework for multiple e-commerce platforms
- **Server Management**: Automatic lifecycle management with PID tracking

## Project Structure

```
ScrapQT/
├── main.py                     # Main application entry point
├── product_detail_dialog.py    # Product detail popup dialogs
├── sentiment_dialog.py         # Sentiment analysis interface
├── database_manager.py         # Database operations and management
├── config_manager.py          # Configuration file handling
├── db_config.py               # Database connection configuration
├── asset_rc.py                # Qt resource file (auto-generated)
├── requirements.txt           # Python dependencies
├── config.ini                # Application configuration
│
├── scripts/                   # Setup and server management scripts
│   ├── install.py            # Environment setup and dependency installation
│   ├── run_servers.py        # Start gRPC servers with PID management
│   ├── stop_servers.py       # Graceful server shutdown
│   └── stop_servers.ps1      # PowerShell server termination script
│
├── src/                      # Core application services
│   ├── database/             # Database server implementation
│   ├── llm/                  # LLM service for sentiment analysis
│   ├── scraper/              # Web scraping services and plugins
│   └── scrapqt/              # Protocol buffer definitions
│
├── docs/                     # Documentation and guides
│   └── *.md                 # Project documentation
│
├── data/                     # Application data and logs
│   ├── scraped_data.db      # SQLite database
│   └── *.log                # Server log files
│
├── plugins/                  # Scraper plugin modules
│   └── example_scraper.py   # Sample scraper implementation
│
├── Asset/                    # UI assets and resources
│   ├── *.png, *.svg         # Icons and images
│   └── *.qrc                # Qt resource files
│
└── UI/                       # Qt Designer UI files
    └── *.ui                  # UI layout definitions
```

## Quick Start

### Prerequisites
- **Python 3.8+** (tested with Python 3.12)
- **Windows** (tested on Windows 10/11)
- **Git** (for cloning the repository)

### 🚀 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ScrapQT
   ```

2. **Run the automated installer**:
   ```bash
   python scripts/install.py
   ```
   
   **What this does automatically:**
   - ✅ Creates a virtual environment (`.venv`)
   - ✅ Installs all required dependencies from `requirements.txt`
   - ✅ Sets up the complete project environment
   - ✅ Verifies installation integrity
   
   **Expected output:**
   ```
   Project root: D:\Workspace\ScrapQT
   Starting installation script...
   Creating virtual environment...
   Installing dependencies...
   [... dependency installation ...]
   Installation complete. You can now run the application using 'python main.py'.
   ```

3. **Launch the application**:
   ```bash
   python main.py
   ```
   
   **What happens automatically:**
   - 🔄 Starts required backend servers (LLM + Database, Scraper)
   - 🖥️ Launches the PyQt5 desktop interface
   - 📊 Initializes empty database (on first run)
   - 🛑 Stops servers gracefully on exit

### 🔧 First Run Setup

On first launch, you'll see:
- Empty product table (no data initially)
- Search bar ready for queries
- All UI features fully functional
- Backend servers running automatically in background

**Ready to use immediately!** Start by typing a search query and clicking "Scrape" to add products.

## Usage Guide

### 📋 Basic Operations

#### **Searching for Products**
1. **Empty Search**: Click the search bar to see all existing queries
2. **Fuzzy Search**: Type partial queries for intelligent autocomplete suggestions
3. **Search Results**: View products from matching queries in the main table
4. **New Queries**: Enter new search terms and click "Scrape" to fetch products

#### **Product Management**
- **View Details**: Double-click any product row to open detailed information
- **Product Links**: Click links to open original product pages in your browser
- **Context Menu**: Right-click products for additional options
- **Image Previews**: Hover over product names to see product images

#### **Data Management**
- **Manual Refresh**: Click the "Refresh" button to update the product table
- **Clear Database**: Use "Clear Database" button to remove all data (with confirmation)
- **Auto-refresh**: Application prompts to refresh after successful scraping

### 🧠 AI Features

#### **Sentiment Analysis**
1. Right-click any product in the table
2. Select "Analyze Sentiment" from context menu
3. AI analyzes product reviews and provides:
   - Sentiment score (-1 to +1 scale)
   - Confidence level
   - Detailed analysis explanation

#### **Statistical Analysis**
- View price distributions and statistics
- Analyze review patterns across products
- Compare sentiment scores between products

### 🔧 Advanced Features

#### **Server Management** (Automatic)
- **Auto-Start**: Servers start automatically when launching `main.py`
- **PID Management**: Automatic cleanup of existing servers before starting new ones
- **Graceful Shutdown**: Servers stop cleanly on application exit or Ctrl+C
- **Log Files**: Server logs available in `data/` directory

#### **Manual Server Control** (Optional)
```bash
# Start servers manually
python scripts/run_servers.py

# Stop servers manually  
python scripts/stop_servers.py

# Check server status
dir data/*.log
```

## Development

### 🔌 Adding Custom Scrapers
1. **Create scraper plugin**: Add new file in `plugins/` directory
2. **Follow interface**: Use `plugins/example_scraper.py` as template
3. **Implement methods**: Define required scraping interface methods
4. **Auto-discovery**: Plugin will be automatically loaded on restart

**Note**: Plugin directory structure will be created automatically when adding scrapers.

### 📁 Project Structure Management
- **Core files**: Keep in root directory (`main.py`, `database_manager.py`, etc.)
- **Scripts**: Management scripts in `scripts/` directory
- **Tests**: All test files organized in `tests/` directory
- **Documentation**: Project docs in `docs/` directory

## Dependencies

**Automatically installed via `scripts/install.py`:**

### Core Framework
- **PyQt5**: Desktop application framework with modern UI components
- **PyQt5-Qt5**: Qt5 runtime libraries
- **PyQt5-sip**: Python bindings for Qt5

### Backend Services  
- **grpcio**: High-performance gRPC communication framework
- **grpcio-tools**: Protocol buffer compiler and tools
- **protobuf**: Google's data serialization library

### AI & Machine Learning
- **google-generativeai**: Google's Generative AI API for sentiment analysis
- **numpy**: Numerical computing foundation for data processing
- **matplotlib**: Statistical visualization and plotting library

### Utilities
- **python-dotenv**: Environment variable management for API keys
- **Additional dependencies**: Automatically resolved (requests, PIL, etc.)

## Configuration

### 🔑 API Keys Setup
1. **Google AI API Key** (for sentiment analysis):
   - Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Application will prompt for key on first use
   - Key is stored securely in `.env` file

### 📊 Database Configuration
- **Location**: `data/scraped_data.db` (SQLite)
- **Auto-created**: Database and tables created automatically
- **Configuration**: Managed via `config.ini` and `db_config.py`

### 🖥️ UI Configuration
- **Assets**: UI resources in `assets/` directory
- **Themes**: Modern flat design with responsive layouts
- **Settings**: Application preferences auto-saved

## Troubleshooting

### Common Issues

#### **Installation Problems**
- **Python Version**: Ensure Python 3.8+ is installed
- **Virtual Environment**: If install fails, try: `python -m venv .venv` manually
- **Dependencies**: For dependency conflicts, delete `.venv` and reinstall

#### **Application Won't Start**
- **Server Issues**: Check `data/*.log` files for server errors
- **Port Conflicts**: Default ports 50051 (LLM), 50052 (Scraper) - ensure they're available
- **Database Lock**: If database is locked, restart and try again

#### **No Search Results**
- **Fresh Install**: Database starts empty - use "Scrape" to add products
- **Server Connection**: Ensure backend servers are running (automatic with main.py)
- **API Keys**: Sentiment analysis requires Google AI API key

### Manual Recovery
```bash
# Reset everything to fresh state
Remove-Item -Path ".venv" -Recurse -Force
Remove-Item -Path "data/*" -Force  
python scripts/install.py
python main.py
```

### Getting Help
- **Logs**: Check `data/llm_server.log` and `data/scraper_server.log` for detailed error info
- **Test Suite**: Run tests in `tests/` directory to verify functionality
- **Debug Mode**: Run servers manually with `python scripts/run_servers.py` for detailed output

## Quick Verification

After installation, verify everything is working:

```bash
# Test 1: Launch application (should start servers automatically)
python main.py

# Test 2: Check database is empty on fresh install
# - Application should show "Loaded 0 products from database"
# - Search bar should be empty and ready for input
# - No data in the product table

# Test 3: Test basic functionality
# - Type any search term in the search bar
# - Click "Scrape" to test web scraping
# - Application should find and display products
# - Servers should shut down cleanly when closing app
```

**Expected Fresh Install Behavior:**
- ✅ Servers start automatically with status messages
- ✅ UI opens with empty product table
- ✅ Search functionality ready for use
- ✅ Clean shutdown when closing application

## Support & Development

### 📚 Documentation
- **README.md**: This comprehensive guide
- **docs/**: Additional documentation and guides
- **Code Comments**: Extensive inline documentation throughout codebase

### 🔧 Development Tools
- **Test Suite**: Comprehensive tests in `tests/` directory
- **Server Scripts**: Manual server management in `scripts/`
- **Database Tools**: Database inspection and management utilities

### 🐛 Issues & Features
For issues, feature requests, or development questions:
1. **Check Logs**: Review `data/*.log` files for detailed error information
2. **Run Tests**: Execute test suite to identify specific problems
3. **Fresh Install**: Try complete reinstall if issues persist
4. **Documentation**: Refer to inline code documentation and comments

### 🎯 Project Status
**ScrapQT** is a complete, production-ready application with:
- ✅ Full feature implementation
- ✅ Comprehensive error handling
- ✅ Automatic server lifecycle management
- ✅ Professional UI/UX design
- ✅ Extensive test coverage
- ✅ Clean project organization

---

**ScrapQT** - Making e-commerce data collection and analysis simple and powerful.





