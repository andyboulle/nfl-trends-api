from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from app.database.connection import get_connection
from app.models.email_subscription import EmailSubscription
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/email-subscriptions",
    tags=["email-subscriptions"]
)

class EmailSubscriptionRequest(BaseModel):
    email: str
    
    @validator('email')
    def validate_email(cls, v):
        if not v or not v.strip():
            raise ValueError('Email address is required')
        
        # Basic email validation pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.strip()):
            raise ValueError('Please enter a valid email address')
        
        return v.strip().lower()

class NewsletterRequest(BaseModel):
    subject: str
    intro_text: Optional[str] = None
    featured_trends: Optional[List[Dict[str, Any]]] = None
    upcoming_games: Optional[List[Dict[str, Any]]] = None
    custom_content: Optional[str] = None
    
    @validator('subject')
    def validate_subject(cls, v):
        if not v or not v.strip():
            raise ValueError('Subject is required')
        return v.strip()

@router.post("/subscribe")
def subscribe_email(subscription_request: EmailSubscriptionRequest, db: Session = Depends(get_connection)):
    """
    Subscribe an email address to the newsletter.
    """
    try:
        # Check if email already exists
        existing_subscription = db.query(EmailSubscription).filter(
            EmailSubscription.email == subscription_request.email
        ).first()
        
        if existing_subscription:
            if existing_subscription.is_active:
                raise HTTPException(
                    status_code=409,
                    detail="This email address is already subscribed to our newsletter"
                )
            else:
                # Reactivate existing subscription
                existing_subscription.is_active = True
                existing_subscription.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing_subscription)
                return {
                    "message": "Successfully resubscribed to newsletter",
                    "email": existing_subscription.email,
                    "subscription_date": existing_subscription.subscription_date.isoformat()
                }
        
        # Create new subscription
        new_subscription = EmailSubscription(
            email=subscription_request.email,
            subscription_date=datetime.utcnow(),
            is_active=True
        )
        
        db.add(new_subscription)
        db.commit()
        db.refresh(new_subscription)
        
        logger.info(f"New email subscription: {subscription_request.email}")
        
        return {
            "message": "Successfully subscribed to newsletter",
            "email": new_subscription.email,
            "subscription_date": new_subscription.subscription_date.isoformat()
        }
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This email address is already subscribed to our newsletter"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in subscribe_email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again."
        )

@router.post("/unsubscribe")
def unsubscribe_email(subscription_request: EmailSubscriptionRequest, db: Session = Depends(get_connection)):
    """
    Unsubscribe an email address from the newsletter.
    """
    try:
        # Find the subscription
        subscription = db.query(EmailSubscription).filter(
            EmailSubscription.email == subscription_request.email
        ).first()
        
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="Email address not found in our subscription list"
            )
        
        if not subscription.is_active:
            return {
                "message": "Email address is already unsubscribed",
                "email": subscription.email
            }
        
        # Deactivate subscription
        subscription.is_active = False
        subscription.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Email unsubscribed: {subscription_request.email}")
        
        return {
            "message": "Successfully unsubscribed from newsletter",
            "email": subscription.email
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in unsubscribe_email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again."
        )

@router.get("/subscriptions/count")
def get_subscription_count(db: Session = Depends(get_connection)):
    """
    Get the total count of active subscriptions.
    """
    try:
        count = db.query(EmailSubscription).filter(EmailSubscription.is_active == True).count()
        
        return {
            "active_subscriptions": count,
            "message": f"Currently {count} active subscribers"
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in get_subscription_count: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving subscription count"
        )

@router.post("/newsletter/send")
def send_newsletter_to_all(newsletter: NewsletterRequest):
    """
    Newsletters are now sent via the email processor script.
    This endpoint provides information about the newsletter process.
    """
    try:
        return {
            "message": "Newsletter sending is handled by the email processor script.",
            "instructions": "Run the email_processor.py script in the nfl-trends-email-service directory to send newsletters.",
            "subject": newsletter.subject,
            "script_location": "/path/to/nfl-trends-email-service/email_processor.py",
            "note": "The script connects directly to the database and sends emails to all active subscribers."
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in send_newsletter_to_all: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

@router.post("/newsletter/test")
def send_test_newsletter(newsletter: NewsletterRequest, test_email: EmailSubscriptionRequest):
    """
    Test newsletters are now sent via the email processor script.
    This endpoint provides information about testing.
    """
    try:
        return {
            "message": "Test newsletter sending is handled by the email processor script.",
            "instructions": "Modify the email_processor.py script to send to a specific test email address.",
            "test_email": test_email.email,
            "subject": newsletter.subject,
            "note": "Update the main() function in email_processor.py to send to your test email instead of all subscribers."
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in send_test_newsletter: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the test newsletter request."
        )

@router.get("/subscribers")
def get_all_subscribers(db: Session = Depends(get_connection)):
    """
    Get all subscribers (both active and inactive).
    """
    try:
        subscribers = db.query(EmailSubscription).all()
        
        subscriber_list = []
        for sub in subscribers:
            subscriber_list.append({
                "id": sub.id,
                "email": sub.email,
                "subscription_date": sub.subscription_date.isoformat(),
                "is_active": sub.is_active,
                "created_at": sub.created_at.isoformat(),
                "updated_at": sub.updated_at.isoformat()
            })
        
        active_count = sum(1 for sub in subscriber_list if sub["is_active"])
        inactive_count = len(subscriber_list) - active_count
        
        return {
            "subscribers": subscriber_list,
            "total_count": len(subscriber_list),
            "active_count": active_count,
            "inactive_count": inactive_count
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in get_all_subscribers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving subscribers"
        )

@router.get("/health")
def email_service_health(db: Session = Depends(get_connection)):
    """
    Check the health of the email subscription system.
    """
    try:
        # Test database connection by counting subscriptions
        count = db.query(EmailSubscription).count()
        
        return {
            "status": "healthy",
            "service": "email_subscriptions_direct_db",
            "database_connection": "ok",
            "total_subscriptions": count,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Email sending is handled by separate script processor"
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in email_service_health: {str(e)}")
        return {
            "status": "unhealthy",
            "error": "Database connection failed",
            "timestamp": datetime.utcnow().isoformat()
        }