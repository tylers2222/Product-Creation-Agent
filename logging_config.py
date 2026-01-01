import structlog
import logging

# Configure standard logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    force=True
)

# Silence noisy third-party libraries
for lib in ["httpcore", "httpx", "openai", "urllib3", "firecrawl", "qdrant_client", "shopify"]:
    logging.getLogger(lib).setLevel(logging.WARNING)

# Custom BoundLogger that completely ignores debug calls
class NoDebugBoundLogger(structlog.stdlib.BoundLogger):
    """BoundLogger that doesn't process debug logs at all"""
    
    def debug(self, event=None, *args, **kw):
        """Completely ignore debug - don't even process it"""
        pass  # Do nothing - don't call parent, don't process

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=NoDebugBoundLogger,  # Use our custom wrapper that ignores debug
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=False,
)