import json
import datetime
import random
import structlog

from qdrant_client.models import PointStruct

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
        print("="*60)
        print("Called: MockVectorDb.upsert_points")
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
        # Simple fake: return first k points
        logger.debug(f"MockVectorDb.search_points returned {k} points")
        return self.points[:k]