import random
import traceback
from dotenv import load_dotenv
import os
import sys
import inspect
import datetime

# Add parent directories to Python path so we can import packages
# Go up from shopify_api -> infrastructure -> agents -> Product generating agent
current_dir = os.path.dirname(os.path.abspath(__file__))
infrastructure_dir = os.path.dirname(current_dir)
agents_dir = os.path.dirname(infrastructure_dir)
project_root = os.path.dirname(agents_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

from agents.infrastructure.shopify_api.client import ShopifyClient, Shop, Locations, Location
from agents.infrastructure.shopify_api.product_schema import DraftResponse, Variant, DraftProduct, InventoryAtStores, Option
from agents.infrastructure.shopify_api.exceptions import ShopifyError
from agents.infrastructure.shopify_api.schema import Inventory, Inputs

load_dotenv()

dummy_variant = Variant(
    option1_value=Option(option_name="Size", option_value="500g"),
    sku=235053,
    barcode=9233952523,
    price=29.99,
    compare_at=39.99,
    product_weight=0.5,
    inventory_at_stores=InventoryAtStores(city=10, south_melbourne=20)
)

dummy_draft_product = DraftProduct(
    title="Test Product Title",
    description="This is a test product description for dummy data",
    type="Supplement",
    vendor="Test Vendor",
    tags=["test", "dummy", "sample"],
    lead_option="Size",
    variants=[dummy_variant]
)

# Real example parsed from actual product data
real_example_parsed = DraftProduct(
    title="Optimum Nutrition Gold Standard 100% Whey Protein Powder",
    vendor="Optimum Nutrition",
    type="Whey Blend Protein Powder",
    tags=["Sports Nutrition", "Whey Blends"],
    description="<h2>Product Overview</h2><p><strong>The World's #1 Whey Protein Powder.</strong> GOLD STANDARD 100% WHEY™ Protein powder supports muscle and post-workout recovery with 24g of quality protein and 5.5g of naturally occurring BCAAs per serving. It's crafted to be a complete, fast-digesting protein with whey protein isolate as the primary source – a filtered form of whey that can support protein goals for people at every level of fitness – from daily runners and gym-goers to competitive strength athletes and everyone in between.</p><p>With more than 15 great-tasting flavor options, satisfying texture, and easy mixing with only a glass and spoon, you'll always look forward to getting the protein you want in your active, performance-driven lifestyle. It's everything you've come to expect from OPTIMUM NUTRITION®: The World's #1 Sports Nutrition Brand.</p><h2>Benefits</h2><ul><li>24g of protein per serving to help build and maintain muscle</li><li>5.5g of naturally occurring BCAAs per serving</li><li>Gluten free</li><li>Banned Substance Tested</li><li>Easy mixing with only a glass and spoon</li><li>15+ great-tasting flavors</li></ul><h2>Suggested Use</h2><p>Mix about one scoop of the powder into 6 to 8 fluid ounces of cold water, milk, or other beverage. Stir, shake, or blend until dissolved. For best results, mix up your shake 30 to 60 minutes after your workout or use as an anytime snack in your balanced diet.</p><p>For healthy adults, consume enough protein to meet your daily protein requirements with a combination of high protein foods and protein supplements throughout the day as part of a balanced diet and exercise program.</p>",
    lead_option="Size",
    baby_options=["Flavor"],
    variants=[
        Variant(
            option1_value=Option(option_name="Size", option_value="2 lb"),
            option2_value=Option(option_name="Flavor", option_value="Chocolate"),
            option3_value=None,
            sku=922001,
            barcode=810095637971,
            price=49.95,
            product_weight=2.0,
            compare_at=None,
            inventory_at_stores=InventoryAtStores(city=1000, south_melbourne=1000)
        ),
        Variant(
            option1_value=Option(option_name="Size", option_value="2 lb"),
            option2_value=Option(option_name="Flavor", option_value="Vanilla"),
            option3_value=None,
            sku=922002,
            barcode=810095637972,
            price=49.95,
            product_weight=2.0,
            compare_at=None,
            inventory_at_stores=InventoryAtStores(city=1000, south_melbourne=1000)
        ),
        Variant(
            option1_value=Option(option_name="Size", option_value="2 lb"),
            option2_value=Option(option_name="Flavor", option_value="Strawberry"),
            option3_value=None,
            sku=922005,
            barcode=810095637975,
            price=49.95,
            product_weight=2.0,
            compare_at=None,
            inventory_at_stores=InventoryAtStores(city=1000, south_melbourne=1000)
        ),
        Variant(
            option1_value=Option(option_name="Size", option_value="5 lb"),
            option2_value=Option(option_name="Flavor", option_value="Chocolate"),
            option3_value=None,
            sku=922003,
            barcode=810095637973,
            price=89.95,
            product_weight=5.0,
            compare_at=None,
            inventory_at_stores=InventoryAtStores(city=1000, south_melbourne=1000)
        ),
        Variant(
            option1_value=Option(option_name="Size", option_value="5 lb"),
            option2_value=Option(option_name="Flavor", option_value="Vanilla"),
            option3_value=None,
            sku=922004,
            barcode=810095637974,
            price=89.95,
            product_weight=5.0,
            compare_at=None,
            inventory_at_stores=InventoryAtStores(city=1000, south_melbourne=1000)
        ),
    ]
)

# -----------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------

class DraftProductWith1Option:
    def __init__(self):
        pass

    def load_products_in(self) -> DraftProduct:
        dummy_variant_real = Variant(
            option1_value=Option(option_name="Size", option_value="2kg"),
            sku=561596,
            barcode=9238957523,
            price=64.95,
            compare_at=79.95,
            product_weight=1.0,
            inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
        )

        dummy_variant_real_2 = Variant(
            option1_value=Option(option_name="Size", option_value="1kg"),
            sku=561597,
            barcode=9233952523,
            price=119.95,
            compare_at=149.95,
            product_weight=2.0,
            inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
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
            option1_value=Option(option_name="Size", option_value="1kg"),
            option2_value=Option(option_name="Flavour", option_value="Strawberry"),
            sku=235052,
            barcode=9238957523,
            price=64.95,
            compare_at=79.95,
            product_weight=1.0,
            inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
        )

        dummy_variant_real_2 = Variant(
            option1_value=Option(option_name="Size", option_value="2kg"),
            option2_value=Option(option_name="Flavour", option_value="Strawberry"),
            sku=235053,
            barcode=9233952523,
            price=119.95,
            compare_at=149.95,
            product_weight=2.0,
            inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
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
            option1_value=Option(option_name="Size", option_value="1kg"),
            option2_value=Option(option_name="Flavour", option_value="Strawberry"),
            sku=random.randint(99999, 1000000),
            barcode=random.randint(999999999, 10000000000),
            price=64.95,
            compare_at=79.95,
            product_weight=1.0,
            inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
        )
        dummy_variant_size_1_chocolate = Variant(
            option1_value=Option(option_name="Size", option_value="1kg"),
            option2_value=Option(option_name="Flavour", option_value="Chocolate"),
            sku=random.randint(99999, 1000000),
            barcode=random.randint(999999999, 10000000000),
            price=64.95,
            compare_at=79.95,
            product_weight=1.0,
            inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
        )
        dummy_variant_size_1_vanilla = Variant(
            option1_value=Option(option_name="Size", option_value="1kg"),
            option2_value=Option(option_name="Flavour", option_value="Vanilla"),
            sku=random.randint(99999, 1000000),
            barcode=random.randint(999999999, 10000000000),
            price=64.95,
            compare_at=79.95,
            product_weight=1.0,
            inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
        )

        dummy_variant_size_2_strawberry = Variant(
            option1_value=Option(option_name="Size", option_value="2kg"),
            option2_value=Option(option_name="Flavour", option_value="Strawberry"),
            sku=random.randint(99999, 1000000),
            barcode=random.randint(999999999, 10000000000),
            price=119.95,
            compare_at=149.95,
            product_weight=2.0,
            inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
        )

        dummy_variant_size_2_chocolate = Variant(
            option1_value=Option(option_name="Size", option_value="2kg"),
            option2_value=Option(option_name="Flavour", option_value="Chocolate"),
            sku=random.randint(99999, 1000000),
            barcode=random.randint(999999999, 10000000000),
            price=119.95,
            compare_at=149.95,
            product_weight=2.0,
            inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
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

mock_inventory_request = Inventory(
    inventory_item_id= "44793372835937", #is this SKU, Barcode or Product issued id?
    stores=[Inputs(name_of_store="City", inventory_number=50), Inputs(name_of_store="South Melbourne", inventory_number=50)],
)

# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------

class MockShop:
    def __init__(self) -> None:
        pass

    def make_a_product_draft(self, shop_name: str, product_listing: DraftProduct) -> DraftResponse:
        print("="*60)
        print("Called: MockShop.make_a_product")
        if len(product_listing.variants) == 0:
            raise ShopifyError("No proposed variants")

        print("MockShop.make_a_product returned DraftResponse")
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
        api_key = os.getenv("SHOPIFY_API_KEY")
        api_secret = os.getenv("SHOPIFY_API_SECRET")
        token = os.getenv("SHOPIFY_TOKEN")
        shop_name = os.getenv("SHOP_NAME")
        shop_url = os.getenv("SHOP_URL")
        location_one_id = f"gid://shopify/Location/{os.getenv("LOCATION_ONE_ID")}"
        location_two_id = f"gid://shopify/Location/{os.getenv("LOCATION_TWO_ID")}"

        print(f"Location One: {location_one_id}")
        print(f"Location Two: {location_two_id}")
        locations = Locations(locations=[Location(name="City", id=location_one_id), Location(name="South Melbourne", id=location_two_id)])

        self.client: Shop = ShopifyClient(api_key=api_key, api_secret=api_secret, token=token, shop_url=shop_url, shop_name=shop_name, locations=locations)
        self.test_1_option = DraftProductWith1Option()
        self.test_1_option_data = self.test_1_option.load_products_in()

        self.test_2_options = DraftProductWith2Options()
        self.test_2_options_data = self.test_2_options.load_products_in()

        self.max_test = DraftProductWithMultipleVariantsAndMultipleSubVariants()
        self.test_max_test_data = self.max_test.load_products_in()

        self.test_a_real_instance = real_example_parsed

        self.shop_name = shop_name

    def test_make_a_product_draft(self):
        try:
            draft_response = self.client.make_a_product_draft(product_listing=self.test_2_options_data)
            assert(draft_response.status_code == 200)

            print(draft_response.model_dump_json(indent=3))

        except Exception as e:
            print(f"Error: {e} -> \n\n {traceback.format_exc()}")

        
    def test_DraftProductWithMultipleVariantsAndMultipleSubVariants(self):
        try:
            draft_response = self.client.make_a_product_draft(product_listing=self.test_max_test_data)
            assert draft_response.status_code == 200

        except Exception as e:
            print(f"Error: {e} -> \n\n {traceback.format_exc()}")

    def test_real_instance(self):
        try:
            print(f"Datas Type: {type(self.test_a_real_instance)}")
            draft_response = self.client.make_a_product_draft(shop_name=self.shop_name, product_listing=self.test_a_real_instance)
            assert draft_response.status_code == 200

        except Exception as e:
            print(f"Error: {e} \n {traceback.format_exc()}")

    def test_changing_a_products_inventory(self):
        completed = self.client.fill_inventory(inventory_data=mock_inventory_request)
        assert completed

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

    def test_what_methods_does_a_variant_have(self):
        self.client.what_methods_does_a_variant_have()

    def test_activating_a_location(self):
        self.client.make_available_at_all_locations(inventory_item_id="44793372835937")

if __name__ == "__main__":
    integration = IntegrationTests()
    #integration.test_get_products_from_store()
    #integration.test_make_a_product_draft()
    #integration.test_DraftProductWithMultipleVariantsAndMultipleSubVariants()
    #integration.test_real_instance()
    #integration.test_changing_a_products_inventory()
    #integration.test_what_methods_does_a_variant_have()
    # integration.test_activating_a_location()

    #ut = UnitTests()
    #ut.test_make_a_product_draft_success()
    #ut.test_model_validation()