import random
import traceback
from dotenv import load_dotenv
import os
import sys
from dotenv import load_dotenv

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

os.chdir("..")
load_dotenv()

from shopify_api.client import ShopifyClient, DraftProduct, Variant, Shop
from shopify_api.product_schema import DraftResponse
from shopify_api.exceptions import ShopifyError
import os
import inspect
import sys
import datetime
import unittest

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

load_dotenv()

dummy_variant = Variant(
    option1_value="500g",
    sku=235053,
    barcode=9233952523,
    price=29.99,
    compare_at=39.99,
    product_weight=0.5
)

dummy_draft_product = DraftProduct(
    title="Test Product Title",
    description="This is a test product description for dummy data",
    inventory=[10, 20],
    type="Supplement",
    vendor="Test Vendor",
    tags=["test", "dummy", "sample"],
    lead_option="Size",
    variants=[dummy_variant]
)

# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------

class DraftProductWith1Option:
    def __init__(self):
        pass

    def load_products_in(self) -> DraftProduct:
        dummy_variant_real = Variant(
            option1_value="2kg",
            sku=561596,
            barcode=9238957523,
            price=64.95,
            compare_at=79.95,
            product_weight=1.0
        )

        dummy_variant_real_2 = Variant(
            option1_value="1kg",
            sku=561597,
            barcode=9233952523,
            price=119.95,
            compare_at=149.95,
            product_weight=2.0
        )

        return DraftProduct(
            title="Gold Standard 100% Whey Protein - Double Rich Chocolate",
            description="""<h2>The World's Best-Selling Whey Protein</h2>
            
        <p>Optimum Nutrition Gold Standard 100% Whey is the gold standard in protein powder. With 24g of high-quality whey protein per serving, it's perfect for muscle recovery and growth after intense training sessions.</p>

        <h3>Key Features:</h3>
        <ul>
            <li>24g of premium whey protein isolates and concentrates</li>
            <li>5.5g of naturally occurring BCAAs per serving</li>
            <li>4g of naturally occurring glutamine and glutamic acid</li>
            <li>Instantized for easy mixing with just a spoon</li>
            <li>Gluten-free formula</li>
        </ul>

        <h3>Suggested Use:</h3>
        <p>Mix one rounded scoop with 180-240ml of cold water, milk, or your favorite beverage. Consume 30-60 minutes after training or between meals to meet your daily protein requirements.</p>

        <p><strong>Allergen Warning:</strong> Contains milk and soy ingredients. Manufactured in a facility that also processes egg, wheat, peanuts, and tree nuts.</p>""",
            inventory=[45, 28],
            type="Sports Nutrition",
            vendor="Optimum Nutrition",
            tags=[
                "protein powder",
                "whey protein", 
                "post-workout",
                "muscle recovery",
                "chocolate",
                "gold standard",
                "optimum nutrition",
                "fitness supplements",
                "bodybuilding",
                "protein shake"
            ],
            lead_option="Size",
            variants=[dummy_variant_real, dummy_variant_real_2]
        )

class DraftProductWith2Options:
    def __init__(self):
        pass

    def load_products_in(self) -> DraftProduct:
        dummy_variant_real = Variant(
            option1_value="1kg",
            option2_value="Strawberry",
            sku=235052,
            barcode=9238957523,
            price=64.95,
            compare_at=79.95,
            product_weight=1.0
        )

        dummy_variant_real_2 = Variant(
            option1_value="2kg",
            option2_value="Strawberry",
            sku=235053,
            barcode=9233952523,
            price=119.95,
            compare_at=149.95,
            product_weight=2.0
        )

        return DraftProduct(
            title="Gold Standard 100% Whey Protein - Double Rich Chocolate",
            description="""<h2>The World's Best-Selling Whey Protein</h2>
            
        <p>Optimum Nutrition Gold Standard 100% Whey is the gold standard in protein powder. With 24g of high-quality whey protein per serving, it's perfect for muscle recovery and growth after intense training sessions.</p>

        <h3>Key Features:</h3>
        <ul>
            <li>24g of premium whey protein isolates and concentrates</li>
            <li>5.5g of naturally occurring BCAAs per serving</li>
            <li>4g of naturally occurring glutamine and glutamic acid</li>
            <li>Instantized for easy mixing with just a spoon</li>
            <li>Gluten-free formula</li>
        </ul>

        <h3>Suggested Use:</h3>
        <p>Mix one rounded scoop with 180-240ml of cold water, milk, or your favorite beverage. Consume 30-60 minutes after training or between meals to meet your daily protein requirements.</p>

        <p><strong>Allergen Warning:</strong> Contains milk and soy ingredients. Manufactured in a facility that also processes egg, wheat, peanuts, and tree nuts.</p>""",
            inventory=[45, 28],
            type="Sports Nutrition",
            vendor="Optimum Nutrition",
            tags=[
                "protein powder",
                "whey protein", 
                "post-workout",
                "muscle recovery",
                "chocolate",
                "gold standard",
                "optimum nutrition",
                "fitness supplements",
                "bodybuilding",
                "protein shake"
            ],
            lead_option="Size",
            baby_options=["Flavour"],
            variants=[dummy_variant_real, dummy_variant_real_2]
        )

    def load_expected_pydantic_validation(self) -> list:
        return [
            {"name": "Size", "values": ["1kg", "2kg"]},
            {"name": "Flavour", "values": ["Strawberry"]},
        ]

