

import json
import pika
from fastapi import APIRouter, Depends, Request, HTTPException
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from ..db import get_db
from ..models import URL
from ..redis_conn import redis_client  

router = APIRouter()



RABBITMQ_HOST = "localhost"  
QUEUE_NAME = "analytics_queue"

@router.get("/{short_code}")
def redirect_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    
    cached_long_url = redis_client.get(short_code)
    if cached_long_url:
        url_record = db.query(URL).filter_by(short_code=short_code).first()
        if not url_record:
            raise HTTPException(status_code=404, detail="Short code not found")
        
        if url_record.expire_at and datetime.utcnow() > url_record.expire_at:
            raise HTTPException(status_code=410, detail="Link expired")

        long_url = cached_long_url
    else:
        url_record = db.query(URL).filter_by(short_code=short_code).first()
        if not url_record:
            raise HTTPException(status_code=404, detail="Short code not found")
        if url_record.expire_at and datetime.utcnow() > url_record.expire_at:
            raise HTTPException(status_code=410, detail="Link expired")
        long_url = url_record.long_url
        redis_client.set(short_code, long_url)

    
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "")
    referrer = request.headers.get("referer", "")

    message = {
        "short_code": short_code,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "referrer": referrer,
        "clicked_at": datetime.utcnow().isoformat(),
    }
    print(message)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST,credentials=pika.PlainCredentials('guest', 'guest')))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  
        )
    )
    connection.close()

    
    return RedirectResponse(url=long_url)
