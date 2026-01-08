import datetime
import time
import traceback
from redis import Redis
from client import RedisDatabase

job_id = "fdsauibeuw2358"

clean_data = {
    "completed": False,
    "time_sent": datetime.datetime.now()
}

class integrationtest:
    def __init__(self):
        self.db = RedisDatabase()

    def send_and_read_data(self):
        print("="*60)
        print("STARTING SEND")
        deleting_at_end = True
        
        try:
            database_name = "jobs:agent"
            added = self.db.hset_data(database_name=database_name, key=job_id, data=clean_data)

            print(f"Type Of Return Response: {type(added)}")
            print(f"Response: {added}")

            time.sleep(2)
            print("="*60)
            print("STARTING GET")

            job_data = self.db.get_data(database_name=database_name, key=job_id)

            print(f"Type Of job_data Response: {type(job_data)}")
            print(f"Job Data: {job_data}")
            
            if deleting_at_end:
                deleted = self.db.del_data(database_name=database_name, key=job_id)

                print(f"Type Of deleted Response: {type(job_data)}")
                print(f"Deleted: {deleted}")

        except Exception as e:
            print(f"Error: {e}")
            print(traceback.format_exc())


if __name__ == "__main__":
    it = integrationtest()
    it.send_and_read_data()