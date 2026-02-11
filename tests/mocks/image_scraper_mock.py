class MockImageScraper:
    def __init__(self):
        pass

    async def get_google_images(
        self,
        query: str, 
        num_images: int = 5,
        headless: bool = True
    ):
        """Mock getting google images"""
        result = []
        for i in range(num_images):
            result.append(
                f"www.{i+1}.com.au"
            )

        return result