import redis

redis_client = redis.Redis(
    host='redis-17453.c257.us-east-1-3.ec2.redns.redis-cloud.com',
    port=17453,
    decode_responses=True,
    username="default",
    password="L39WD21TagkTDgqVvH8elTrVW33HjExK",
)

def get_redis():
    return redis_client