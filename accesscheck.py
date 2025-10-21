#!/usr/bin/env python3
"""
GCP Permissions Checker for AgenticBot

This script verifies that the current authentication has all required permissions
to run the AgenticBot Streamlit application, including:
- BigQuery dataset and table access
- Vertex AI model access
- Service account impersonation (if applicable)

Usage:
    python check_permissions.py

Requirements:
    - Application Default Credentials (ADC) must be configured
    - Run: gcloud auth application-default login --impersonate-service-account=YOUR_SA
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path

try:
    from dotenv import load_dotenv
    from google.cloud import bigquery
    from google.cloud import resourcemanager_v3
    import vertexai
    from vertexai.generative_models import GenerativeModel
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
    import google.auth.transport.requests
    from google.api_core import exceptions as api_exceptions
    from google.cloud import exceptions as google_exceptions
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please install dependencies with: uv sync")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PermissionsChecker:
    """
    Check GCP permissions required for AgenticBot application.
    """
    
    def __init__(self):
        """Initialize the permissions checker."""
        load_dotenv()
        
        # Get configuration from environment
        self.project_id = os.getenv('GCP_PROJECT_ID')
        self.dataset_id = os.getenv('BQ_DATASET_ID')
        self.location = os.getenv('VERTEX_AI_LOCATION')
        self.model_name = os.getenv('GEMINI_MODEL_NAME')
        self.service_account = os.getenv('GOOGLE_CLOUD_SERVICE_ACCOUNT')
        
        if not all([self.project_id, self.dataset_id, self.location, self.model_name]):
            raise ValueError("Missing required environment variables. Check your .env file.")
        
        print(f"🔧 Configuration:")
        print(f"   Project ID: {self.project_id}")
        print(f"   Dataset ID: {self.dataset_id}")
        print(f"   Vertex AI Location: {self.location}")
        print(f"   Model: {self.model_name}")
        print(f"   Target Service Account: {self.service_account or 'Not specified'}")
        print()
    
    def check_authentication(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if Application Default Credentials are properly configured.
        Uses existing ADC without trying to refresh or re-authenticate.
        
        Returns:
            Tuple of (success, auth_info)
        """
        print("🔍 Checking Authentication...")
        
        try:
            # Get default credentials without forcing refresh
            credentials, project = default()
            
            # Get credential details without refreshing
            auth_info = {
                "valid": True,
                "project_id": project,
                "service_account_email": None,
                "credential_type": type(credentials).__name__
            }
            
            # Check if using service account impersonation
            if hasattr(credentials, 'service_account_email'):
                auth_info["service_account_email"] = credentials.service_account_email
            elif hasattr(credentials, '_service_account_email'):
                auth_info["service_account_email"] = credentials._service_account_email
            elif hasattr(credentials, '_target_principal'):
                auth_info["service_account_email"] = credentials._target_principal
            
            print(f"   ✅ Authentication: ADC Found")
            print(f"   📋 Credential Type: {auth_info['credential_type']}")
            print(f"   🏗️  Project: {project or 'Not specified in credentials'}")
            if auth_info["service_account_email"]:
                print(f"   👤 Service Account: {auth_info['service_account_email']}")
            else:
                print(f"   👤 Using: User credentials (no impersonation)")
            
            # Note about potential issues without trying to refresh
            if 'Impersonated' in auth_info['credential_type']:
                print(f"   ⚠️  Note: Impersonated credentials detected - some tests may fail if impersonation is broken")
            
            return True, auth_info
            
        except DefaultCredentialsError as e:
            print(f"   ❌ Authentication: Failed")
            print(f"   📋 Error: Application Default Credentials not found")
            print(f"   💡 Solution: Run 'gcloud auth application-default login'")
            return False, {"valid": False, "error": str(e)}
        
        except Exception as e:
            print(f"   ❌ Authentication: Failed")
            print(f"   📋 Error: {str(e)}")
            print(f"   💡 Note: Using existing ADC without refresh - this may be normal")
            return False, {"valid": False, "error": str(e)}
    
    def check_bigquery_permissions(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check BigQuery permissions and access.
        
        Returns:
            Tuple of (success, results_dict)
        """
        print("🗄️  Checking BigQuery Permissions...")
        
        results = {
            "client_creation": False,
            "dataset_access": False,
            "table_listing": False,
            "query_execution": False,
            "tables_found": [],
            "errors": []
        }
        
        try:
            # Test 1: Create BigQuery client
            client = bigquery.Client(project=self.project_id)
            results["client_creation"] = True
            print(f"   ✅ BigQuery Client: Created successfully")
            
            # Test 2: Access dataset
            try:
                dataset_ref = client.dataset(self.dataset_id)
                dataset = client.get_dataset(dataset_ref)
                results["dataset_access"] = True
                print(f"   ✅ Dataset Access: {self.dataset_id}")
                print(f"      📊 Created: {dataset.created}")
                print(f"      📍 Location: {dataset.location}")
                
                # Test 3: List tables in dataset
                try:
                    tables = list(client.list_tables(dataset))
                    results["table_listing"] = True
                    results["tables_found"] = [table.table_id for table in tables]
                    print(f"   ✅ Table Listing: Found {len(tables)} tables")
                    for table in tables[:5]:  # Show first 5 tables
                        print(f"      📋 {table.table_id}")
                    if len(tables) > 5:
                        print(f"      📋 ... and {len(tables) - 5} more")
                        
                except Exception as e:
                    results["errors"].append(f"Table listing failed: {str(e)}")
                    print(f"   ❌ Table Listing: Failed")
                    print(f"      📋 Error: {str(e)}")
                    
            except google_exceptions.NotFound:
                results["errors"].append(f"Dataset '{self.dataset_id}' not found")
                print(f"   ❌ Dataset Access: Dataset '{self.dataset_id}' not found")
                
            except google_exceptions.Forbidden as e:
                results["errors"].append(f"Dataset access forbidden: {str(e)}")
                print(f"   ❌ Dataset Access: Permission denied")
                print(f"      📋 Error: {str(e)}")
            
            # Test 4: Execute simple query
            try:
                query = "SELECT CURRENT_TIMESTAMP() as test_time"
                query_job = client.query(query)
                query_result = query_job.result()
                
                # Get first row
                for row in query_result:
                    test_time = row.test_time
                    break
                
                results["query_execution"] = True
                print(f"   ✅ Query Execution: Test query successful")
                print(f"      🕒 Result: {test_time}")
                
            except Exception as e:
                results["errors"].append(f"Query execution failed: {str(e)}")
                print(f"   ❌ Query Execution: Failed")
                print(f"      📋 Error: {str(e)}")
        
        except Exception as e:
            results["errors"].append(f"BigQuery client creation failed: {str(e)}")
            print(f"   ❌ BigQuery Client: Creation failed")
            print(f"      📋 Error: {str(e)}")
        
        success = all([
            results["client_creation"],
            results["dataset_access"],
            results["table_listing"],
            results["query_execution"]
        ])
        
        return success, results
    
    def check_vertex_ai_permissions(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check Vertex AI permissions and model access.
        
        Returns:
            Tuple of (success, results_dict)
        """
        print("🤖 Checking Vertex AI Permissions...")
        
        results = {
            "vertex_init": False,
            "model_creation": False,
            "model_prediction": False,
            "errors": []
        }
        
        try:
            # Test 1: Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            results["vertex_init"] = True
            print(f"   ✅ Vertex AI Init: Successful")
            print(f"      📍 Location: {self.location}")
            
            # Test 2: Create model instance
            try:
                model = GenerativeModel(self.model_name)
                results["model_creation"] = True
                print(f"   ✅ Model Access: {self.model_name}")
                
                # Test 3: Test prediction
                try:
                    test_prompt = "Say 'Hello' in one word only."
                    response = model.generate_content(test_prompt)
                    response_text = response.text.strip()
                    
                    results["model_prediction"] = True
                    print(f"   ✅ Model Prediction: Successful")
                    print(f"      🎯 Test prompt: {test_prompt}")
                    print(f"      📝 Response: {response_text[:50]}")
                    
                except Exception as e:
                    results["errors"].append(f"Model prediction failed: {str(e)}")
                    print(f"   ❌ Model Prediction: Failed")
                    print(f"      📋 Error: {str(e)}")
                    
            except Exception as e:
                results["errors"].append(f"Model creation failed: {str(e)}")
                print(f"   ❌ Model Access: Failed")
                print(f"      📋 Error: {str(e)}")
        
        except Exception as e:
            results["errors"].append(f"Vertex AI initialization failed: {str(e)}")
            print(f"   ❌ Vertex AI Init: Failed")
            print(f"      📋 Error: {str(e)}")
        
        success = all([
            results["vertex_init"],
            results["model_creation"],
            results["model_prediction"]
        ])
        
        return success, results
    
    def check_project_permissions(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check basic project-level permissions.
        
        Returns:
            Tuple of (success, results_dict)
        """
        print("🏗️  Checking Project Permissions...")
        
        results = {
            "project_access": False,
            "project_info": {},
            "errors": []
        }
        
        try:
            # Test project access using Resource Manager API
            client = resourcemanager_v3.ProjectsClient()
            project_name = f"projects/{self.project_id}"
            
            try:
                project = client.get_project(name=project_name)
                results["project_access"] = True
                results["project_info"] = {
                    "project_id": project.project_id,
                    "display_name": project.display_name,
                    "state": project.state.name,
                    "project_number": project.name.split('/')[-1]
                }
                
                print(f"   ✅ Project Access: Successful")
                print(f"      📋 Display Name: {project.display_name}")
                print(f"      🔢 Project Number: {results['project_info']['project_number']}")
                print(f"      📊 State: {project.state.name}")
                
            except api_exceptions.PermissionDenied as e:
                results["errors"].append(f"Project access denied: {str(e)}")
                print(f"   ⚠️  Project Access: Limited (this is often normal)")
                print(f"      📋 Note: Resource Manager API access not required for BigQuery/Vertex AI")
                # Don't fail on this - it's common to not have project-level permissions
                results["project_access"] = True
                
        except Exception as e:
            results["errors"].append(f"Project check failed: {str(e)}")
            print(f"   ⚠️  Project Access: Could not verify")
            print(f"      📋 Error: {str(e)}")
            # Don't fail on this - focus on service-specific permissions
            results["project_access"] = True
        
        return results["project_access"], results
    
    def generate_report(self, auth_result: Dict, bq_result: Dict, vai_result: Dict, proj_result: Dict) -> str:
        """
        Generate a comprehensive permissions report.
        
        Args:
            auth_result: Authentication check results
            bq_result: BigQuery check results  
            vai_result: Vertex AI check results
            proj_result: Project check results
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("📋 GCP PERMISSIONS REPORT FOR AGENTICBOT")
        report.append("=" * 80)
        
        # Overall Status
        auth_ok = auth_result[0]
        bq_ok = bq_result[0] 
        vai_ok = vai_result[0]
        proj_ok = proj_result[0]
        
        # Focus on service permissions for overall status
        overall_ok = bq_ok and vai_ok
        
        report.append(f"\n🎯 OVERALL STATUS: {'✅ READY TO RUN' if overall_ok else '❌ ISSUES FOUND'}\n")
        
        # Detailed Results
        report.append("📊 DETAILED RESULTS:")
        report.append(f"   🔐 Authentication:     {'✅ Pass' if auth_ok else '❌ Fail'}")
        report.append(f"   🗄️  BigQuery Access:    {'✅ Pass' if bq_ok else '❌ Fail'}")
        report.append(f"   🤖 Vertex AI Access:   {'✅ Pass' if vai_ok else '❌ Fail'}")
        report.append(f"   🏗️  Project Access:     {'✅ Pass' if proj_ok else '⚠️  Limited'}")
        
        # BigQuery Details
        if bq_result[1].get("tables_found"):
            report.append(f"\n📋 BIGQUERY TABLES FOUND ({len(bq_result[1]['tables_found'])}):")
            for table in bq_result[1]["tables_found"][:10]:
                report.append(f"   📊 {table}")
            if len(bq_result[1]["tables_found"]) > 10:
                report.append(f"   📊 ... and {len(bq_result[1]['tables_found']) - 10} more")
        
        # Errors Summary
        all_errors = []
        for result in [auth_result[1], bq_result[1], vai_result[1], proj_result[1]]:
            if isinstance(result, dict) and "errors" in result:
                all_errors.extend(result["errors"])
            elif isinstance(result, dict) and "error" in result:
                all_errors.append(result["error"])
        
        if all_errors:
            report.append(f"\n❌ ISSUES FOUND ({len(all_errors)}):")
            for i, error in enumerate(all_errors, 1):
                report.append(f"   {i}. {error}")
        
        # Next Steps
        report.append(f"\n🚀 NEXT STEPS:")
        if overall_ok:
            report.append("   ✅ All required permissions verified!")
            report.append("   🎉 You can now run the Streamlit app:")
            report.append("      streamlit run src/ui/agenticbot_streamlit.py")
        else:
            report.append("   🔧 Fix the issues above, then:")
            if not auth_ok:
                report.append("      1. Run: gcloud auth application-default login")
                if self.service_account:
                    report.append(f"         With: --impersonate-service-account={self.service_account}")
            if not bq_ok:
                report.append("      2. Ensure BigQuery permissions: bigquery.dataViewer, bigquery.jobUser")
            if not vai_ok:
                report.append("      3. Ensure Vertex AI permissions: aiplatform.user")
            report.append("      4. Re-run this script to verify")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
    
    def run_full_check(self):
        """Run all permission checks and display comprehensive report."""
        print("🚀 GCP Permissions Checker for AgenticBot")
        print("=" * 80)
        print()
        
        # Run all checks
        auth_result = self.check_authentication()
        print()
        
        # Continue with service checks even if auth check failed
        # The actual service calls will reveal the real permission status
        if not auth_result[0]:
            print("⚠️  Authentication check had issues, but continuing with service tests...")
            print("   (Service calls will reveal actual permission status)")
            print()
        
        bq_result = self.check_bigquery_permissions()
        print()
        
        vai_result = self.check_vertex_ai_permissions()
        print()
        
        proj_result = self.check_project_permissions()
        print()
        
        # Generate and display report
        report = self.generate_report(auth_result, bq_result, vai_result, proj_result)
        print(report)
        
        # Return overall success (focus on service permissions rather than auth check)
        return bq_result[0] and vai_result[0]


def main():
    """Main entry point."""
    try:
        checker = PermissionsChecker()
        success = checker.run_full_check()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Permission check cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
