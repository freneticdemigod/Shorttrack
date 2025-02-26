
from fastapi import APIRouter, Depends, HTTPException, Body
from ..schemas import URLCreate
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..db import get_db
from .. import models
from .utils import generate_short_code  
from ..redis_conn import redis_client
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from ..db import get_db
from .. import models
from .utils import generate_short_code
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.post("/shorten")
def shorten_url(payload: URLCreate, db: Session = Depends(get_db)):
    """
    1) Generate a short_code (base62 or random string).
    2) Insert a new row in the `urls` table.
    3) Return the generated short_code or a full short URL to the client.
    """
    long_url = payload.long_url
    valid_url = str(long_url)

    
    if not valid_url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL format.")

    
    short_code = generate_short_code(valid_url)

    
    expire_at = datetime.now(timezone.utc) + timedelta(days=8)

    
    new_url = models.URL(short_code=short_code, long_url=valid_url,expire_at=expire_at)
    db.add(new_url)

    try:
        db.commit()       
    except IntegrityError:
        db.rollback()
        
        for _ in range(3):  
            short_code = generate_short_code(long_url)
            new_url.short_code = short_code
            try:
                db.commit()
                break  
            except IntegrityError:
                db.rollback()
        else:
            
            raise HTTPException(status_code=409, detail="Too many collisions.")

    db.refresh(new_url)

    
    redis_client.set(short_code, valid_url)

    
    return {
        "short_code": new_url.short_code,
        "long_url": new_url.long_url,
        "created_at": new_url.created_at,
        "expire_at":new_url.expire_at
    }

@router.get("/url/{short_code}")
def redirect_url(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    1) Look up short_code in the `urls` table.
    2) If found, log analytics (IP, User-Agent, etc.).
    3) Redirect to the long_url.
    4) If not found, raise 404.
    """

    cached_long_url = redis_client.get(short_code)
    if cached_long_url:
        long_url = cached_long_url
        print(f"\n REDIS LOOKUP FOUND: {long_url} \n")
    else:
        print("\n REDIS LOOKUP NOT FOUND \n")
        
        url_record = db.query(models.URL).filter_by(short_code=short_code).first()
        if not url_record:
            raise HTTPException(status_code=404, detail="Short code not found")

        
        if url_record.expire_at and url_record.expire_at < datetime.datetime.utcnow():
            raise HTTPException(status_code=410, detail="This link has expired")

        
        long_url = url_record.long_url
        redis_client.set(short_code, long_url)

    
    ip_address = request.client.host  
    user_agent = request.headers.get("user-agent", "")
    referrer = request.headers.get("referer", "")  
    
    analytics_entry = models.Analytics(
        short_code=short_code,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer,
        
    )
    print(analytics_entry)
    db.add(analytics_entry)
    db.commit()

    
    return RedirectResponse(url=long_url)
