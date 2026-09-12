from app.infrastructure.redis.client import r


async def redis_check_user_rate_limit(
   
    key:str,
    
    limit:int,
    window:int
):
     """This function sets rate limit for users trying to create account or log into 
     the server """
     attempts = await r.incr(name=key,amount=1)
     if attempts == 1:
         await r.expire(name=key,time=window)
     return attempts <= limit 
async def redis_verification_attempt_limit(key:str,limit:int):
    attempts = await  r.incr(name=key,amount=1)
    
    return attempts <= limit 

async def redis_get_attempts_left(key:str,limit:int): 
    """This function is used to get attempts left for a particular key"""
    attempts_raw = await r.get(name=key)
    attempts = int(attempts_raw) if attempts_raw else 0
    attempts_left = limit - attempts
    return max(0,attempts_left)
 


     