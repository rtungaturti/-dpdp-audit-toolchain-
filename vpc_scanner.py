"""
Verifiable Parental Consent (VPC) Scanner - Agent 2
Scans databases for child data and verifies parental consent compliance
Under DPDP Section 9 and Rule 10
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
from udc import get_udc
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VPCScanner:
    """
    Verifiable Parental Consent Scanner
    
    Requirements under DPDP Act:
    - Section 9(1): Verifiable parental consent required for children (<18 years)
    - Section 9(2): No tracking/behavioral monitoring of children
    - Rule 10: Specific requirements for consent verification
    """
    
    def __init__(self):
        self.udc = get_udc()
        self.child_records = []
        self.verified_consents = []
        self.missing_consents = []
        self.violations = []
    
    def scan_database(self, source_name: str, 
                      user_table: str,
                      age_column: str,
                      consent_column: str = None,
                      parent_consent_column: str = None,
                      consent_table: str = None):
        """
        Scan database for child data and verify parental consent
        
        Args:
            source_name: Name of the data source (configured in UDC)
            user_table: Table containing user/child data
            age_column: Column with age or date of birth
            consent_column: Column indicating consent status
            parent_consent_column: Column for parental consent flag
            consent_table: Separate table for consent records (if any)
        """
        logger.info(f"🔍 Scanning {source_name}.{user_table} for child data...")
        
        # Build query to find children (age < 18)
        query = f"""
            SELECT * FROM {user_table}
            WHERE {age_column} < 18
        """
        
        try:
            df = self.udc.query(source_name, query)
            logger.info(f"Found {len(df)} child records")
            
            for idx, row in df.iterrows():
                child_record = {
                    "source": source_name,
                    "table": user_table,
                    "age": row[age_column],
                    "row_data": row.to_dict()
                }
                self.child_records.append(child_record)
                
                # Check consent status
                consent_status = self._check_consent(
                    source_name, row, consent_column, parent_consent_column, consent_table
                )
                
                if consent_status == "verified":
                    self.verified_consents.append(child_record)
                else:
                    self.missing_consents.append({
                        **child_record,
                        "consent_status": consent_status
                    })
            
            # Check for violations (tracking, behavioral monitoring)
            self._check_violations(source_name, user_table)
            
            return self.generate_report()
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return f"Error scanning database: {str(e)}"
    
    def _check_consent(self, source_name: str, row: pd.Series,
                       consent_column: str, parent_consent_column: str,
                       consent_table: str) -> str:
        """Check if proper parental consent exists"""
        
        # Check direct consent column
        if consent_column and consent_column in row:
            value = str(row[consent_column]).lower()
            if value in ['yes', 'true', '1', 'verified', 'granted']:
                return "verified"
            elif value in ['no', 'false', '0', 'none']:
                return "missing"
        
        # Check separate parent consent column
        if parent_consent_column and parent_consent_column in row:
            value = str(row[parent_consent_column]).lower()
            if value in ['yes', 'true', '1', 'verified']:
                return "verified"
        
        # Check consent table if provided
        if consent_table:
            try:
                user_id = row.get('id')
                if user_id:
                    consent_query = f"""
                        SELECT * FROM {consent_table}
                        WHERE user_id = '{user_id}'
                        AND consent_type = 'parental'
                        AND status = 'active'
                    """
                    consent_df = self.udc.query(source_name, consent_query)
                    if len(consent_df) > 0:
                        return "verified"
            except Exception:
                pass
        
        return "not_found"
    
    def _check_violations(self, source_name: str, user_table: str):
        """Check for prohibited activities (tracking, behavioral monitoring)"""
        # This would check for tracking tables, behavioral data storage, etc.
        # For now, add placeholder check
        try:
            tables = self.udc.list_tables(source_name)
            tracking_tables = [t for t in tables if 'track' in t.lower() or 'behavior' in t.lower()]
            if tracking_tables:
                self.violations.append({
                    "type": "tracking_data",
                    "tables": tracking_tables,
                    "message": "Found tables that may contain tracking/behavioral data of children"
                })
        except Exception:
            pass
    
    def generate_report(self) -> str:
        """Generate VPC compliance report"""
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# 👶 Verifiable Parental Consent (VPC) Compliance Report

**Generated**: {today}
**Under DPDP Act**: Section 9 & Rule 10

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| Total Child Records Found | {len(self.child_records)} |
| ✅ Verified Parental Consent | {len(self.verified_consents)} |
| ❌ Missing/Invalid Consent | {len(self.missing_consents)} |
| ⚠️ Violations Found | {len(self.violations)} |

---

## ✅ Verified Consent Records ({len(self.verified_consents)})

"""
        if self.verified_consents:
            for record in self.verified_consents[:5]:  # Show first 5
                report += f"- Age: {record['age']} | Source: {record['source']}.{record['table']}\n"
            if len(self.verified_consents) > 5:
                report += f"\n*... and {len(self.verified_consents) - 5} more records*\n"
        else:
            report += "*No verified consent records found*\n"
        
        report += f"""
---

## ❌ Missing/Invalid Consent ({len(self.missing_consents)})

"""
        if self.missing_consents:
            for record in self.missing_consents[:5]:
                report += f"- Age: {record['age']} | Consent Status: {record.get('consent_status', 'unknown')}\n"
            if len(self.missing_consents) > 5:
                report += f"\n*... and {len(self.missing_consents) - 5} more records*\n"
        else:
            report += "*All child records have proper parental consent* ✅\n"
        
        report += f"""
---

## ⚠️ Compliance Violations

"""
        if self.violations:
            for violation in self.violations:
                report += f"**{violation['type']}**: {violation['message']}\n"
                if 'tables' in violation:
                    report += f"  - Tables: {', '.join(violation['tables'])}\n"
        else:
            report += "*No violations detected* ✅\n"
        
        report += f"""
---

## 📋 Compliance Requirements Reference

Under DPDP Act, 2023:

| Section | Requirement | Status |
|---------|-------------|--------|
| Section 9(1) | Verifiable parental consent for children | {'✅ Compliant' if len(self.missing_consents) == 0 else '❌ Non-Compliant'} |
| Section 9(2) | No tracking/behavioral monitoring | {'✅ Compliant' if len(self.violations) == 0 else '❌ Non-Compliant'} |
| Rule 10 | Consent verification standards | Requires implementation review |

---

## 🔧 Recommendations

"""
        if self.missing_consents:
            report += f"1. **Obtain parental consent** for {len(self.missing_consents)} child records\n"
            report += "2. Implement verifiable consent mechanism (Rule 10)\n"
        
        if self.violations:
            report += "3. Remove or anonymize tracking/behavioral data for children\n"
        
        report += """
---
*This report is generated automatically by the DPDP VPC Scanner*
"""
        return report
    
    def reset(self):
        """Reset scanner state for new scan"""
        self.child_records = []
        self.verified_consents = []
        self.missing_consents = []
        self.violations = []


# Singleton instance
_vpc_scanner = None

def get_vpc_scanner() -> VPCScanner:
    """Get the global VPC Scanner instance"""
    global _vpc_scanner
    if _vpc_scanner is None:
        _vpc_scanner = VPCScanner()
    return _vpc_scanner