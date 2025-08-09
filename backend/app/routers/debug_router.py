"""
Debug router for testing database connections during HTTP requests
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, select
from app.db.session import get_db, SessionLocal
from app.models.organization import Organization
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/debug/db-test")
async def debug_database_connections(db: Session = Depends(get_db)):
    """
    Test database connections and schema setup within HTTP request context
    """
    results = {}
    
    # Test 1: Current session via dependency injection
    try:
        result = db.execute(text('SELECT current_schema()'))
        results['dependency_schema'] = result.scalar()
        
        result = db.execute(text('SELECT COUNT(*) FROM organizations'))
        results['dependency_count'] = result.scalar()
        
        # Test SQLAlchemy model
        stmt = select(Organization).limit(1)
        result = db.execute(stmt)
        org = result.scalar_one_or_none()
        results['dependency_model'] = str(org)
        
    except Exception as e:
        results['dependency_error'] = str(e)
    
    # Test 2: Direct SessionLocal
    session2 = SessionLocal()
    try:
        result = session2.execute(text('SELECT current_schema()'))
        results['direct_schema'] = result.scalar()
        
        result = session2.execute(text('SELECT COUNT(*) FROM organizations'))
        results['direct_count'] = result.scalar()
        
    except Exception as e:
        results['direct_error'] = str(e)
    finally:
        session2.close()
    
    return {"debug_results": results}


@router.post("/debug/simple-org-test")
async def debug_simple_organization_test(db: Session = Depends(get_db)):
    """
    Simple organization query test to isolate the issue
    """
    try:
        # The exact query that's failing in registration
        stmt = select(Organization).where(
            (Organization.domain == 'testcorp') |
            (Organization.custom_domain == 'testcorp.sonicus.com')
        )
        result = db.execute(stmt)
        existing_org = result.scalar_one_or_none()
        
        return {
            "success": True,
            "existing_org": str(existing_org),
            "message": "Query executed successfully"
        }
        
    except Exception as e:
        logger.error(f"Debug organization test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Query failed"
        }
