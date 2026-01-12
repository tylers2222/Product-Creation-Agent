import inspect
import json
import os
import sys
import logging
import random
import traceback
from qdrant_client.models import PointStruct
import shopify
from dotenv import load_dotenv

# Add parent directory to Python path so we can import packages
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.infrastructure.vector_database.db import vector_database, VectorDb
from agents.infrastructure.vector_database.embeddings import Embeddings
from agents.infrastructure.vector_database.response_schema import DbResponse
from agents.infrastructure.vector_database.schema import VectorFilter
from agents.infrastructure.vector_database.db_mock import MockVectorDb, points_tests

# Load environment variables from .env file
load_dotenv()

# Configure logging to show all INFO level and above messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration even if already configured
)

# Silence noisy third-party libraries by completely disabling their handlers
for lib in ["openai", "langchain", "langchain_openai", "httpx", "httpcore", "urllib3", "qdrant_client"]:
    logger = logging.getLogger(lib)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False
    # Remove all existing handlers and add a NullHandler
    logger.handlers = []
    logger.addHandler(logging.NullHandler())

dummy_shopify_data = [
    {
        "product_name": "Optimum Nutrition Gold Standard 100% Whey Protein",
        "description": "<h2>Premium Whey Protein Supplement</h2><p>Optimum Nutrition's Gold Standard Whey is the world's best-selling whey protein powder. With 24g of high-quality whey protein per serving, it's perfect for muscle recovery and growth after intense training sessions.</p><ul><li>24g of premium whey protein per serving</li><li>5.5g naturally occurring BCAAs</li><li>4g naturally occurring glutamine</li><li>Instantized for easy mixing</li><li>Gluten-free formula</li></ul>",
        "product_type": "Sports Nutrition",
        "tags": ["protein powder", "whey protein", "post-workout", "muscle recovery", "chocolate", "fitness supplements", "bodybuilding", "protein shake"]
    },
    {
        "product_name": "Nature's Way Activated B-Complex",
        "description": "<h2>Complete B Vitamin Complex</h2><p>Nature's Way Activated B-Complex provides essential B vitamins in their active forms for maximum absorption. Supports energy metabolism, nervous system health, and overall wellbeing.</p><ul><li>Active forms of B vitamins</li><li>Supports energy production</li><li>Nervous system support</li><li>Easy-to-swallow capsules</li></ul>",
        "product_type": "Vitamins",
        "tags": ["vitamins", "B-complex", "energy", "metabolism", "nervous system", "supplements", "wellness", "health"]
    },
    {
        "product_name": "Blackmores Omega Daily",
        "description": "<h2>Fish Oil Omega-3 Supplement</h2><p>Blackmores Omega Daily is a high-strength fish oil supplement providing essential omega-3 fatty acids EPA and DHA. Supports heart health, brain function, and joint mobility.</p><ul><li>High-strength omega-3</li><li>Supports heart health</li><li>Brain function support</li><li>Joint mobility</li><li>Enteric coated for easy digestion</li></ul>",
        "product_type": "Supplements",
        "tags": ["omega-3", "fish oil", "heart health", "brain health", "joint support", "DHA", "EPA", "essential fatty acids"]
    },
    {
        "product_name": "Swisse Ultiboost Sleep",
        "description": "<h2>Natural Sleep Support Formula</h2><p>Swisse Ultiboost Sleep is a scientifically formulated blend of herbs and nutrients designed to support healthy sleep patterns. Contains valerian, hops, and magnesium for natural relaxation.</p><ul><li>Natural sleep support</li><li>Valerian and hops blend</li><li>Magnesium for relaxation</li><li>Non-habit forming</li><li>Vegan friendly</li></ul>",
        "product_type": "Sleep Support",
        "tags": ["sleep", "sleep support", "valerian", "hops", "relaxation", "insomnia", "natural sleep", "magnesium"]
    },
    {
        "product_name": "Vitacoost Probiotic 50 Billion",
        "description": "<h2>High Potency Probiotic Supplement</h2><p>Vitacoost Probiotic 50 Billion provides 50 billion CFU per serving with 10 different probiotic strains. Supports digestive health, immune function, and gut microbiome balance.</p><ul><li>50 billion CFU per serving</li><li>10 probiotic strains</li><li>Digestive health support</li><li>Immune system support</li><li>Delayed-release capsules</li></ul>",
        "product_type": "Probiotics",
        "tags": ["probiotics", "digestive health", "gut health", "immune support", "microbiome", "digestion", "CFU", "bacteria"]
    },
    {
        "product_name": "MusclePharm Combat Protein",
        "description": "<h2>Multi-Source Protein Blend</h2><p>MusclePharm Combat Protein combines multiple protein sources including whey, casein, and egg protein for sustained muscle building. Perfect for post-workout recovery and between meals.</p><ul><li>Multi-source protein blend</li><li>Fast and slow release proteins</li><li>25g protein per serving</li><li>BCAA enriched</li><li>Great taste</li></ul>",
        "product_type": "Sports Nutrition",
        "tags": ["protein", "whey", "casein", "muscle building", "recovery", "BCAA", "fitness", "athletic performance"]
    },
    {
        "product_name": "Cenovis Vitamin C 1000mg",
        "description": "<h2>High-Strength Vitamin C Tablets</h2><p>Cenovis Vitamin C 1000mg provides high-strength vitamin C support for immune system function, collagen production, and antioxidant protection.</p><ul><li>1000mg vitamin C per tablet</li><li>Immune system support</li><li>Antioxidant protection</li><li>Collagen production support</li><li>Easy-to-swallow tablets</li></ul>",
        "product_type": "Vitamins",
        "tags": ["vitamin C", "immune support", "antioxidant", "collagen", "immune system", "wellness", "ascorbic acid", "health"]
    },
    {
        "product_name": "Bio Island Iron Kids",
        "description": "<h2>Liquid Iron Supplement for Children</h2><p>Bio Island Iron Kids is a specially formulated liquid iron supplement designed for children. Supports healthy development, cognitive function, and prevents iron deficiency.</p><ul><li>Child-friendly liquid formula</li><li>Prevents iron deficiency</li><li>Supports cognitive development</li><li>Great cherry flavour</li><li>Easy to take</li></ul>",
        "product_type": "Children's Supplements",
        "tags": ["iron", "children", "kids", "liquid", "development", "cognitive", "iron deficiency", "nutrition"]
    },
    {
        "product_name": "Ethical Nutrients Zinc + Vitamin C",
        "description": "<h2>Immune System Support Formula</h2><p>Ethical Nutrients Zinc + Vitamin C combines two essential nutrients for comprehensive immune system support. Helps reduce the duration and severity of cold symptoms.</p><ul><li>Zinc and vitamin C combination</li><li>Immune system support</li><li>Cold and flu support</li><li>Antioxidant protection</li><li>High-quality ingredients</li></ul>",
        "product_type": "Immune Support",
        "tags": ["zinc", "vitamin C", "immune support", "cold", "flu", "immune system", "antioxidant", "wellness"]
    },
    {
        "product_name": "Thompson's One-A-Day Multivitamin",
        "description": "<h2>Complete Daily Multivitamin</h2><p>Thompson's One-A-Day Multivitamin provides a comprehensive blend of essential vitamins and minerals to support daily health and wellbeing. One tablet per day formula.</p><ul><li>Comprehensive vitamin blend</li><li>Essential minerals included</li><li>One tablet per day</li><li>Supports daily health</li><li>Convenient formula</li></ul>",
        "product_type": "Multivitamins",
        "tags": ["multivitamin", "daily vitamins", "minerals", "wellness", "daily health", "nutrition", "one-a-day", "complete formula"]
    }
]

# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# -------------------------------------------------------------------------

# Create 5 dummy Shopify Product objects
product1 = shopify.Product()
product1.id = 6776951308385
product1.title = "Optimum Nutrition Gold Standard 100% Whey Protein"
product1.body_html = "<h2>Premium Whey Protein Supplement</h2><p>Optimum Nutrition's Gold Standard Whey is the world's best-selling whey protein powder. With 24g of high-quality whey protein per serving, it's perfect for muscle recovery and growth after intense training sessions.</p>"
product1.product_type = "Sports Nutrition"
product1.tags = "protein powder, whey protein, post-workout, muscle recovery, chocolate, fitness supplements, bodybuilding, protein shake"

product2 = shopify.Product()
product2.id = 6776951308386
product2.title = "Nature's Way Activated B-Complex"
product2.body_html = "<h2>Complete B Vitamin Complex</h2><p>Nature's Way Activated B-Complex provides essential B vitamins in their active forms for maximum absorption. Supports energy metabolism, nervous system health, and overall wellbeing.</p>"
product2.product_type = "Vitamins"
product2.tags = "vitamins, B-complex, energy, metabolism, nervous system, supplements, wellness, health"

product3 = shopify.Product()
product3.id = 6776951308387
product3.title = "Blackmores Omega Daily"
product3.body_html = "<h2>Fish Oil Omega-3 Supplement</h2><p>Blackmores Omega Daily is a high-strength fish oil supplement providing essential omega-3 fatty acids EPA and DHA. Supports heart health, brain function, and joint mobility.</p>"
product3.product_type = "Supplements"
product3.tags = "omega-3, fish oil, heart health, brain health, joint support, DHA, EPA, essential fatty acids"

