import json
import datetime
import random
import structlog

from qdrant_client.models import PointStruct, ScoredPoint

from agents.infrastructure.vector_database.response_schema import DbResponse

logger = structlog.getLogger(__name__)

points_tests = {
    "test_1": {
        "description": "A successful test with random ints as the vector mock",
        "points": [
            PointStruct(
                id=i,
                vector=[random.randint(-3, 3) for _ in range(10)],
                payload={"id": random.random()}
            ) for i in range(5)
        ]
    }
}

class MockVectorDb:
    def __init__(self):
        self.points = []
        self.seen = {}
        self.upsert_call_count = 0

    def upsert_points(self, collection_name: str, points: list[PointStruct]) -> DbResponse | None:
        logger.debug("Called: MockVectorDb.upsert_points")
        self.points.extend(points)
        self.upsert_call_count += 1

        points_dict = [point.payload["id"] for point in points_tests["test_1"]["points"]]
        print(f"Points Dict In Upsert Function: {points_dict}")

        for idx, point in enumerate(points_tests["test_1"]["points"]):
            print(f"Starting Index {idx}")

            payload = point.payload
            assert(payload is not None)

            id_payload = payload.get("id", {})
            assert(id_payload is not None)
            assert(id_payload != "")
            print(f"ID Payload: {id_payload}\n")

            seen_before = self.seen.get(f"{id_payload}", {})
            if seen_before:
                print(f"ERROR: Idx {id_payload} has already been added\n\n")
                print(json.dumps(self.seen, indent=3))
                return None

            self.seen[id_payload] = 1

        # print(f"\n\n{json.dumps(self.seen, indent=3)}\n\n")

        print("MockVectorDb.upsert_points returned DbResponse")
        return DbResponse(
            records_inserted=len(points),
            collection_name=collection_name,
            time=datetime.datetime.now(),
            error=None,
            traceback=None
        )
    
    def search_points(self, collection_name: str, query_vector: list[float], k: int) -> list:
        # Note: collection_name and query_vector are unused in mock implementation
        # Return 10 hardcoded points with scores from 95 down to 30 for deterministic testing
        logger.debug(f"MockVectorDb.search_points returned {k} points")
        
        # Hardcoded scores: 10 points from 95.0 down to 30.0
        # Exact values for deterministic testing/assertions
        # Create for returning over/under threshold by input

        #---------------------------------------------------------------
        # To test both test cases
        # If the first index is greater than 0 we will say the first product returned is below 90 and visa versa
        #---------------------------------------------------------------
        if query_vector[0] < 0:
            mock_points = [
                ScoredPoint(
                    id=0,
                    score=95.0,
                    payload={"id": "mock_product_0", "title": "Mock Product 0"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=1,
                    score=87.77777777777777,
                    payload={"id": "mock_product_1", "title": "Mock Product 1"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=2,
                    score=80.55555555555556,
                    payload={"id": "mock_product_2", "title": "Mock Product 2"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=3,
                    score=73.33333333333333,
                    payload={"id": "mock_product_3", "title": "Mock Product 3"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=4,
                    score=66.11111111111111,
                    payload={"id": "mock_product_4", "title": "Mock Product 4"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=5,
                    score=58.888888888888886,
                    payload={"id": "mock_product_5", "title": "Mock Product 5"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=6,
                    score=51.666666666666664,
                    payload={"id": "mock_product_6", "title": "Mock Product 6"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=7,
                    score=44.44444444444444,
                    payload={"id": "mock_product_7", "title": "Mock Product 7"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=8,
                    score=37.22222222222222,
                    payload={"id": "mock_product_8", "title": "Mock Product 8"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=9,
                    score=30.0,
                    payload={"id": "mock_product_9", "title": "Mock Product 9"},
                    vector=[0.0] * 1536,
                    version=0
                ),
            ]
            return mock_points

        if query_vector[0] > 0:
            mock_points = [
                ScoredPoint(
                    id=0,
                    score=89.0,
                    payload={"id": "mock_product_0", "title": "Mock Product 0"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=1,
                    score=87.77777777777777,
                    payload={"id": "mock_product_1", "title": "Mock Product 1"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=2,
                    score=80.55555555555556,
                    payload={"id": "mock_product_2", "title": "Mock Product 2"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=3,
                    score=73.33333333333333,
                    payload={"id": "mock_product_3", "title": "Mock Product 3"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=4,
                    score=66.11111111111111,
                    payload={"id": "mock_product_4", "title": "Mock Product 4"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=5,
                    score=58.888888888888886,
                    payload={"id": "mock_product_5", "title": "Mock Product 5"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=6,
                    score=51.666666666666664,
                    payload={"id": "mock_product_6", "title": "Mock Product 6"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=7,
                    score=44.44444444444444,
                    payload={"id": "mock_product_7", "title": "Mock Product 7"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=8,
                    score=37.22222222222222,
                    payload={"id": "mock_product_8", "title": "Mock Product 8"},
                    vector=[0.0] * 1536,
                    version=0
                ),
                ScoredPoint(
                    id=9,
                    score=30.0,
                    payload={"id": "mock_product_9", "title": "Mock Product 9"},
                    vector=[0.0] * 1536,
                    version=0
                ),
            ]
            return mock_points
        