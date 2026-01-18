"""
Factory package - Composition root for dependency injection.

This package is the ONLY place where concrete implementations are assembled.
All other packages import from here to get fully-constructed dependencies.

Usage:
    from product_agent.config import build_service_container, build_synthesis_agent

    container = build_service_container()
    agent = build_synthesis_agent(container)
"""
from .container import ServiceContainer, build_service_container, build_mock_service_container
from .agents import build_synthesis_agent

__all__ = [
    "ServiceContainer",
    "build_service_container",
    "build_mock_service_container",
    "build_synthesis_agent",
]
