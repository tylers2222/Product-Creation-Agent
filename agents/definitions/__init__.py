"""
Agent Definitions - Pure configuration for agents.

This package contains agent configurations (prompts, models, tool lists)
WITHOUT any runtime dependencies. Actual agent construction happens in factory/.
"""
from .synthesis import SYNTHESIS_CONFIG

__all__ = ["SYNTHESIS_CONFIG"]
