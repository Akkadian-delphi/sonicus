#!/usr/bin/env python3
"""Simple test server without file watching to verify tenant middleware works"""

import sys
sys.path.append('.')

from fastapi import FastAPI
from app.core.tenant_middleware import TenantDetectionMiddleware
from app.db.session import get_db

# Create a simple FastAPI app
app = FastAPI(title="Tenant Test Server")

# Add the tenant detection middleware
app.add_middleware(TenantDetectionMiddleware)

@app.get("/api/v1/organizations/status")
async def get_organization_status():
    """Simple endpoint to test tenant detection"""
    return {"message": "Tenant middleware should populate this request"}

if __name__ == "__main__":
    import uvicorn
    print("Starting simple tenant test server on http://127.0.0.1:18101")
    uvicorn.run(app, host="127.0.0.1", port=18101, log_level="info", reload=False)
