import json
from queue import Queue

q = Queue()
with open("day2/bucket.json" , "r") as f:
    data = json.load(f)


for bucket in data["buckets"]:
    # print("Name is" , bucket["name"])
    # for key,value in bucket["tags"].items():
    #     print(f"  {key}: {value}")
    
    # for policy in bucket["policies"]:
    #     print("Type is " , policy["type"])

    if bucket["sizeGB"] > 50:
        q.put(bucket)

    today = data.NOW()

    


print("Buckets to be deleted are the")
while not q.empty():        
    item = q.get()        
    print(item["name"])