class DraftProductWithMultipleVariantsAndMultipleSubVariants:
    def __init__(self):
        pass

    def load_products_in(self) -> DraftProduct:
        dummy_variant_size_1_strawberry = Variant(
            option1_value="1kg",
            option2_value="Strawberry",
            sku=random.randint(99999, 1000000),
            barcode=random.randint(999999999, 10000000000),
            price=64.95,
            compare_at=79.95,
            product_weight=1.0
        )
        dummy_variant_size_1_chocolate = Variant(
            option1_value="1kg",
            option2_value="Chocolate",
            sku=random.randint(99999, 1000000),
            barcode=random.randint(999999999, 10000000000),
            price=64.95,
            compare_at=79.95,
            product_weight=1.0
        )
        dummy_variant_size_1_vanilla = Variant(
            option1_value="1kg",
            option2_value="Vanilla",
            sku=random.randint(99999, 1000000),
            barcode=random.randint(999999999, 10000000000),
            price=64.95,
            compare_at=79.95,
            product_weight=1.0
        )

        dummy_variant_size_2_strawberry = Variant(
            option1_value="2kg",
            option2_value="Strawberry",
            sku=random.randint(99999, 1000000),
            barcode=random.randint(999999999, 10000000000),
            price=119.95,
            compare_at=149.95,
            product_weight=2.0
        )

        dummy_variant_size_2_chocolate = Variant(
            option1_value="2kg",
            option2_value="Chocolate",
            sku=random.randint(99999, 1000000),
            barcode=random.randint(999999999, 10000000000),
            price=119.95,
            compare_at=149.95,
            product_weight=2.0
        )

        return DraftProduct(
            title="Gold Standard 100% Whey Protein - Double Rich Chocolate",
            description="""<h2>The World's Best-Selling Whey Protein</h2>
            
        <p>Optimum Nutrition Gold Standard 100% Whey is the gold standard in protein powder. With 24g of high-quality whey protein per serving, it's perfect for muscle recovery and growth after intense training sessions.</p>

        <h3>Key Features:</h3>
        <ul>
            <li>24g of premium whey protein isolates and concentrates</li>
            <li>5.5g of naturally occurring BCAAs per serving</li>
            <li>4g of naturally occurring glutamine and glutamic acid</li>
            <li>Instantized for easy mixing with just a spoon</li>
            <li>Gluten-free formula</li>
        </ul>

        <h3>Suggested Use:</h3>
        <p>Mix one rounded scoop with 180-240ml of cold water, milk, or your favorite beverage. Consume 30-60 minutes after training or between meals to meet your daily protein requirements.</p>

        <p><strong>Allergen Warning:</strong> Contains milk and soy ingredients. Manufactured in a facility that also processes egg, wheat, peanuts, and tree nuts.</p>""",
            inventory=[45, 28],
            type="Sports Nutrition",
            vendor="Optimum Nutrition",
            tags=[
                "protein powder",
                "whey protein", 
                "post-workout",
                "muscle recovery",
                "chocolate",
                "gold standard",
                "optimum nutrition",
                "fitness supplements",
                "bodybuilding",
                "protein shake"
            ],
            lead_option="Size",
            baby_options=["Flavour"],
            variants=[dummy_variant_size_1_strawberry, dummy_variant_size_1_chocolate, dummy_variant_size_1_vanilla, dummy_variant_size_2_strawberry, dummy_variant_size_2_chocolate]
        )

    def load_expected_pydantic_validation(self) -> list:
        return [
            {"name": "Size", "values": ["1kg", "2kg"]},
            {"name": "Flavour", "values": ["Strawberry"]},
        ]

