from redis_client import r

logs = r.lrange('logs' , 0,-1)
logs=logs[::-1]
for item in logs:
    print(item.strip())