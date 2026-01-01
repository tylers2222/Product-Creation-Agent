from setuptools import setup, find_packages
import os

# Read the README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="evelyn-faye-gui",
    version="1.0.0",
    description="GUI client for Evelyn Faye Product Generation Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tyler Stewart",
    author_email="tyler@example.com",
    
    # Single package - just the GUI
    py_modules=["main"],
    
    python_requires=">=3.10",
    
    # Minimal dependencies for GUI only
    install_requires=[
        "customtkinter>=5.2.0",
        "Pillow>=10.0.0",
        "requests>=2.31.0",
        "pydantic>=2.5.0",
    ],
    
    # Package data - include images
    package_data={
        "": ["images/*.png", "*.json"],
    },
    include_package_data=True,
    
    # Entry point for running the GUI
    entry_points={
        "console_scripts": [
            "evelyn-faye-gui=main:main",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Desktop Environment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    
    keywords="gui desktop shopify product-management",
)

