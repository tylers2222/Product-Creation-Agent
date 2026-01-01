# Evelyn Faye Product Generation Agent

AI-powered product generation agent with Shopify integration, featuring a modern GUI for easy product creation.

## Features

- 🤖 **AI-Powered Product Generation** - Uses LangChain/LangGraph with GPT-4 for intelligent product creation
- 🛍️ **Shopify Integration** - Direct integration with Shopify API for product management
- 🖥️ **Modern GUI** - CustomTkinter-based interface with dark theme
- 🔐 **Daily Login System** - Password-protected access with device tracking
- 📊 **Vector Database** - Qdrant for semantic product search
- 🔍 **Web Scraping** - Firecrawl integration for product research
- 📝 **Structured Logging** - Clean, structured logs with Structlog

## Installation

### Prerequisites

- Python 3.10 or higher
- Redis server running locally or remotely
- OpenAI API key
- Shopify store with API credentials
- Qdrant vector database (local or cloud)

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "Product generating agent"
   ```

2. **Install dependencies**
   
   Using pip:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or using setup.py:
   ```bash
   pip install -e .
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   # OpenAI
   OPENAI_API_KEY=your_openai_api_key
   
   # Shopify
   SHOPIFY_ACCESS_TOKEN=your_shopify_access_token
   SHOPIFY_SHOP_NAME=your-shop-name
   SHOPIFY_API_VERSION=2024-01
   
   # Shopify Locations (get these from your Shopify admin)
   CITY_LOCATION_ID=your_city_location_id
   SOUTH_MELBOURNE_LOCATION_ID=your_south_melbourne_location_id
   
   # Qdrant Vector Database
   QDRANT_API_KEY=your_qdrant_api_key
   QDRANT_URL=https://your-qdrant-cluster.qdrant.io
   
   # Firecrawl (for web scraping)
   FIRECRAWL_API_KEY=your_firecrawl_api_key
   
   # Redis (optional, defaults to localhost:6379)
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

4. **Start Redis**
   ```bash
   redis-server
   ```

## Usage

### Running the API Server

```bash
python main.py
```

The API will be available at `http://localhost:3000`

### Running the GUI

```bash
python gui/main.py
```

**Default Password:** `999999` (change in `gui/main.py` line 32)

### GUI Features

1. **Daily Login** - Requires password authentication once per day per device
2. **Product Input** - Enter brand, product name, and variant details
3. **Variant Management** - Auto-generate variants based on options (Size, Flavor, etc.)
4. **Inventory Control** - Set inventory levels for City and South Melbourne locations
5. **Real-time Status** - Monitor request status with polling
6. **Success Popup** - Get direct link to created Shopify product

### API Endpoints

- `POST /internal/product_generation` - Create a new product
- `GET /internal/product_generation/{request_id}` - Get job status

## Project Structure

```
Product generating agent/
├── agents/                    # AI agent logic
│   ├── agent/                # Main agent workflow
│   └── infrastructure/       # External service integrations
│       ├── shopify_api/     # Shopify client
│       ├── firecrawl_api/   # Web scraping
│       └── vector_database/ # Qdrant client
├── api/                      # FastAPI application
│   ├── routers/             # API routes
│   ├── models/              # Pydantic models
│   └── internal/            # Task consumer
├── db/                       # Redis database client
├── gui/                      # CustomTkinter GUI
│   ├── main.py             # GUI application
│   └── images/             # GUI assets
├── config.py                 # Service container
├── logging_config.py         # Logging setup
├── main.py                   # API entry point
├── requirements.txt          # Python dependencies
└── setup.py                  # Package setup

```

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
black .
flake8 .
```

## Configuration

### GUI Configuration

Edit `gui/main.py`:
- Line 25: `API_BASE_URL` - Change to ngrok URL or production URL
- Line 32: `CORRECT_PASSWORD` - Change default password

### Logging

Logging is configured in `logging_config.py`:
- INFO level by default (no DEBUG logs)
- Third-party libraries set to WARNING
- Custom NoDebugBoundLogger for clean output

## Troubleshooting

### Redis Connection Error
Ensure Redis is running:
```bash
redis-cli ping
```

### GUI Not Starting
Check that CustomTkinter is installed:
```bash
pip install customtkinter
```

### API Import Errors
Ensure `logging_config` is imported first in `main.py`

## License

Proprietary - All rights reserved

## Authors

- Tyler Stewart - Initial work

## Acknowledgments

- OpenAI for GPT models
- LangChain/LangGraph for agent framework
- Shopify for e-commerce platform
- Qdrant for vector database

