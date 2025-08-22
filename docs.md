# ScrapQT Documentation

## Overview
ScrapQT is a robust and maintainable application designed for web scraping, leveraging gRPC services for inter-service communication, a database for data storage, and an LLM for sentiment analysis. It comprises Database, LLM, and Scraper servers that work in conjunction to provide a comprehensive scraping and analysis solution.

## Features
- **Background Server Operation:** Managed by `run_servers.py` and `stop_servers.py` for efficient process handling.
- **Database-Centric Query Linking:** `add_linked_queries.py` initializes database queries and establishes relationships between them.
- **gRPC Services:** Utilizes gRPC for high-performance communication between the Database, LLM, and Scraper services.
- **Web Scraping:** Orchestrated by `plugin_loader.py`, allowing for extensible scraping capabilities.
- **Sentiment Analysis:** Integrates with an LLM (Gemini) to perform sentiment analysis on scraped data and database entries.
- **Configurable API Keys:** API keys are securely stored in a `.env` file and loaded dynamically.
- **Portable Design:** Hardcoded paths have been replaced with dynamic `os.path.join` constructs for enhanced portability across different operating systems.

## Setup and Installation

To set up the ScrapQT application from a fresh clone, follow these steps:

1.  **Navigate to the project's root directory:**
    Open your terminal or command prompt and navigate to the root directory of the `ScrapQT` project.

2.  **Create and activate a virtual environment, install dependencies, and compile protobufs:**
    ```bash
    python install.py
    ```
    This script will:
    *   Create a Python virtual environment (`.venv`).
    *   Install all necessary Python packages listed in `requirements.txt`.
    *   Compile the gRPC protobuf files into the `src/scrapqt` package.
    *   Fix any internal import issues within the generated protobuf files.

3.  **Activate the Virtual Environment:**
    Before running any Python scripts, activate the virtual environment.

    *   **On Windows:**
        ```bash
        .venv\\Scripts\\activate
        ```
    *   **On macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

4.  **Configure API Keys:**
    Create a `.env` file in the project root directory and add your Gemini API key:
    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
    ```
    Replace `"YOUR_GEMINI_API_KEY_HERE"` with your actual Gemini API key.

## Running the Application

**Note:** Before running any of the commands below, ensure your virtual environment is activated as described in the [Setup and Installation](#setup-and-installation) section.

### Starting Servers
The application relies on three main servers: Database, LLM, and Scraper. To start them in the background:

```bash
python run_servers.py
```

### Stopping Servers
To stop all running servers:

```bash
python stop_servers.py
```

## Usage Examples

**Note:** Ensure the servers are running and your virtual environment is activated before executing the following commands.

### 1. Populate Initial Queries and Links
This script adds predefined queries and links them in the database.
```bash
python add_linked_queries.py
```

### 2. Initiate a Scraping Task
This script triggers the scraper service to scrape data for a specified query (defaults to "gaming keyboard").
```bash
python run_scraper_client.py "your desired query"
```
Example:
```bash
python run_scraper_client.py "gaming mouse"
```

### 3. Check Database Content
View the current content of the `products`, `queries`, and `query_links` tables in the database.
```bash
python check_db.py
```

### 4. Perform Sentiment Analysis
This script demonstrates both analyzing the sentiment of individual text inputs and analyzing/updating the sentiment scores of items stored in the database.
```bash
python run_sentiment_client.py
```

## Project Structure (Key Files)
- `.env`: Environment variables (e.g., API keys).
- `install.py`: Sets up the virtual environment, installs dependencies, and compiles protobufs.
- `run_servers.py`: Starts the Database, LLM, and Scraper gRPC servers.
- `stop_servers.py`: Stops all running servers.
- `add_linked_queries.py`: Populates the database with initial queries and links.
- `check_db.py`: Utility to inspect the database content.
- `fix_proto_imports.py`: Script to correct protobuf import paths.
- `plugins/`: Directory for scraper plugins (e.g., `example_scraper.py`).
- `src/database/server.py`: Implements the Database gRPC service.
- `src/llm/server.py`: Implements the LLM (Sentiment Analysis) gRPC service.
- `src/scraper/server.py`: Implements the Scraper gRPC service.
- `src/scraper/plugin_loader.py`: Orchestrates loading and running scraper plugins.
- `src/protos/services.proto`: Protobuf definition file for gRPC services.
- `src/scrapqt/`: Python package for generated protobuf files (`services_pb2.py`, `services_pb2_grpc.py`).
- `run_scraper_client.py`: Example client to interact with the Scraper service.
- `run_sentiment_client.py`: Example client to interact with the Sentiment Analysis service.
