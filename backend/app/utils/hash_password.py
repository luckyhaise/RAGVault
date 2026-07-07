from argon2 import PasswordHasher


hasher = PasswordHasher()


def hash_password(password:str):
   hashed_password = hasher.hash(password=password)
   return hashed_password

def match_password(password:str,hashed_password:str):
 return hasher.verify(hash=hashed_password,password=password)
 

