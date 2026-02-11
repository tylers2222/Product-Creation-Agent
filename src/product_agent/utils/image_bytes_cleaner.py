import structlog

logger = structlog.getLogger(__name__)

def clean_image_bytes(image_data: list | dict):
    if isinstance(image_data, list):
        list_result = []
        for img_bytes in image_data:
            if len(img_bytes) < 500:
                logger.debug("Skipped image bad bytes", bytes_decoded=img_bytes.decode("utf-8"))
                continue

            list_result.append(img_bytes)

        return list_result

    if isinstance(image_data, dict):
        dict_result = {}
        for url, img_bytes in image_data.items():
            if len(img_bytes) < 500:
                logger.debug("Skipped image bad bytes", bytes_decoded=img_bytes.decode("utf-8"))
                continue

            dict_result[url] = img_bytes

        return dict_result