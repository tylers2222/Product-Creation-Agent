import os
import sys

from qdrant_client.models import PointStruct

# Add parent directory to Python path so we can import packages
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import datetime
from firecrawl_api.client import FireResult, DataResult
from shopify_api.client import DraftProduct, Variant, DraftResponse
from agent.tools import scrape_and_return_similar_products, web_scraper_impl, draft_product_impl
from vector_database.embeddings_test import MockEmbeddor 
from vector_database.db_test import MockVectorDb
from firecrawl_api.client_test import MockScraperClient
import shopify
from vector_database.embeddings import Embeddings
from vector_database.db import vector_database
from firecrawl_api.client import FirecrawlClient


# Dummy Shopify Product objects for testing
dummy_shopify_objects = []

# Product 1: Protein Powder
p1 = shopify.Product()
p1.id = 6776951308385
p1.title = "Optimum Nutrition Gold Standard 100% Whey Protein"
p1.body_html = "<h2>Premium Whey Protein Supplement</h2><p>Optimum Nutrition's Gold Standard Whey is the world's best-selling whey protein powder. With 24g of high-quality whey protein per serving, it's perfect for muscle recovery and growth after intense training sessions.</p><ul><li>24g of premium whey protein per serving</li><li>5.5g naturally occurring BCAAs</li><li>4g naturally occurring glutamine</li><li>Instantized for easy mixing</li><li>Gluten-free formula</li></ul>"
p1.product_type = "Sports Nutrition"
p1.tags = "protein powder, whey protein, post-workout, muscle recovery, chocolate, fitness supplements, bodybuilding, protein shake"
dummy_shopify_objects.append(p1)

# Product 2: Pre-Workout
p2 = shopify.Product()
p2.id = 6776951308386
p2.title = "C4 Original Pre-Workout Powder"
p2.body_html = "<h2>Explosive Energy Pre-Workout</h2><p>C4 Original is the #1 selling pre-workout in America, designed to ignite your workouts with explosive energy and intense focus. Contains 150mg of caffeine and CarnoSyn Beta-Alanine.</p><ul><li>150mg caffeine for energy</li><li>CarnoSyn Beta-Alanine for endurance</li><li>Arginine AKG for pumps</li><li>Great tasting flavors</li></ul>"
p2.product_type = "Pre-Workout"
p2.tags = "pre-workout, energy, caffeine, beta-alanine, workout supplement, C4, pump, focus"
dummy_shopify_objects.append(p2)

# Product 3: Multivitamin
p3 = shopify.Product()
p3.id = 6776951308387
p3.title = "Optimum Nutrition Opti-Men Multivitamin"
p3.body_html = "<h2>Complete Nutrient Optimization System</h2><p>Opti-Men is a comprehensive nutrient optimization system providing 75+ active ingredients in 4 blends specifically designed to support the nutrient needs of active men.</p><ul><li>75+ active ingredients</li><li>8 essential amino acids</li><li>25+ vitamins and minerals</li><li>Botanical extracts and antioxidants</li></ul>"
p3.product_type = "Vitamins"
p3.tags = "multivitamin, vitamins, minerals, men's health, daily vitamins, nutrition, wellness, health supplement"
dummy_shopify_objects.append(p3)

# Product 4: BCAA
p4 = shopify.Product()
p4.id = 6776951308388
p4.title = "Xtend Original BCAA Powder"
p4.body_html = "<h2>Intra-Workout Catalyst</h2><p>Xtend Original contains 7g of BCAAs in the scientifically studied 2:1:1 ratio, along with hydration-promoting electrolytes. Support muscle recovery, reduce muscle fatigue, and enhance endurance during your workout.</p><ul><li>7g BCAAs per serving</li><li>2:1:1 ratio of leucine, isoleucine, valine</li><li>Electrolytes for hydration</li><li>Zero sugar and zero carbs</li></ul>"
p4.product_type = "Amino Acids"
p4.tags = "BCAA, amino acids, intra-workout, recovery, muscle recovery, hydration, electrolytes, sugar-free"
dummy_shopify_objects.append(p4)

# Product 5: Creatine
p5 = shopify.Product()
p5.id = 6776951308389
p5.title = "Optimum Nutrition Micronized Creatine Monohydrate"
p5.body_html = "<h2>Pure Creatine Monohydrate</h2><p>Creatine is one of the most researched and effective supplements for increasing strength, power, and muscle mass. Our micronized formula mixes easier and absorbs better.</p><ul><li>5g pure creatine monohydrate per serving</li><li>Micronized for better absorption</li><li>Supports strength and power</li><li>Helps build lean muscle mass</li></ul>"
p5.product_type = "Creatine"
p5.tags = "creatine, creatine monohydrate, strength, power, muscle building, performance, workout supplement"
dummy_shopify_objects.append(p5)

