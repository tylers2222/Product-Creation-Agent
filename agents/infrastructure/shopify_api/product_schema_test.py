import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.infrastructure.shopify_api.product_schema import Fields

def test_field_setting():
    f = Fields(
        id=True,
        title=True,
        product_type=True,
        tags=True
    )

    fields_string = f.shopify_transform_fields()
    print("Fields: ", fields_string)
    # cant assert properly, it gets looped through in random order
    assert fields_string == "id, title, product_type, tags"

if __name__ == "__main__":
    test_field_setting()