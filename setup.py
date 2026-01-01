from setuptools import setup, find_packages

setup(
    name="evelyn-faye-product-agent",
    version="1.0.0",
    description="AI-powered product generation agent with Shopify integration",
    author="Tyler Stewart",
    author_email="tyler@example.com",
    packages=find_packages(),
    python_requires=">=3.10",
    
    # Core dependencies
    install_requires=[
        # GUI
        "customtkinter>=5.2.0",
        "Pillow>=10.0.0",
        
        # Web Framework & API
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "requests>=2.31.0",
        "python-multipart>=0.0.6",
        
        # Logging
        "structlog>=23.2.0",
        
        # Data Validation & Models
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        
        # Database
        "redis>=5.0.0",
        
        # AI & LangChain
        "langgraph>=0.0.40",
        "langchain-core>=0.1.0",
        "langchain-openai>=0.0.5",
        "langchain-community>=0.0.20",
        
        # Vector Database
        "qdrant-client>=1.7.0",
        
        # OpenAI
        "openai>=1.6.0",
        
        # Environment & Config
        "python-dotenv>=1.0.0",
        
        # Utilities
        "numpy>=1.24.0",
    ],
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.7.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "httpx>=0.25.0",
        ],
    },
    
    # Entry points for command-line scripts
    entry_points={
        "console_scripts": [
            "evelyn-faye-api=main:main",
            "evelyn-faye-gui=gui.main:main",
        ],
    },
    
    # Package data
    package_data={
        "gui": ["images/*.png", "*.json"],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    
    # Additional metadata
    keywords="ai agent shopify product-generation langchain",
    project_urls={
        "Source": "https://github.com/yourusername/evelyn-faye-product-agent",
        "Bug Reports": "https://github.com/yourusername/evelyn-faye-product-agent/issues",
    },
)