# Product 6: Fish Oil
p6 = shopify.Product()
p6.id = 6776951308390
p6.title = "Nordic Naturals Ultimate Omega Fish Oil"
p6.body_html = "<h2>High-Potency Omega-3 Fish Oil</h2><p>Ultimate Omega provides concentrated omega-3 essential fatty acids from fresh, wild-caught fish. Supports heart health, brain function, and overall wellness.</p><ul><li>1280mg omega-3s per serving</li><li>Supports heart and brain health</li><li>Molecularly distilled for purity</li><li>Lemon flavor, no fishy aftertaste</li></ul>"
p6.product_type = "Omega-3"
p6.tags = "fish oil, omega-3, EPA, DHA, heart health, brain health, essential fatty acids, Nordic Naturals"
dummy_shopify_objects.append(p6)

# Product 7: Greens Powder
p7 = shopify.Product()
p7.id = 6776951308391
p7.title = "Athletic Greens AG1 Nutritional Drink"
p7.body_html = "<h2>All-In-One Nutritional Insurance</h2><p>AG1 is a comprehensive daily nutritional drink with 75 vitamins, minerals, and whole-food sourced ingredients. One scoop covers your nutritional bases and supports immunity, energy, recovery, and gut health.</p><ul><li>75 vitamins, minerals, and nutrients</li><li>Supports immunity and gut health</li><li>Boosts energy and recovery</li><li>NSF Certified for Sport</li></ul>"
p7.product_type = "Greens"
p7.tags = "greens powder, superfood, vitamins, minerals, gut health, immunity, energy, athletic greens, AG1"
dummy_shopify_objects.append(p7)

# Product 8: Protein Bar
p8 = shopify.Product()
p8.id = 6776951308392
p8.title = "Quest Protein Bar - Chocolate Chip Cookie Dough"
p8.body_html = "<h2>High Protein, Low Carb Nutrition Bar</h2><p>Quest Bars deliver 20g of protein with minimal sugar and net carbs. Perfect for on-the-go nutrition that doesn't compromise on taste.</p><ul><li>20g complete protein</li><li>4g net carbs</li><li>Less than 1g sugar</li><li>Gluten-free</li><li>14g fiber</li></ul>"
p8.product_type = "Protein Bars"
p8.tags = "protein bar, Quest, low carb, high protein, snack, gluten-free, keto-friendly, meal replacement"
dummy_shopify_objects.append(p8)

# Product 9: Mass Gainer
p9 = shopify.Product()
p9.id = 6776951308393
p9.title = "Optimum Nutrition Serious Mass Weight Gainer"
p9.body_html = "<h2>High-Calorie Mass Gainer</h2><p>Serious Mass provides 1,250 calories per serving to fuel muscle growth and recovery. Ideal for hard gainers who need extra calories to build mass.</p><ul><li>1,250 calories per serving</li><li>50g protein blend</li><li>252g carbohydrates</li><li>25 vitamins and minerals</li><li>Creatine and glutamine</li></ul>"
p9.product_type = "Mass Gainers"
p9.tags = "mass gainer, weight gainer, calories, muscle building, bulking, high protein, serious mass, hard gainer"
dummy_shopify_objects.append(p9)

# Product 10: Sleep Aid
p10 = shopify.Product()
p10.id = 6776951308394
p10.title = "Optimum Nutrition ZMA Recovery Support"
p10.body_html = "<h2>Nighttime Recovery Support</h2><p>ZMA is a scientifically designed anabolic mineral formula containing highly bioavailable forms of Zinc, Magnesium, and Vitamin B6. Supports immune function, recovery, and restful sleep.</p><ul><li>Zinc for immune support</li><li>Magnesium for muscle relaxation</li><li>Vitamin B6 for recovery</li><li>Supports natural sleep quality</li></ul>"
p10.product_type = "Recovery"
p10.tags = "ZMA, zinc, magnesium, vitamin B6, sleep aid, recovery, muscle recovery, immune support, nighttime"
dummy_shopify_objects.append(p10)

query = "Caruso's Ashwagandha + Sleep"

# Mock SearchData object (mimics the structure returned by firecrawl.search())
class MockSearchData:
    def __init__(self, web_data):
        self.web = web_data

dummy_scrape_result = FireResult(
    data=MockSearchData(
        web_data=[
            {
                "markdown": "fweuybfuibweafuibdsuiafbuidsabfuiasdbfuiasdbfuiasbfuiasbfuia",
                "metadata": {
                    "title": "Nutrition Warehouse",
                    "description": "Switch Nutrition's Hair + Skin is a complete beauty and recovery formula, designed to nourish and revitalise you from within.",
                    "url": "dummywebsite.com.au"
                }
            },
            {
                "markdown": "",
                "metadata": {
                    "title": "Chemist Warehouse",
                    "description": "Premium health supplement with essential vitamins and minerals for daily wellness support.",
                    "url": "chemistwarehouse.com.au"
                }
            },
            {
                "markdown": "idsoanfiosdnfiodasnfioanfoingoiewrbnguiewnbfuiodsnbafiusdbnfuiasbdnfuibgavuibnudiva",
                "metadata": {
                    "title": "My Vitamins",
                    "description": "High-quality supplement designed to support overall health and wellbeing with natural ingredients.",
                    "url": "myvitamins.com.au"
                }
            },
            {
                "markdown": "dnfgionsaoigbnaoudbgiuasbgviubasdiuvbuaibvuirebvuiebrvuiberuivbreufivbeurib",
                "metadata": {
                    "title": "Nature's Own",
                    "description": "Trusted brand offering scientifically formulated supplements for optimal health and performance.",
                    "url": "naturesown.com.au"
                }
            },
            {
                "markdown": "fcwaioenvcionvbnavienwaciodsanoicndsaiovcnioewoewipcqpqocjeowpcowecnw",
                "metadata": {
                    "title": "Priceline Pharmacy",
                    "description": "Comprehensive health and wellness products available online with fast shipping and competitive prices.",
                    "url": "priceline.com.au"
                }
            },
        ]
    ),
    query=query
)

