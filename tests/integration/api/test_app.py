import asyncio
import datetime
import json
import time
from fastapi.testclient import TestClient
import uvicorn
from fastapi import FastAPI, Request, Response
from shopify import Product

from product_agent.api.app import create_app
from product_agent.infrastructure.llm.prompts import PromptVariant
from product_agent.infrastructure.shopify.schemas import DraftResponse, Variant, Option, InventoryAtStores, ShopifyProductSchema
from product_agent.db.redis import RedisDatabase

# Create mock data using the PromptVariant structure
mock_data = PromptVariant(
    brand_name="Optimum Nutrition",
    product_name="Gold Standard 100% Whey Protein",
    variants=[
        # Variant 1: 2lb Chocolate
        Variant(
            option1_value=Option(option_name="Size", option_value="2 lb"),
            option2_value=Option(option_name="Flavour", option_value="Chocolate"),
            sku=922001,
            barcode="0810095637971",
            price=49.95,
            product_weight=0.91,
            inventory_at_stores=InventoryAtStores(city=100, south_melbourne=100)
        ),
        # Variant 2: 2lb Vanilla
        Variant(
            option1_value=Option(option_name="Size", option_value="2 lb"),
            option2_value=Option(option_name="Flavour", option_value="Vanilla"),
            sku=922002,
            barcode="0810095637972",
            price=49.95,
            product_weight=0.91,
            inventory_at_stores=InventoryAtStores(city=100, south_melbourne=100)
        ),
        # Variant 3: 5lb Chocolate
        Variant(
            option1_value=Option(option_name="Size", option_value="5 lb"),
            option2_value=Option(option_name="Flavour", option_value="Chocolate"),
            sku=922003,
            barcode="0810095637973",
            price=89.95,
            product_weight=2.27,
            inventory_at_stores=InventoryAtStores(city=100, south_melbourne=100)
        ),
        # Variant 4: 5lb Vanilla
        Variant(
            option1_value=Option(option_name="Size", option_value="5 lb"),
            option2_value=Option(option_name="Flavour", option_value="Vanilla"),
            sku=922004,
            barcode="0810095637974",
            price=89.95,
            product_weight=2.27,
            inventory_at_stores=InventoryAtStores(city=100, south_melbourne=100)
        ),
        # Variant 5: 2lb Strawberry
        Variant(
            option1_value=Option(option_name="Size", option_value="2 lb"),
            option2_value=Option(option_name="Flavour", option_value="Strawberry"),
            sku=922005,
            barcode="0810095637975",
            price=49.95,
            product_weight=0.91,
            inventory_at_stores=InventoryAtStores(city=100, south_melbourne=100)
        ),
    ]
)

# Second mock data - different product
mock_data_2 = PromptVariant(
    brand_name="MuscleTech",
    product_name="Nitro-Tech Whey Gold",
    variants=[
        # Variant 1: 2lb Chocolate Peanut Butter
        Variant(
            option1_value=Option(option_name="Size", option_value="2 lb"),
            option2_value=Option(option_name="Flavour", option_value="Chocolate Peanut Butter"),
            sku=923001,
            barcode="0810095638001",
            price=54.95,
            product_weight=0.91,
            inventory_at_stores=InventoryAtStores(city=50, south_melbourne=50)
        ),
        # Variant 2: 2lb Vanilla
        Variant(
            option1_value=Option(option_name="Size", option_value="2 lb"),
            option2_value=Option(option_name="Flavour", option_value="Vanilla"),
            sku=923002,
            barcode="0810095638002",
            price=54.95,
            product_weight=0.91,
            inventory_at_stores=InventoryAtStores(city=50, south_melbourne=50)
        ),
        # Variant 3: 4lb Chocolate Peanut Butter
        Variant(
            option1_value=Option(option_name="Size", option_value="4 lb"),
            option2_value=Option(option_name="Flavour", option_value="Chocolate Peanut Butter"),
            sku=923003,
            barcode="0810095638003",
            price=89.95,
            product_weight=1.81,
            inventory_at_stores=InventoryAtStores(city=50, south_melbourne=50)
        ),
        # Variant 4: 4lb Vanilla
        Variant(
            option1_value=Option(option_name="Size", option_value="4 lb"),
            option2_value=Option(option_name="Flavour", option_value="Vanilla"),
            sku=923004,
            barcode="0810095638004",
            price=89.95,
            product_weight=1.81,
            inventory_at_stores=InventoryAtStores(city=50, south_melbourne=50)
        ),
        # Variant 5: 4lb Cookies & Cream (with 3 options)
        Variant(
            option1_value=Option(option_name="Size", option_value="4 lb"),
            option2_value=Option(option_name="Flavour", option_value="Cookies & Cream"),
            sku=923005,
            barcode="0810095638005",
            price=94.95,
            product_weight=1.81,
            inventory_at_stores=InventoryAtStores(city=50, south_melbourne=50)
        )
    ]
)

