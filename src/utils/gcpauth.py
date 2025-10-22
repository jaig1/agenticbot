#!/usr/bin/env python3
"""
GCP Authentication Script with Service Account Impersonation

This script manages Google Cloud Platform authentication by:
1. Checking existing Application Default Credentials (ADC)
2. Validating current credentials against target service account
3. Providing options for re-authentication if needed
4. Setting up ADC with service account impersonation

Usage:
    python gcpauth.py
"""

import os
import subprocess
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
    import google.auth.transport.requests
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please install dependencies with: uv add google-auth google-cloud-core python-dotenv")
    sys.exit(1)


class GCPAuthManager:
    """Manages GCP authentication and service account impersonation."""
   
    def __init__(self):
        """Initialize the GCP Auth Manager."""
        load_dotenv()
       
        self.project_id = os.getenv('GCP_PROJECT_ID')
        self.service_account = os.getenv('GOOGLE_CLOUD_SERVICE_ACCOUNT')
       
        if not self.project_id:
            print("❌ Error: GCP_PROJECT_ID not found in .env file")
            sys.exit(1)
           
        if not self.service_account:
            print("❌ Error: GOOGLE_CLOUD_SERVICE_ACCOUNT not found in .env file")
            sys.exit(1)
           
        print(f"🔧 Target Project: {self.project_id}")
        print(f"🔧 Target Service Account: {self.service_account}")
        print()

    def check_gcloud_installed(self) -> bool:
        """Check if gcloud CLI is installed."""
        try:
            result = subprocess.run(['gcloud', 'version'],
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_current_user_auth(self) -> Optional[str]:
        """Get current authenticated user from gcloud."""
        try:
            result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        except subprocess.TimeoutExpired:
            return None

    def check_adc_status(self) -> Dict[str, Any]:
        """Check Application Default Credentials status."""
        status = {
            'exists': False,
            'valid': False,
            'project_id': None,
            'service_account': None,
            'error': None
        }
       
        try:
            # Try to get default credentials
            credentials, project = default()
            status['exists'] = True
            status['project_id'] = project
           
            # Test if credentials are valid
            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
            status['valid'] = True
           
            # Check if using service account impersonation
            # For impersonated credentials, check multiple possible attributes
            if hasattr(credentials, 'service_account_email'):
                status['service_account'] = credentials.service_account_email
            elif hasattr(credentials, '_service_account_email'):
                status['service_account'] = credentials._service_account_email
            elif hasattr(credentials, '_target_principal'):
                status['service_account'] = credentials._target_principal
            elif 'impersonate' in str(type(credentials)).lower():
                # Try to extract from the credential object representation
                cred_str = str(credentials)
                if 'service_account_email' in cred_str:
                    import re
                    match = re.search(r"service_account_email='([^']+)'", cred_str)
                    if match:
                        status['service_account'] = match.group(1)
               
        except DefaultCredentialsError as e:
            status['error'] = str(e)
        except Exception as e:
            status['exists'] = True
            status['error'] = str(e)
           
        return status

    def test_service_account_access(self) -> bool:
        """Test if we can actually use the service account impersonation."""
        try:
            # Try to get an access token using the impersonated credentials
            from google.auth import impersonated_credentials
            from google.auth.transport.requests import Request
           
            # Get source credentials
            source_credentials, _ = default()
           
            # Create impersonated credentials
            target_credentials = impersonated_credentials.Credentials(
                source_credentials=source_credentials,
                target_principal=self.service_account,
                target_scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
           
            # Try to refresh to get a token
            request = Request()
            target_credentials.refresh(request)
           
            return target_credentials.valid
           
        except Exception as e:
            print(f"   ❌ Service account access test failed: {e}")
            return False

    def validate_credentials_for_target(self) -> bool:
        """Validate if current credentials work with target service account."""
        print("   Testing authentication with a simple GCP API call...")
       
        try:
            # Simple test: try to describe the project using gcloud
            result = subprocess.run(
                ['gcloud', 'projects', 'describe', self.project_id, '--format=value(projectId)'],
                capture_output=True, text=True, timeout=30
            )
           
            if result.returncode == 0 and result.stdout.strip() == self.project_id:
                print("   ✅ Authentication is working correctly")
                return True
            else:
                print(f"   ❌ Project access test failed: {result.stderr}")
                return False
               
        except subprocess.TimeoutExpired:
            print("   ❌ Authentication test timed out")
            return False
        except Exception as e:
            print(f"   ❌ Authentication test failed: {e}")
            return False

    def run_gcloud_command(self, command: list, description: str) -> bool:
        """Run a gcloud command with user interaction."""
        print(f"🔄 {description}...")
        print(f"   Command: gcloud {' '.join(command)}")
        print()
       
        try:
            result = subprocess.run(['gcloud'] + command, timeout=300)  # 5 minute timeout
            success = result.returncode == 0
           
            if success:
                print(f"✅ {description} completed successfully")
            else:
                print(f"❌ {description} failed")
               
            return success
           
        except subprocess.TimeoutExpired:
            print(f"❌ {description} timed out")
            return False
        except KeyboardInterrupt:
            print(f"❌ {description} cancelled by user")
            return False

    def perform_user_authentication(self) -> bool:
        """Perform user authentication via gcloud auth login."""
        return self.run_gcloud_command(
            ['auth', 'login'],
            "User authentication (browser will open)"
        )

    def perform_adc_setup(self) -> bool:
        """Set up Application Default Credentials with service account impersonation."""
        command = [
            'auth', 'application-default', 'login',
            '--impersonate-service-account', self.service_account
        ]
       
        return self.run_gcloud_command(
            command,
            f"ADC setup with service account impersonation (browser will open)"
        )

    def revoke_all_auth(self) -> bool:
        """Revoke all existing authentication."""
        # Try to revoke user credentials first
        user_result = self.run_gcloud_command(
            ['auth', 'revoke', '--all'],
            "Revoking all existing authentication"
        )
       
        # If that fails, try to revoke just ADC
        if not user_result:
            print("🔄 Trying to revoke just Application Default Credentials...")
            adc_result = self.run_gcloud_command(
                ['auth', 'application-default', 'revoke'],
                "Revoking Application Default Credentials"
            )
            return adc_result
           
        return user_result

    def get_user_choice(self, message: str) -> bool:
        """Get yes/no choice from user."""
        while True:
            choice = input(f"{message} (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")

    def display_status(self):
        """Display current authentication status."""
        print("=" * 60)
        print("🔍 CHECKING CURRENT AUTHENTICATION STATUS")
        print("=" * 60)
       
        # Check gcloud installation
        if not self.check_gcloud_installed():
            print("❌ gcloud CLI not found. Please install Google Cloud SDK first.")
            print("   Installation: https://cloud.google.com/sdk/docs/install")
            sys.exit(1)
       
        print("✅ gcloud CLI is installed")
       
        # Check current user auth
        current_user = self.get_current_user_auth()
        if current_user:
            print(f"✅ User authenticated as: {current_user}")
        else:
            print("⚠️  No active user authentication")
       
        # Check ADC status
        adc_status = self.check_adc_status()
       
        if adc_status['exists']:
            if adc_status['valid']:
                print("✅ Application Default Credentials (ADC) are valid")
                print(f"   Project: {adc_status['project_id']}")
                if adc_status['service_account']:
                    print(f"   Service Account: {adc_status['service_account']}")
                else:
                    print("   Using user credentials (no impersonation)")
            else:
                print(f"❌ ADC exist but are invalid: {adc_status['error']}")
        else:
            print("⚠️  No Application Default Credentials found")
       
        print()
        return adc_status

    def run(self):
        """Main execution flow."""
        print("🚀 GCP Authentication Manager")
        print()
       
        # Display current status
        adc_status = self.display_status()
       
        # Check if current credentials are valid for our target
        credentials_valid = self.validate_credentials_for_target()
       
        if credentials_valid:
            print("✅ Current credentials are valid for the target configuration!")
            print()
           
            if not self.get_user_choice("Do you want to force re-authentication anyway?"):
                print("🎉 Using existing credentials. Authentication setup complete!")
                return True
            print()
       
        print("🔄 Starting authentication process...")
        print()
       
        # Step 1: Revoke existing auth if needed
        if adc_status['exists'] or self.get_current_user_auth():
            print("📋 Existing authentication detected. Cleaning up first...")
            revoke_success = self.revoke_all_auth()
            if not revoke_success:
                print("⚠️  Could not revoke existing credentials, but continuing...")
                print("   This may happen with impersonated credentials.")
            print()
       
        # Step 2: User authentication
        print("📋 Step 1: User Authentication")
        print("   You will be redirected to your browser to sign in to Google Cloud.")
        input("   Press Enter to continue...")
       
        if not self.perform_user_authentication():
            print("❌ User authentication failed")
            return False
        print()
       
        # Step 3: ADC setup with impersonation
        print("📋 Step 2: Application Default Credentials Setup")
        print("   Setting up ADC with service account impersonation.")
        print("   You may need to authorize impersonation in your browser.")
        input("   Press Enter to continue...")
       
        if not self.perform_adc_setup():
            print("❌ ADC setup failed")
            return False
        print()
       
        # Step 4: Final validation
        print("🔍 Validating final setup...")
        if self.validate_credentials_for_target():
            print("🎉 Authentication setup completed successfully!")
            print()
            print("You can now use Google Cloud services with the configured service account.")
            return True
        else:
            print("❌ Final validation failed. Please check your configuration.")
            return False


def main():
    """Main entry point."""
    try:
        auth_manager = GCPAuthManager()
        success = auth_manager.run()
        sys.exit(0 if success else 1)
       
    except KeyboardInterrupt:
        print("\n❌ Authentication cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
