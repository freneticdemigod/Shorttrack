
import pika, json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models import Analytics  
import os
from dotenv import load_dotenv

load_dotenv()  

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
QUEUE_NAME = os.getenv("QUEUE_NAME")

def callback(ch, method, properties, body):
    
    data = json.loads(body)
    session = SessionLocal()

    try:
        
        analytics_entry = Analytics(
            short_code=data["short_code"],
            ip_address=data["ip_address"],
            user_agent=data["user_agent"],
            referrer=data["referrer"],
            
            
        )
        
        session.add(analytics_entry)
        session.commit()

        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        
        session.rollback()
        print(f"Error processing message: {e}")
        

    finally:
        session.close()

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print("Worker is listening for analytics messages...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