class FakeAgent:
    """A class replicating our Ai agent"""
    def __init__(self):
        pass

    async def service_workflow(self, query: str):
        print("Called the service workflow from the fake agent")
        await asyncio.sleep(15)
        print("Processing for 15 seconds")
        await asyncio.sleep(15)
        print("Processing for 30 seconds")

        return DraftResponse(title="Ty Lu", url="www.shopify.com.au/luehty", time_of_comepletion=datetime.datetime.now(), status_code=200)

class FakeRedis():
    """A class replicating redis database"""
    def __init__(self):
        self.db = {}

    def get_data(self, database_name: str, key: str):
        print("Called test redis get_data")
        wanted_data = self.db.get(key, None)
        if wanted_data is None:
            raise Exception("Data not in redis")
        data = json.dumps(wanted_data).encode()

        print()
        print("*"*60)
        print("About To Return Data From  Fake get_data")
        print(f"Data's Type: {type(data)}")
        print(f"Data: {data}")
        print()

        return data

    def hset_data(self, database_name: str, key: str, data: dict):
        print("Called test redis hset_data")
        self.db[key] = data
        return 1

    def print_internal_db(self):
        print(json.dumps(self.db, indent=3, default=str))

    def return_internal_db(self) -> dict:
        return self.db 

def test_read_main():
    print("="*60)
    print("STARTING TEST READ FROM MAIN ROOT")

    client = create_app(agent=FakeAgent(), job_database=FakeRedis())

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

    print("Test succeded")

def test_getting_data():
    print("="*60)
    print("STARTING TEST GET A JOBS STATUS")

    test_app = create_app(agent=FakeAgent(), job_database=FakeAgent(), start_consumer=False)
    with TestClient(test_app) as client:
        response = client.get("/internal/product_generation/325492afdsa")
        assert response is not None
        print("Response: ", response)
        assert response.status_code == 200
        
        print(f"Response's type: {type(response)}")
        print("Response: ", response.json())

    
    print("Test Succeded")

def test_posting_to_agent():
    print("="*60)
    print("STARTING POST TO AGENT")

    mock_queue = asyncio.Queue()

    fake_agent = FakeAgent()
    fake_redis = FakeRedis()

    test_app = create_app(agent=fake_agent, job_database=fake_redis, agent_job_queue=mock_queue, start_consumer=True)
    print("Created Mock App")

    with TestClient(test_app) as client:
        url = "/internal/product_generation"
        content = mock_data.model_dump()

        print(f"Posting mock data: {json.dumps(content, indent=2)}")
        response_one = client.post(url=url, json=content)
        response_two = client.post(url=url, json=content)
        response_three = client.post(url=url, json=content)

        size_of_queue = mock_queue.qsize()
        print(f"At Start -> Size Of Queue: {size_of_queue}")
        assert size_of_queue == 2

        print(f"Response status: {response_one.status_code}")
        print(f"Response Type: {type(response_one)}")
        print(f"Response Content Type: {type(response_one.content)}")
        print(f"Response: {response_two.json()}")
        assert response_three.status_code in [200, 202]

        total_run_time = 0
        while mock_queue.qsize() > 0:
            print(f"Current size of queue: {mock_queue.qsize()}")
            if total_run_time > 340:
                raise Exception("Total Expected Runtime Exceeded")

            time.sleep(15)
            total_run_time += 15

    # need to assert the final json schema in this test 
    # Whatever the database should hold assert it
    # check responses one two and threes job id and query        
    fake_result = fake_redis.return_internal_db()
    response_one_dict = json.loads(response_one.content)
    req_id = response_one_dict.get("request_id", None)
    if req_id is None:
        raise Exception("Req Id is none")

    job_data = fake_result.get(req_id, None)
    assert job_data is not None

    # job_data should be a success dictionary
    job_completed = job_data.get("completed", None)
    url = job_data.get("url_of_job", None)
    assert job_completed is not None 
    assert url is not None 
    
    fake_redis.print_internal_db()

