import json
import logging
from typing import Protocol
import redis

class KV_DB(Protocol):
    def hget_data(self, database_name: str, key: str):
        ...

    def hset_data(self, database_name: str, key: str, data: dict):
        ...

class RedisDatabase:
    def __init__(self):
        port = 6379
        self.client = redis.Redis(host='localhost', port=port, db=0)
        logging.info(f"Started Redis Database on port {port}")

    def hget_data(self, database_name: str, key: str):
        return self.client.hget(name=database_name, key=key)

    def hset_data(self, database_name: str, key: str, data: dict):
        # cant be nested otherwise json.dumps
        return self.client.hset(name=database_name, key=key, value=json.dumps(data, default=str))

    def hdel_data(self, database_name: str, key: str):
        return self.client.hdel(database_name, key)