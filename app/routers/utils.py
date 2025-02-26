
import hashlib
import base64
import time
import requests
from dotenv import load_dotenv
import os

load_dotenv()

ACCESS_KEY = os.getenv("ACCESS_KEY")
GEO_LOC_API_URL = os.getenv("GEO_LOC_API_URL")

def generate_short_code(long_url: str, length: int = 6) -> str:
    """
    1) Optionally, append a random or time-based salt to the URL for uniqueness.
    2) MD5-hash the resulting string.
    3) Base64-encode the hash, then truncate to `length`.
    4) Return that as the short code.
    """
    
    salt = str(time.time_ns())  
    to_hash = long_url + salt

    
    hash_digest = hashlib.md5(to_hash.encode()).digest()

    
    code = base64.urlsafe_b64encode(hash_digest).decode('utf-8')

    
    short_code = code[:length]

    return short_code

def geoLoc(ip_address):
    url = f"{GEO_LOC_API_URL}/{ip_address}?access_key={ACCESS_KEY}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  
    except requests.exceptions.RequestException as e:
        
        print(f"Error fetching geolocation data: {e}")
        return None

    data = response.json()
    print("Geoloc Data retrieved successfully")
    return data