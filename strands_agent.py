"""
Strands Agent with UDC and VPC Scanner tools
Uses GROQ Llama 3.3 via LiteLLM
"""

import os
import json
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models.litellm import LiteLLMModel

# Load environment variables
load_dotenv()

# Import our modules
from udc import get_udc, configure_udc_from_json, DataSource
from vpc_scanner import get_vpc_scanner

# Suppress HF symlink warning (optional)
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

# ============================================
# Tool 1: Universal Data Connector (UDC)
# ============================================

@tool
def configure_database_connection(database_type: str, host: str, port: int, 
                                   database: str, username: str, password: str) -> str:
    """
    Configure a database connection for the Universal Data Connector.
    Use this before running any database queries.
    
    Args:
        database_type: 'mysql' or 'postgresql'
        host: Database host address
        port: Database port (3306 for MySQL, 5432 for PostgreSQL)
        database: Database name
        username: Database username
        password: Database password
    """
    try:
        udc = get_udc()
        source = DataSource(
            name="client_db",
            source_type=database_type,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password
        )
        udc.add_source(source)
        udc.connect()
        return f"✅ Successfully connected to {database_type} database '{database}' at {host}:{port}"
    except Exception as e:
        return f"❌ Failed to connect: {str(e)}"

@tool
def execute_database_query(query: str, source_name: str = "client_db") -> str:
    """
    Execute a SQL query on the configured database.
    Use this after configuring the database connection.
    
    Args:
        query: The SQL query to execute (SELECT statements only for safety)
        source_name: Name of the data source (default: 'client_db')
    """
    try:
        # Safety check - only allow SELECT queries in this version
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            return "⚠️ For safety, only SELECT queries are allowed in this version."
        
        udc = get_udc()
        df = udc.query(source_name, query)
        
        if df.empty:
            return "Query returned no results."
        
        # Convert to readable format
        result = f"✅ Query returned {len(df)} rows\n\n"
        result += df.head(20).to_string()
        
        if len(df) > 20:
            result += f"\n\n... and {len(df) - 20} more rows"
        
        return result
    except Exception as e:
        return f"❌ Query failed: {str(e)}"

@tool
def list_database_tables(source_name: str = "client_db") -> str:
    """
    List all tables in the connected database.
    
    Args:
        source_name: Name of the data source (default: 'client_db')
    """
    try:
        udc = get_udc()
        tables = udc.list_tables(source_name)
        
        if not tables:
            return "No tables found in the database."
        
        result = f"📋 Found {len(tables)} tables:\n\n"
        for table in tables:
            result += f"- {table}\n"
        
        return result
    except Exception as e:
        return f"❌ Failed to list tables: {str(e)}"

# ============================================
# Tool 2: VPC Scanner (Verifiable Parental Consent)
# ============================================

@tool
def scan_child_data(user_table: str, age_column: str, 
                    consent_column: str = None,
                    parent_consent_column: str = None) -> str:
    """
    Scan database for child data and verify parental consent compliance.
    Under DPDP Section 9, children under 18 require verifiable parental consent.
    
    Args:
        user_table: Name of the table containing user data
        age_column: Column name that stores age or date of birth
        consent_column: Column name that stores consent status (optional)
        parent_consent_column: Column name for parental consent flag (optional)
    """
    try:
        scanner = get_vpc_scanner()
        result = scanner.scan_database(
            source_name="client_db",
            user_table=user_table,
            age_column=age_column,
            consent_column=consent_column,
            parent_consent_column=parent_consent_column
        )
        return result
    except Exception as e:
        return f"❌ VPC scan failed: {str(e)}"

@tool
def get_vpc_compliance_summary() -> str:
    """
    Get a summary of the last VPC scan results.
    """
    scanner = get_vpc_scanner()
    
    summary = f"""## VPC Compliance Summary

- Total Child Records: {len(scanner.child_records)}
- Verified Consents: {len(scanner.verified_consents)}
- Missing Consents: {len(scanner.missing_consents)}
- Violations: {len(scanner.violations)}

**Overall Status**: {'✅ COMPLIANT' if len(scanner.missing_consents) == 0 else '❌ NON-COMPLIANT'}
"""
    return summary

# ============================================
# Configure and Create the Agent
# ============================================

def create_dpdp_agent():
    """Create and return the DPDP compliance agent"""
    
    # Configure GROQ model via LiteLLM
    model = LiteLLMModel(
        model_id="groq/llama-3.3-70b-versatile",
        params={
            "max_tokens": 2000,
            "temperature": 0.3,  # Lower for factual compliance
            "stream": False,
        },
        client_args={
            "api_key": os.getenv("GROQ_API_KEY"),
        }
    )
    
    # Create agent with both tools
    agent = Agent(
        model=model,
        tools=[
            configure_database_connection,
            execute_database_query,
            list_database_tables,
            scan_child_data,
            get_vpc_compliance_summary
        ],
        system_prompt="""You are a DPDP (Digital Personal Data Protection Act) compliance assistant specializing in:
1. Connecting to databases via Universal Data Connector
2. Scanning for child data and verifying parental consent (Section 9)
3. Identifying compliance gaps

**Available Tools:**
- configure_database_connection: Set up database connection
- execute_database_query: Run SQL queries
- list_database_tables: See available tables
- scan_child_data: Check for child data and parental consent
- get_vpc_compliance_summary: Get compliance status

**Guidelines:**
- Always help users configure database connection first
- Explain DPDP requirements when relevant
- Generate clear compliance reports
- Be professional and factual
"""
    )
    
    return agent


# ============================================
# Quick Test Function
# ============================================

def test_agent():
    """Test the agent with sample queries"""
    
    agent = create_dpdp_agent()
    
    print("🤖 DPDP Compliance Agent Ready")
    print("=" * 50)
    print("\nExample queries you can try:")
    print("1. 'Help me connect to a MySQL database'")
    print("2. 'List all tables in my database'")
    print("3. 'Run a SELECT query to see users'")
    print("4. 'Scan for child data in the users table'")
    print("\n" + "=" * 50)
    
    # Uncomment to test with actual queries
    # response = agent("What DPDP sections cover children's data?")
    # print(response)


if __name__ == "__main__":
    test_agent()