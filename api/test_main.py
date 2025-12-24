import asyncio
import datetime
import json
import time
from fastapi.testclient import TestClient

from main import create_app
from api.models.product_generation import PromptVariant, Variant, Option
from agents.infrastructure.shopify_api.product_schema import DraftResponse
from db.client import RedisDatabase

# Create mock data using the PromptVariant structure
mock_data = PromptVariant(
    brand_name="Optimum Nutrition",
    product_name="Gold Standard 100% Whey Protein",
    variants=[
        # Variant 1: 2lb Chocolate
        Variant(
            option_1=Option(option_name="Size", option_value="2 lb"),
            option_2=Option(option_name="Flavour", option_value="Chocolate"),
            sku=922001,
            barcode="0810095637971",
            price=49.95
        ),
        # Variant 2: 2lb Vanilla
        Variant(
            option_1=Option(option_name="Size", option_value="2 lb"),
            option_2=Option(option_name="Flavour", option_value="Vanilla"),
            sku=922002,
            barcode="0810095637972",
            price=49.95
        ),
        # Variant 3: 5lb Chocolate
        Variant(
            option_1=Option(option_name="Size", option_value="5 lb"),
            option_2=Option(option_name="Flavour", option_value="Chocolate"),
            sku=922003,
            barcode="0810095637973",
            price=89.95
        ),
        # Variant 4: 5lb Vanilla
        Variant(
            option_1=Option(option_name="Size", option_value="5 lb"),
            option_2=Option(option_name="Flavour", option_value="Vanilla"),
            sku=922004,
            barcode="0810095637974",
            price=89.95
        ),
        # Variant 5: 2lb Strawberry (with 3 options)
        Variant(
            option_1=Option(option_name="Size", option_value="2 lb"),
            option_2=Option(option_name="Flavour", option_value="Strawberry"),
            sku=922005,
            barcode="0810095637975",
            price=49.95
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
            option_1=Option(option_name="Size", option_value="2 lb"),
            option_2=Option(option_name="Flavour", option_value="Chocolate Peanut Butter"),
            sku=923001,
            barcode="0810095638001",
            price=54.95
        ),
        # Variant 2: 2lb Vanilla
        Variant(
            option_1=Option(option_name="Size", option_value="2 lb"),
            option_2=Option(option_name="Flavour", option_value="Vanilla"),
            sku=923002,
            barcode="0810095638002",
            price=54.95
        ),
        # Variant 3: 4lb Chocolate Peanut Butter
        Variant(
            option_1=Option(option_name="Size", option_value="4 lb"),
            option_2=Option(option_name="Flavour", option_value="Chocolate Peanut Butter"),
            sku=923003,
            barcode="0810095638003",
            price=89.95
        ),
        # Variant 4: 4lb Vanilla
        Variant(
            option_1=Option(option_name="Size", option_value="4 lb"),
            option_2=Option(option_name="Flavour", option_value="Vanilla"),
            sku=923004,
            barcode="0810095638004",
            price=89.95
        ),
        # Variant 5: 4lb Cookies & Cream (with 3 options)
        Variant(
            option_1=Option(option_name="Size", option_value="4 lb"),
            option_2=Option(option_name="Flavour", option_value="Cookies & Cream"),
            option_3=Option(option_name="Type", option_value="Premium"),
            sku=923005,
            barcode="0810095638005",
            price=94.95
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

    def hget_data(self, database_name: str, key: str):
        print("Called test redis hget_data")
        wanted_data = self.db.get(key, None)
        if wanted_data is None:
            raise Exception("Data not in redis")
        data = json.dumps(wanted_data).encode()

        print()
        print("*"*60)
        print("About To Return Data From  Fake hget_data")
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

    client = create_app(agent=fake_agent, job_database=fake_redis)

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

    print("Test succeded")

def test_getting_data():
    print("="*60)
    print("STARTING TEST GET A JOBS STATUS")

    test_app = create_app(agent=fake_agent(), job_database=fake_redis(), start_consumer=False)
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

            job_data = redis_db.hget_data("agent:jobs", key=request_id)
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

            job_data = redis_db.hget_data("agent:jobs", key=request_id_2)
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

if __name__ == "__main__":
    #test_read_main()
    #test_getting_data()
    #test_posting_to_agent()
    integration_test_post()
