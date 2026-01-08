import json
import structlog
from typing import Any, Protocol
import redis

logger = structlog.get_logger(__name__)

class KV_DB(Protocol):
    def get_data(self, database_name: str, key: str):
        ...

    def hset_data(self, database_name: str, key: str, data: dict):
        ...

class RedisDatabase:
    def __init__(self, host: str, port: int):
        self.client = redis.Redis(host=host, port=port, db=0)
        logger.info("Started Redis Database", port=port)

    def get_data(self, database_name: str, key: str):
        logger.debug("Called redis hget", database_name_called=database_name, key=key)
        return self.client.hget(name=database_name, key=key)

    def del_data(self, database_name: str, key: str):
        logger.debug("Called redis hdel", database_name_called=database_name, key=key)
        return self.client.hdel(database_name, key)

    def hset_data(self, database_name: str, key: str, data: dict):
        # cant be nested otherwise json.dumps
        logger.debug("Called redis hset", database_name_called=database_name, key=key, data=data)
        return self.client.hset(name=database_name, key=key, value=json.dumps(data, default=str))
