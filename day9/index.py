import redis 
import json
from redis_client import  r



with open('day9/input.txt' , 'r') as f:
    for line in f:
        r.lpush('logs', line.strip())

print("Logs have been pushed to Redis list 'logs'.")

