"""
GCP Pricing Tools for Cloud Billing API
Tools for searching services, getting SKUs, and retrieving pricing information.
"""

import os
import json
import requests
from typing import Dict, List, Optional
from pathlib import Path
from google.auth import default
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class GCPPricingTools:
    """Tools for interacting with GCP Cloud Billing API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GCP Pricing Tools
        
        Args:
            api_key: GCP API key for Cloud Billing API (optional, will use ADC if not provided)
        """
        self.api_key = api_key or os.getenv('GCP_PRICING_API_KEY')
        
        # Set up authentication - prefer API key over ADC
        if self.api_key:
            self.use_adc = False
            print("Using API key for GCP Pricing API")
        else:
            try:
                self.credentials, self.project = default()
                self.auth_request = Request()
                self.use_adc = True
                print("Using Application Default Credentials for GCP Pricing API")
            except Exception as e:
                raise ValueError(f"No API key provided and ADC not available: {e}")
        
        self.base_url_v2beta = "https://cloudbilling.googleapis.com/v2beta"
        self.base_url_v1beta = "https://cloudbilling.googleapis.com/v1beta"
        
        # Load service mappings cache
        self.service_mappings = self._load_service_mappings()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if self.use_adc:
            # Refresh credentials if needed
            if not self.credentials.valid:
                self.credentials.refresh(self.auth_request)
            return {
                'Authorization': f'Bearer {self.credentials.token}',
                'Content-Type': 'application/json'
            }
        else:
            return {}
    
    def _get_auth_params(self) -> Dict[str, str]:
        """Get authentication parameters for API requests"""
        if self.use_adc:
            return {}
        else:
            return {'key': self.api_key}
    
    def _load_service_mappings(self) -> Dict[str, str]:
        """Load cached service name to ID mappings"""
        # Go up 4 levels: tools -> agents -> src -> project_root, then config
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "service_mappings.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def search_gcp_service(self, service_name: str) -> Dict:
        """
        Search for a GCP service by name and return service ID
        
        Args:
            service_name: Natural language service name (e.g., "Compute Engine", "Gemini API")
        
        Returns:
            {
                "service_id": "AEFD-7695-64FA",
                "display_name": "Gemini API",
                "found": true
            }
        """
        # Check cache first
        service_key = service_name.lower().strip()
        if service_key in self.service_mappings:
            cached = self.service_mappings[service_key]
            return {
                "service_id": cached["service_id"],
                "display_name": cached["display_name"],
                "found": True,
                "source": "cache"
            }
        
        # Search via API
        url = f"{self.base_url_v2beta}/services"
        params = self._get_auth_params()
        params["pageSize"] = 1000
        headers = self._get_auth_headers()
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Search for matching service
            search_term = service_name.lower()
            for service in data.get("services", []):
                display_name = service.get("displayName", "")
                if display_name and search_term in display_name.lower():
                    return {
                        "service_id": service["serviceId"],
                        "display_name": display_name,
                        "found": True,
                        "source": "api"
                    }
            
            return {
                "service_id": None,
                "display_name": None,
                "found": False,
                "error": f"Service '{service_name}' not found"
            }
            
        except Exception as e:
            return {
                "service_id": None,
                "display_name": None,
                "found": False,
                "error": str(e)
            }
    
    def get_service_skus(self, service_id: str, filter_text: Optional[str] = None) -> List[Dict]:
        """
        Get all SKUs for a GCP service
        
        Args:
            service_id: Service ID from search_gcp_service
            filter_text: Optional filter (e.g., "gemini-2.5-flash-lite", "n1-standard")
        
        Returns:
            [
                {
                    "sku_id": "399C-32AD-1412",
                    "display_name": "Generate content input token count gemini 2.5 flash lite",
                    "description": "Input tokens for Gemini 2.5 Flash Lite"
                }
            ]
        """
        url = f"{self.base_url_v2beta}/skus"
        params = self._get_auth_params()
        params.update({
            "filter": f'service="services/{service_id}"',
            "pageSize": 200
        })
        headers = self._get_auth_headers()
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            skus = []
            for sku in data.get("skus", []):
                display_name = sku.get("displayName", "")
                
                # Apply filter if provided (case-insensitive, ignore special chars)
                if filter_text:
                    # Normalize both strings for comparison
                    filter_normalized = filter_text.lower().replace("-", " ").replace("_", " ")
                    name_normalized = display_name.lower().replace("-", " ").replace("_", " ")
                    
                    if filter_normalized not in name_normalized:
                        continue
                
                skus.append({
                    "sku_id": sku["skuId"],
                    "display_name": display_name,
                    "name": sku.get("name", "")
                })
            
            return skus
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_sku_pricing(self, sku_id: str, currency: str = "USD") -> Dict:
        """
        Get pricing details for a specific SKU
        
        Args:
            sku_id: SKU ID from get_service_skus
            currency: Currency code (default: USD)
        
        Returns:
            {
                "sku_id": "399C-32AD-1412",
                "price": 0.10,
                "currency": "USD",
                "unit": "per 1M tokens",
                "unit_description": "count",
                "unit_quantity": "1000000"
            }
        """
        url = f"{self.base_url_v1beta}/skus/{sku_id}/price"
        params = self._get_auth_params()
        params["currencyCode"] = currency
        headers = self._get_auth_headers()
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            rate = data.get("rate", {})
            tiers = rate.get("tiers", [])
            unit_info = rate.get("unitInfo", {})
            
            # Get first tier price (most common case)
            price_nanos = 0
            if tiers and len(tiers) > 0:
                list_price = tiers[0].get("listPrice", {})
                price_nanos = list_price.get("nanos", 0)
            
            # Convert nanos to dollars
            price = price_nanos / 1_000_000_000
            
            # Format unit description
            unit_quantity = unit_info.get("unitQuantity", {}).get("value", "1")
            unit = unit_info.get("unit", "")
            unit_description = unit_info.get("unitDescription", "")
            
            # Create readable unit string
            if unit_quantity == "1000000":
                readable_unit = f"per 1M {unit_description}s" if unit_description else "per 1M units"
            else:
                readable_unit = f"per {unit_description}" if unit_description else f"per {unit}"
            
            return {
                "sku_id": sku_id,
                "price": price,
                "currency": currency,
                "unit": readable_unit,
                "unit_description": unit_description,
                "unit_quantity": unit_quantity,
                "raw_unit": unit,
                "has_tiered_pricing": len(tiers) > 1,
                "tiers": tiers if len(tiers) > 1 else []
            }
            
        except Exception as e:
            return {
                "sku_id": sku_id,
                "error": str(e)
            }
    
    def calculate_cost(self, sku_id: str, quantity: float, price_per_unit: float, unit_quantity: float, currency: str = "USD") -> Dict:
        """
        Calculate cost for a single SKU with given usage
        
        Args:
            sku_id: The SKU ID
            quantity: Usage quantity (e.g., 3000000 for 3M tokens)
            price_per_unit: Price per unit from get_sku_pricing (e.g., 0.5)
            unit_quantity: Unit quantity from get_sku_pricing (e.g., 1000000 for 'per 1M')
            currency: Currency code (default: USD)
        
        Returns:
            {
                "sku_id": "AC9B-C746-1501",
                "total_cost": 1.5,
                "currency": "USD",
                "calculation": "3000000 / 1000000 * 0.5 = 1.5",
                "breakdown": {...}
            }
        """
        # Calculate cost: (quantity / unit_quantity) * price_per_unit
        cost = (quantity / unit_quantity) * price_per_unit
        
        # Create calculation explanation
        calculation = f"{quantity} / {unit_quantity} * {price_per_unit} = {cost}"
        
        return {
            "sku_id": sku_id,
            "total_cost": round(cost, 4),
            "currency": currency,
            "calculation": calculation,
            "breakdown": {
                "quantity_used": quantity,
                "price_per_unit": price_per_unit,
                "unit_quantity": unit_quantity,
                "units_consumed": quantity / unit_quantity,
                "cost": round(cost, 4)
            }
        }


# Convenience functions for direct tool use
def search_gcp_service(service_name: str) -> Dict:
    """Search for GCP service - convenience wrapper"""
    tools = GCPPricingTools()
    return tools.search_gcp_service(service_name)


def get_service_skus(service_id: str, filter_text: Optional[str] = None) -> List[Dict]:
    """Get service SKUs - convenience wrapper"""
    tools = GCPPricingTools()
    return tools.get_service_skus(service_id, filter_text)


def get_sku_pricing(sku_id: str, currency: str = "USD") -> Dict:
    """Get SKU pricing - convenience wrapper"""
    tools = GCPPricingTools()
    return tools.get_sku_pricing(sku_id, currency)


def calculate_cost(sku_id: str, quantity: float, price_per_unit: float, unit_quantity: float, currency: str = "USD") -> Dict:
    """Calculate cost - convenience wrapper"""
    tools = GCPPricingTools()
    return tools.calculate_cost(sku_id, quantity, price_per_unit, unit_quantity, currency)
