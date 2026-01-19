#!/usr/bin/env python3
"""
Test n8n Webhook Connection
Diagnoses DNS and connection issues with n8n webhook URL.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from src.services.n8n_client import get_n8n_client
    from src.utils.config import settings
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def main():
    """Test n8n webhook connection."""
    print("=" * 60)
    print("n8n Webhook Connection Test")
    print("=" * 60)
    print()
    
    # Check if URL is configured
    webhook_url = settings.n8n_webhook_url
    if not webhook_url:
        print("❌ ERROR: N8N_WEBHOOK_URL is not configured")
        print()
        print("Please set N8N_WEBHOOK_URL in your .env file:")
        print("  N8N_WEBHOOK_URL=https://your-instance.app.n8n.cloud/webhook/your-path")
        print()
        print("To get your webhook URL:")
        print("  1. Open your n8n workflow")
        print("  2. Click on the Webhook node")
        print("  3. Copy the Production URL (not Test URL)")
        return 1
    
    print(f"Webhook URL: {webhook_url}")
    print()
    
    # Get client and test connection
    n8n_client = get_n8n_client()
    if not n8n_client:
        print("❌ ERROR: Could not create n8n client")
        return 1
    
    print("Testing connection...")
    print()
    
    result = n8n_client.test_connection()
    
    if result.get("success"):
        print("✅ Connection test PASSED")
        print()
        print(f"  DNS Resolution: ✅ ({result.get('ip_address', 'N/A')})")
        print(f"  HTTP Status: {result.get('http_status', 'N/A')}")
        print(f"  Webhook URL: {result.get('webhook_url', 'N/A')}")
        print()
        print("Your n8n webhook is accessible!")
        return 0
    else:
        print("❌ Connection test FAILED")
        print()
        print(f"Error: {result.get('error', 'Unknown error')}")
        print()
        
        if result.get("hostname"):
            print(f"Hostname: {result.get('hostname')}")
            print()
        
        suggestions = result.get("suggestions", [])
        if suggestions:
            print("Suggestions:")
            for suggestion in suggestions:
                print(f"  • {suggestion}")
            print()
        
        print("Troubleshooting steps:")
        print("  1. Verify the domain exists:")
        print(f"     Try accessing https://{result.get('hostname', 'your-instance.app.n8n.cloud')} in your browser")
        print()
        print("  2. Check if the n8n instance was deleted or the domain changed")
        print()
        print("  3. Verify the webhook URL in your .env file matches the Production URL from n8n")
        print()
        print("  4. Check your network connection and firewall settings")
        print()
        print("  5. Try using a different DNS server:")
        print("     - Google DNS: 8.8.8.8, 8.8.4.4")
        print("     - Cloudflare DNS: 1.1.1.1, 1.0.0.1")
        print()
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