def integration_test_post():
    """An integration test that tests once leaves the queue idle and then sends another request"""
    # Create redis instance here for more usability
    redis_db = RedisDatabase()
    test_app = create_app(job_database=redis_db)
    with TestClient(test_app) as client:
        url = "/internal/product_generation"
        content = mock_data.model_dump()
        assert isinstance(content, dict)
        response_post_one = client.post(url=url, json=content)
        assert response_post_one is not None

        request_id_dict = json.loads(response_post_one.content)
        request_id = request_id_dict.get("request_id", None)
        assert request_id is not None

        run_number = 0
        while True:
            run_number += 1

            job_data = redis_db.get_data("agent:jobs", key=request_id)
            job_data_dict = json.loads(job_data)
            assert job_data is not None

            if run_number == 15:
                # Timeout metric
                print("Run 15 Concluded")
                print("Job Data", job_data)
            if run_number == 1:
                print(f"job_data Type: {type(job_data)}")
                print(f"job_data Data: {job_data}")

            completed = job_data_dict.get("completed", None)
            print(f"Has The Task Completed: {completed}")
            if completed:
                job_url = job_data_dict["url_of_job"]
                print()
                print("*"*60)
                print("JOB 1 COMPLETED")
                print(f"Url To Check: {job_url}")
                break
            
            print(f"Job not completed on iter {run_number}")
            time.sleep(12) 
            
            # Add timeout protection
            if run_number > 20: 
                raise Exception(f"Test timeout: Job {request_id} did not complete after {run_number} iterations")

        # pretend like theres no requests coming in for a bit
        print("Sleeping, no requests for a little bit simulation")
        time.sleep(15)  # Use time.sleep, not asyncio.sleep

        content_2 = mock_data_2.model_dump()
        resp_2 = client.post(url=url, json=content_2)
        assert resp_2 is not None

        resp_2_dict = json.loads(resp_2.content)
        request_id_2 = resp_2_dict.get("request_id", None)
        assert request_id_2 is not None

        run_number_2 = 0
        while True:
            run_number_2 += 1

            job_data = redis_db.get_data("agent:jobs", key=request_id_2)
            job_data_dict = json.loads(job_data)
            assert job_data is not None

            if run_number_2 == 15:
                print("Run 15 Concluded")
                print("Job Data", job_data)
            if run_number_2 == 1:
                print(f"job_data Type: {type(job_data)}")
                print(f"job_data Data: {job_data}")

            completed = job_data_dict.get("completed", None)
            print(f"Has The Task Completed: {completed}")
            if completed:
                url = job_data_dict["url_of_job"]
                print()
                print("*"*60)
                print("JOB 2 COMPLETED")
                print(f"Url To Check: {url}")
                break
            
            print(f"Job not completed on iter {run_number_2}")
            time.sleep(12)  # Use time.sleep, not asyncio.sleep in sync function
            
            # Add timeout protection
            if run_number_2 > 100:  # Max 100 iterations (20 minutes at 12 seconds each)
                raise Exception(f"Test timeout: Job {request_id_2} did not complete after {run_number_2} iterations")

def test_sending_same_time():
    """A test to simulate multiple request handled async"""
    redis_db = RedisDatabase()
    test_app = create_app(job_database=redis_db)
    with TestClient(test_app) as client:
        first_product = mock_data.model_dump()
        second_product = mock_data_2.model_dump()

        url = "/internal/product_generation"
        response_one = client.post(url=url, json=first_product, timeout=5000)
        response_two = client.post(url=url, json=second_product, timeout=5000)

        print("Response One", response_one.json())
        print("Response Two", response_two.json())

        resp_2_dict = response_two.json()
        resp_2_req_id = resp_2_dict["request_id"]

        while True:
            # Dont shut function down while task is executing
            time.sleep(20)
            job_status = redis_db.get_data(database_name="agent:jobs", key=resp_2_req_id)

            job_status_dict = json.loads(job_status)
            completed = job_status_dict.get("completed")
            if completed:
                break

        print("Completed all tasks")

def test_exposing_webhook_for_shopify_webhook():
    # an integration test to expose a real port
    # used for a small window
    # go to shopify and give them your url that is forwarded to this port
    app = FastAPI()

    @app.get("/")
    async def greet():
        print("Recieved get request")
        return {"Hello": "World"}

    @app.post("/webhook-test")
    async def get_payload_from_webhook(request: Request):
        print("="*60)
        print("Printing Request From Shopify")

        body = await request.json()
        print(f"\nRequest JSON: \n{json.dumps(body, indent=2)}")

        print(f"\nRequest Headers: {request.headers}")
        print(f"\nRequest url: {request.url}")

    port = 8080
    print(f"Starting api on port {port}")
    uvicorn.run(app=app, host="127.0.0.1", port=port)

def test_exposing_webhook_and_send_to_queue():
    app = FastAPI()

    @app.post("/webhook-test")
    async def get_payload_from_webhook(request: Request):
        print("="*60)
        print("Returned a webhook response")
        
        try:
            response = await request.json()
            product_coming_in = ShopifyProductSchema(**response)
            print(f"Successfully obtained {product_coming_in.title}")

            print(f"Response In Model Format: \n\n{product_coming_in.model_dump_json(indent=3)}")

            return {"response:": "recieved"}

        except Exception as e:
            print("Error: ", e)
            print(json.dumps(request.json(), indent=3))

    port=8080
    uvicorn.run(app=app, host="127.0.0.1", port=port)

if __name__ == "__main__":
    #test_read_main()
    #test_getting_data()
    #test_posting_to_agent()
    #integration_test_post()
    #test_sending_same_time()
    #test_exposing_webhook_for_shopify_webhook()
    test_exposing_webhook_and_send_to_queue()