# ----------------------------------------------------------------------------------------------------------

class MockShop:
    def __init__(self) -> None:
        pass

    def make_a_product_draft(self, shop_name: str, product_listing: DraftProduct) -> DraftResponse:
        if len(product_listing.variants) == 0:
            raise ShopifyError("No proposed variants")

        return DraftResponse(
            title = product_listing.title,
            url = f"https://admin.shopify.com/store/{shop_name}/products/5327895723",
            time_of_comepletion = datetime.datetime.now(),
            status_code = 200,
        )

class UnitTests():
    def __init__(self) -> None:
        self.client: Shop = MockShop()
        self.test_1_option = DraftProductWith1Option()
        self.test_1_option_data = self.test_1_option.load_products_in()

        self.test_2_options = DraftProductWith2Options()
        self.test_2_options_data = self.test_2_options.load_products_in()

        self.shop_name = os.getenv("SHOP_NAME")

    def test_make_a_product_draft_success(self) -> DraftResponse:
        print("="*60)
        print("STARTING A UNIT TEST FOR test_make_a_product_draft_success")
        assert(self.shop_name is not None and self.shop_name != "")

        draft_response = self.client.make_a_product_draft(shop_name=self.shop_name, product_listing=self.test_1_option_data)
        assert(draft_response.title == self.test_1_option_data.title)

        print("TEST PASSED")
        print("="*60)

    def test_model_validation(self):
        print("="*60)
        print("STARTING A UNIT TEST FOR test_model_validation")

        self.test_2_options_data.validate_length()

        wanted_result = self.test_2_options.load_expected_pydantic_validation()
        actual_result = self.test_2_options_data.options

        if wanted_result != actual_result:
            print(f"Wanted Result = {wanted_result}\n\nActual Result = {actual_result}")

        assert(wanted_result == actual_result)

        print("TEST PASSED")
        print("="*60)
        

class IntegrationTests:
    def __init__(self) -> None:
        self.client: Shop = ShopifyClient()
        self.test_1_option = DraftProductWith1Option()
        self.test_1_option_data = self.test_1_option.load_products_in()

        self.test_2_options = DraftProductWith2Options()
        self.test_2_options_data = self.test_2_options.load_products_in()

        self.max_test = DraftProductWithMultipleVariantsAndMultipleSubVariants()
        self.test_max_test_data = self.max_test.load_products_in()

        self.shop_name = os.getenv("SHOP_NAME")

    def test_make_a_product_draft(self):
        try:
            draft_response = self.client.make_a_product_draft(shop_name=self.shop_name, product_listing=self.test_2_options_data)
            assert(draft_response.status_code == 200)

        except Exception as e:
            print(f"Error: {e} -> \n\n {traceback.format_exc()}")

        
    def test_DraftProductWithMultipleVariantsAndMultipleSubVariants(self):
        try:
            draft_response = self.client.make_a_product_draft(shop_name=self.shop_name, product_listing=self.test_max_test_data)
            assert(draft_response.status_code == 200)

        except Exception as e:
            print(f"Error: {e} -> \n\n {traceback.format_exc()}")


    def test_get_products_from_store(self):
        print("="*60)
        print(f"STARTING {inspect.stack()[0][3]}")
        res = self.client.get_products_from_store()
        if not res:
            print("No result")
            return
        print(f"Result: \n\n{res[:25]}")
        print(f"\nJson Of A Product: \n\n {res[3].to_dict()}")
        print(f"Type: {type(res[3])}")
        print("="*60)

if __name__ == "__main__":
    integration = IntegrationTests()
    #integration.test_get_products_from_store()
    #integration.test_make_a_product_draft()
    integration.test_DraftProductWithMultipleVariantsAndMultipleSubVariants()

    ut = UnitTests()
    #ut.test_make_a_product_draft_success()
    #ut.test_model_validation()