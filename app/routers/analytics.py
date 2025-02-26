

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from user_agents import parse as ua_parse

from ..db import get_db
from .. import models
from .utils import geoLoc  

router = APIRouter()

@router.get("/analytics/{short_code}")
def get_analytics(
    short_code: str,
    group_by: str | None = Query(
        default=None, 
        description="Group by 'day' or 'week', else return last 10 raw records"
    ),
    db: Session = Depends(get_db)
):
    """
    1) If group_by is 'day' or 'week', return aggregated count for current day/week.
    2) Otherwise, return last 10 visits (plus geolocation & user-agent parsing).
    """

    
    url_record = db.query(models.URL).filter_by(short_code=short_code).first()
    if not url_record:
        raise HTTPException(status_code=404, detail="Short code not found")

    now = datetime.utcnow()

    
    if group_by in ["day", "week"]:
        if group_by == "day":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            total_clicks_today = db.query(func.count(models.Analytics.id)) \
                .filter(models.Analytics.short_code == short_code) \
                .filter(models.Analytics.clicked_at >= start_of_day) \
                .scalar()
            return {
                "short_code": short_code,
                "long_url": url_record.long_url,
                "group_by": "day",
                "start": start_of_day,
                "end": now,
                "total_clicks": total_clicks_today
            }

        elif group_by == "week":
            
            start_of_week = (now - timedelta(days=now.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            total_clicks_this_week = db.query(func.count(models.Analytics.id)) \
                .filter(models.Analytics.short_code == short_code) \
                .filter(models.Analytics.clicked_at >= start_of_week) \
                .scalar()
            return {
                "short_code": short_code,
                "long_url": url_record.long_url,
                "group_by": "week",
                "start": start_of_week,
                "end": now,
                "total_clicks": total_clicks_this_week
            }

    
    last_visits = (
        db.query(models.Analytics)
        .filter_by(short_code=short_code)
        .order_by(models.Analytics.clicked_at.desc())
        .limit(10)
        .all()
    )

    visits_data = []
    for visit in last_visits:
        
        parsed_ua = ua_parse(visit.user_agent or "")
        
        
        ip_str = str(visit.ip_address) if visit.ip_address else None

        
        geo_data = None
        if ip_str:
            geo_data = geoLoc(ip_str)

        
        visits_data.append({
            "clicked_at": visit.clicked_at,
            "ip_address": ip_str,
            "user_agent": str(parsed_ua),           
            "browser": parsed_ua.browser.family,
            "os": parsed_ua.os.family,
            "device": parsed_ua.device.family,
            "referrer": visit.referrer,

            
            "geo": geo_data  
        })

    return {
        "short_code": short_code,
        "long_url": url_record.long_url,
        "recent_visits": visits_data
    }
