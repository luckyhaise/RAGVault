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
     