product4 = shopify.Product()
product4.id = 6776951308388
product4.title = "Swisse Ultiboost Sleep"
product4.body_html = "<h2>Natural Sleep Support Formula</h2><p>Swisse Ultiboost Sleep is a scientifically formulated blend of herbs and nutrients designed to support healthy sleep patterns. Contains valerian, hops, and magnesium for natural relaxation.</p>"
product4.product_type = "Sleep Support"
product4.tags = "sleep, sleep support, valerian, hops, relaxation, insomnia, natural sleep, magnesium"

product5 = shopify.Product()
product5.id = 6776951308389
product5.title = "Vitacoost Probiotic 50 Billion"
product5.body_html = "<h2>High Potency Probiotic Supplement</h2><p>Vitacoost Probiotic 50 Billion provides 50 billion CFU per serving with 10 different probiotic strains. Supports digestive health, immune function, and gut microbiome balance.</p>"
product5.product_type = "Probiotics"
product5.tags = "probiotics, digestive health, gut health, immune support, microbiome, digestion, CFU, bacteria"

dummy_shopify_data_in_shopify_class = [product1, product2, product3, product4, product5]

# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# -------------------------------------------------------------------------

class unit_tests:
    def __init__(self):
        self.db = MockVectorDb()

    def test_upsert_points(self):
        points = [
            PointStruct(
                id=i,
                vector = [random.randint(-3, 3) for i in range(10)],
                payload={"number": random.random()}
            ) for i in range (5)
        ]

        print(f"Length Of Points -> {len(points)}")

        db_response = self.db.upsert_points(collection_name="Tyler", )
        assert(db_response is not None)

    def test_search_points(self):
        pass

# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# -------------------------------------------------------------------------

