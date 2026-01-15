"""
Configuration module - Re-exports from factory for backwards compatibility.

DEPRECATED: Import directly from factory/ instead.

Example:
    # Old (deprecated)
    from config import create_service_container, ServiceContainer

    # New (preferred)
    from factory import build_service_container, ServiceContainer
"""
from factory.container import (
    ServiceContainer,
    build_service_container,
    build_mock_service_container,
)

# Backwards compatibility aliases
create_service_container = build_service_container
create_mock_service_container = build_mock_service_container

__all__ = [
    "ServiceContainer",
    "create_service_container",
    "create_mock_service_container",
    # New names
    "build_service_container",
    "build_mock_service_container",
]
