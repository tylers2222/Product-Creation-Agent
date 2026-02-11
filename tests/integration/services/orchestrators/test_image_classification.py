import structlog
import glob
import pytest
from product_agent.services.orchestrators.images import classify_image_svc

logger = structlog.getLogger(__name__)

@pytest.mark.integration
class TestImageClassification:
    """
    Testing the image classification service
    """
    @pytest.mark.asyncio
    async def test_image_classification_correct(
        self,
        real_service_container
    ):
        """
        A correct image for the query is given
        See if the model can classify it
        """
        images = glob.glob("tests/integration/infrastructure/images/*")
        logger.debug("Got images from test folder", images=images)

        query = "Dr Bronner's 18-in-1 Pure Castile Magic Soap Baby Unscented 946 ml"

        ready_data = {}
        for idx, image_path in enumerate(images):
            image_name = image_path.split("/")[-1]
            logger.debug("Found image with name %s", image_name)
            with open(image_path, "rb") as image_bytes:
                image_bytes_read = image_bytes.read()
                assert isinstance(image_bytes_read, bytes)
                mock_url = f"www.{image_name}.com.au"

                ready_data[mock_url] = image_bytes_read

        llm_response = await classify_image_svc(
            query=query,
            images_bytes_data=ready_data,
            llm=real_service_container.llm["gemini"],
            model="gemini-3-pro-preview"
        )

        assert llm_response is not None
        print("Type: ", type(llm_response))
        print(llm_response)
