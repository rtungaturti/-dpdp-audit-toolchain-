"""
FastAPI Application for DPDP Compliance Audit Toolchain
Deploy to Railway for API access
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# Import our modules
from udc import get_udc, configure_udc_from_json, DataSource
from vpc_scanner import get_vpc_scanner
from strands_agent import create_dpdp_agent

app = FastAPI(
    title="DPDP Compliance Audit API",
    description="API for DPDP Act compliance auditing (UDC + VPC Scanner)",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class DBConnectionRequest(BaseModel):
    database_type: str
    host: str
    port: int
    database: str
    username: str
    password: str

class VPCScanRequest(BaseModel):
    user_table: str
    age_column: str
    consent_column: Optional[str] = None
    parent_consent_column: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    source_name: str = "client_db"

# API Endpoints
@app.get("/")
def root():
    return {
        "service": "DPDP Compliance Audit Toolchain",
        "version": "1.0.0",
        "agents": ["Universal Data Connector (UDC)", "VPC Scanner"],
        "endpoints": [
            "POST /connect/database - Configure DB connection",
            "POST /query - Execute SQL query",
            "POST /vpc/scan - Run VPC compliance scan",
            "GET /vpc/report - Get latest VPC report",
            "GET /health - Health check"
        ]
    }

@app.post("/connect/database")
def connect_database(request: DBConnectionRequest):
    """Configure and connect to a database"""
    try:
        udc = get_udc()
        source = DataSource(
            name="client_db",
            source_type=request.database_type,
            host=request.host,
            port=request.port,
            database=request.database,
            username=request.username,
            password=request.password
        )
        udc.add_source(source)
        udc.connect()
        
        return {
            "status": "success",
            "message": f"Connected to {request.database_type} database '{request.database}'",
            "source": "client_db"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def execute_query(request: QueryRequest):
    """Execute a SQL query"""
    try:
        udc = get_udc()
        df = udc.query(request.source_name, request.query)
        
        return {
            "status": "success",
            "row_count": len(df),
            "data": df.head(100).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vpc/scan")
def run_vpc_scan(request: VPCScanRequest):
    """Run VPC compliance scan"""
    try:
        scanner = get_vpc_scanner()
        result = scanner.scan_database(
            source_name="client_db",
            user_table=request.user_table,
            age_column=request.age_column,
            consent_column=request.consent_column,
            parent_consent_column=request.parent_consent_column
        )
        
        return {
            "status": "success",
            "report": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vpc/report")
def get_vpc_report():
    """Get the latest VPC compliance report"""
    scanner = get_vpc_scanner()
    
    return {
        "total_child_records": len(scanner.child_records),
        "verified_consents": len(scanner.verified_consents),
        "missing_consents": len(scanner.missing_consents),
        "violations": len(scanner.violations),
        "compliant": len(scanner.missing_consents) == 0,
        "full_report": scanner.generate_report()
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    udc = get_udc()
    return {
        "status": "healthy",
        "udc_connected": udc.connected,
        "sources_configured": list(udc.sources.keys())
    }

# For local development
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)