class integration_tests:
    def __init__(self) -> None:
        self.fake_vector_db = vector_db = MockVectorDb()

        vector_db_url = os.getenv("QDRANT_URL")
        vector_db_api_key = os.getenv("QDRANT_API_KEY")
        self.real_vector_db = vector_db = vector_database(vector_db_url, vector_db_api_key)

        self.embeddor = Embeddings()

        self.collection_name_og = "shopify_products"
        self.collection_name_test_one = "shopify_products-latest"

    def test_upsert_points(self, collection_name: str, points: list[PointStruct]) -> DbResponse | None:
        print("="*60)
        print("STARTING AN INTEGRATION TEST FOR UPSERTING VECTOR DB POINTS\n\n")
        print(f"Test Description: {points_tests["test_1"]["description"]}")

        points = points_tests["test_1"]["points"]

        db_response = self.real_vector_db.upsert_points(collection_name=self.collection_name_og, points=points)
        assert(db_response is not None)
        assert(db_response.error is None)
        assert(db_response.records_inserted == len(points))

    def test_search_points(self):
        print("="*60)
        print("STARTING AN INTEGRATION TEST FOR SEARCHING POITNS OUT OF THE DATABASE")

        try:
            with open("singe_document_embed.json", "r") as f:
                data = json.load(f)
                print("Data returned successfully")

        except Exception as e:
            print(f"File not read: {e}")
            print(f"Current wd: {os.getcwd()}")
            return

        text_that_got_embedded = data["text"]
        embedding = data["embed"]

        print(f"Embedded -> {text_that_got_embedded}")
        print(f"Embed -> {embedding[:10]}")

        k = 3

        search_points_result = self.real_vector_db.search_points(collection_name=self.collection_name_og, query_vector=embedding, k=k)
        print(f"Response Type: {type(search_points_result)}")
        # print(f"Dir: {dir(search_points_result)}")
        assert(len(search_points_result) == k)
        assert(payload.get("payload", {}) is not None for payload in search_points_result)

        for point in search_points_result:
            # could set up a struct and bind the payload
            try:
                payload = point.payload
                if not payload:
                    print(f"Payload not found in point")
                    continue
                print(f"Type Payload: {type(payload)}\n\n")
                
                print(f"Id: {payload["id"]}")
                print(f"Title: {payload["title"]}")
            except AttributeError or TypeError as a:
                print(f"Dir Of Attribute Error: {dir(point)}")
                print(f"Error Looping Through Points: {e}\n\n{traceback.format_exc()}")
                return
            except Exception as e:
                print(f"Error Looping Through Points: {e}\n\n{traceback.format_exc()}")
                return

    def test_creating_index_on_a_collection(self):
        """
        Testing
        1) Creating a collection
        2) Putting an index in that collection
        3) deleting the collection
        """
        print("="*60)
        print("Starting ", inspect.stack()[0][3])
        collection_name = "shopify_products-latest"
        collection_created = self.real_vector_db.create_collection(
            collection_name=collection_name, 
            index_payload=True, 
            index_wanted="vendor")
        assert collection_created

        #time.sleep(15)
        #deleted = self.real_vector_db.delete_collection(collection_name=collection_name)
        #assert deleted
        print("Completed ", inspect.stack()[0][3])

    def test_searches_for_product_names(self):
        """
        A test gets the result of a vetor search based on product name when the input vector is {brand name} {product name}
        Results should be something like 80% similarity
        """
        # From the embeddings test script we can save embeds to a json file
        # We can gitignore them
        try:
            with open("embed_data/product_names_embedded.json", encoding="utf-8") as data:
                names_and_vectors = json.load(data)
                print(f"Type Of Loaded In Data: {type(names_and_vectors)}")


        except FileNotFoundError as f:
            print(f"ERROR: {f}")
            print(os.getcwd())

        first_key = list(names_and_vectors.keys())[0]
        first_value = list(names_and_vectors.values())[0]
        print("Key Getting Result For: ", first_key)
        # A test  that shows a the response to a singular vector search
        # Print the results of what came back

        search_points_result = self.real_vector_db.search_points(
            collection_name=self.collection_name_og,
            query_vector=first_value, 
            k=10)

        print("Type: ", type(search_points_result))
        for result in search_points_result:
            print()
            print(result)
            print()

    def test_search_brand_and_product(self):
        """
        Searching by brand and product without a filter
        """
        print("="*60)
        print("STARTING: ", inspect.stack()[0][3])

        search_string = "Vitamin D3"
        search_document = self.embeddor.embed_documents([search_string])

        result_documents = self.real_vector_db.search_points(
            collection_name=self.collection_name_test_one,
            query_vector=search_document[0],
            k=10)

        for result in result_documents:
            print()
            print(result)
            print()


    def test_search_brand_and_product_with_filter(self):
        """
        Searching by brand and product as the name, with a filter to the brand
        Analysing edge case where your brand name actually changes in an Ai re-do, this could be a problem

        Single test to check the result querying the db
        """

        real_product_title = "A.Vogel Liver Support"
        print("="*60)
        print("Searching vector db for: ", real_product_title)
        mock_refined_product_title = "A.Vogel Liver Support Capsules"
        print("Testing Query String: ", mock_refined_product_title)

        documents_needing_embed = [mock_refined_product_title]

        result_embed = self.embeddor.embed_documents(documents=documents_needing_embed)[0]

        vector_filter = VectorFilter(
            key = "vendor",
            value = "A.Vogel"
        )

        search_points_result = self.real_vector_db.search_points(
            collection_name=self.collection_name_test_one, 
            query_vector=result_embed, 
            vector_filter=vector_filter)

        print("Type: ", type(search_points_result))
        for result in search_points_result:
            print()
            print(result)
            print()

    def test_multiple_vector_searches(self):
        """
        Testing a suite of documents

        As part of the product generation agent that documents results of searching documents
        """

        print("="*60)
        print("STARTING ", inspect.stack()[0][3])

        tests = [
            {
                "test_document": "2Die4 Live Foods Activated Organic Almonds 500g",
                "real_document": "2Die4 Live Foods Activated Organic Almonds",
                "description": "A different product with the similar naming conventions until the type of nut"
            },
            {
                "test_document": "A.Vogel Echinacea Forte",
                "real_document": "A.Vogel Echinacea Toothpaste",
                "description": "Different products that are different until the end word"
            },
            {
                "test_document": "Absolute Essential Certified Organic Immune Care Essential Oil Blend",
                "real_document": "Absolute Essential Certified Organic Inhale Essential Oil Blend",
                "description": "Different Oil blend mid name"
            },
            {
                "test_document": "Activated Probiotics Biome Eczema Probiotics",
                "real_document": "Activated Probiotics Biome Eczema Probiotic",
                "description": "Changed the product name to plurals"
            },
            {
                "test_document": "Micronutrition Vitamin D3 2000IU",
                "real_document": "Micronutrition Vitamin D3 1000IU",
                "description": "A concrete different product stores might want, although a varaint structure can achieved here"
            },
        ]

        for test in tests:
            # Loop through the tests
            test_document = test["test_document"]
            real_document = test["real_document"]
            vector = self.embeddor.embed_documents([test_document])
            return_documents = self.real_vector_db.search_points(
                collection_name=self.collection_name_test_one, 
                query_vector=vector[0], 
                k=10) 
            
            found = False
            for return_document in return_documents:
                # Loop through the returned results as a similarity search to the test_documetn
                payload = return_document.payload
                title = payload["title"]

                if title == real_document:
                    # title is equal to the document we wanna test for 
                    # print the result
                    found = True
                    test["score"] = return_document.score
                    print(json.dumps(test, indent=3))
            
            if not found:
                logging.warning("%s couldnt be found when looking for %s", real_document, test_document)
# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# -------------------------------------------------------------------------

if __name__ == "__main__":
    test_interface = integration_tests()
    # test_interface.invoke_embeddings_text()
    # test_interface.test_invoke_embeddings_documents()
    #test_interface.test_creating_index_on_a_collection()
    # test_interface.test_making_shopify_into_qdrant_points()
    # test_interface.test_adding_to_database()
    # test_interface.test_search_points()
    #test_interface.test_searches_for_product_names()
    #test_interface.test_search_brand_and_product()
    test_interface.test_multiple_vector_searches()