dummy_draft_product = DraftProduct(
    title="Switch Nutrition Hair + Skin",
    description="<h2>Complete Beauty and Recovery Formula</h2><p>Switch Nutrition's Hair + Skin is designed to nourish and revitalise you from within. This comprehensive formula contains essential vitamins and minerals to support healthy hair, skin, and overall wellbeing.</p><ul><li>Supports hair growth and strength</li><li>Promotes healthy, radiant skin</li><li>Contains biotin and collagen</li><li>Natural ingredients</li></ul>",
    inventory=[1000, 1000],
    type="Supplement",
    vendor="Switch Nutrition",
    tags=["hair care", "skin care", "beauty supplements", "biotin", "collagen", "vitamins", "wellness"],
    variants=[
        Variant(
            option_name="Size",
            option_value="60 Veg Caps",
            sku=123456,
            barcode=987654321,
            price=29.95,
            compare_at=39.95,
            product_weight=0.15
        ),
        Variant(
            option_name="Size",
            option_value="120 Veg Caps",
            sku=123457,
            barcode=987654322,
            price=49.95,
            compare_at=69.95,
            product_weight=0.30
        )
    ]
)

class dummy_shop:
    def __init__(self):
        print("Initialised the dummy shop")

    def make_a_product_draft(self, product_listing: DraftProduct):
        print("Returned dummy draft response")
        return DraftResponse(
            title = f"{product_listing.title}",
            time_of_comepletion = datetime.datetime.now(),
            status_code = 200,
            error_message = None
        )

class UnitTests:
    def __init__(self):
        self.scraper = MockScraperClient()
        self.embeddor = MockEmbeddor()
        self.vector_db = MockVectorDb()
        self.shop = dummy_shop()

    def test_scrape_and_return_similar_products(self):
        print("="*60)
        print("STARTING test_scrape_and_return_similar_products()\n\n\n")

        print("*"*60)
        print("Testing each mock individually for return results, make sure they work")

        fire_result = self.scraper.scrape_and_search_site(query=query)
        assert(fire_result.data is not None)
        print(f"1) self.scraper.scrape_and_search_site = SUCCESSFUL -> {fire_result.data}\n\n")

        embeddings = self.embeddor.embed_documents([query])
        assert(embeddings is not None)
        print(f"2) self.embeddor.embed_documents = SUCCESSFUL -> {embeddings[0][:5]}\n\n")

        # This uploads points to the mocks in memory list database
        db_response = self.vector_db.upsert_points("shopify_products", points=[PointStruct(id=1, vector=[0.1], payload={"id": 1})])
        points = self.vector_db.search_points("shopify_products", embeddings[0], k=2)
        assert(points is not None)
        print(f"3) self.vector_db.search_points = SUCCESSFUL -> {points}")

        scrape_and_similarity = scrape_and_return_similar_products(query=query, scraper=self.scraper, embeddor=self.embeddor, vector_db=self.vector_db)
        assert(scrape_and_similarity is not None)

        print(f"\nScrape && Similarity ->\n\n{scrape_and_similarity.model_dump_json()}")
        print("="*60)

class IntegrationTests:
    def __init__(self):
        self.scraper = FirecrawlClient()
        self.embeddor = Embeddings()
        self.vector_db = vector_database()
        self.shop = dummy_shop()

    def test_scrape_and_return_similar_products(self):
        print("="*60)
        print("STARTING INTEGRAITON TEST test_scrape_and_return_similar_products")

        scrape_and_similarity = scrape_and_return_similar_products(query=query, scraper=self.scraper, embeddor=self.embeddor, vector_db=self.vector_db)
        assert(scrape_and_similarity is not None)

        # fix this  to include the scraper response and similarity response to a terminal pretty print
        print(f"\nScrape && Similarity ->\n\nScraper Result = {scrape_and_similarity.scraper_response.model_dump_json()}")
        for idx, similar_products in enumerate(scrape_and_similarity.similarity_response):
            print(f"\n\n{idx+1}) {similar_products}")
        print("="*60)

if __name__ == "__main__":
    #ut = UnitTests()
    #ut.test_scrape_and_return_similar_products()

    it = IntegrationTests()
    it.test_scrape_and_return_similar_products()

