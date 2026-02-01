class NoScraperResult(Exception):
    """Exception when all the urls in a scrape return no results"""
    def __init__(self, search_query: str):
        message = f"Markdown scraper return no usable results for the query {search_query}"
        super().__init__(message)
        