"""
Test script for Phase 8: n8n Integration
Run this to verify all Phase 8 components work correctly.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set dummy API key for testing (if not set)
if not os.getenv('GROK_API_KEY'):
    os.environ['GROK_API_KEY'] = 'test_key_for_testing_only'

try:
    from src.services.n8n_client import N8nClient, get_n8n_client
    from src.orchestrator.conversation_manager import get_conversation_manager
except Exception as e:
    print(f"Error importing n8n modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def test_n8n_client_initialization():
    """Test n8n Client initialization."""
    print("\n=== Testing n8n Client Initialization ===")
    try:
        client = get_n8n_client()
        if client:
            print(f"[PASS] n8n Client initialized: webhook_url configured")
            return True
        else:
            print("[WARNING] n8n Client not initialized (N8N_WEBHOOK_URL not set)")
            print("[INFO] This is expected if N8N_WEBHOOK_URL is not configured")
            return True  # Not a failure, just not configured
    except Exception as e:
        print(f"[FAIL] n8n Client initialization failed: {e}")
        return False


def test_n8n_client_without_url():
    """Test n8n Client behavior when URL is not configured."""
    print("\n=== Testing n8n Client (No URL) ===")
    try:
        # Create client without URL
        client = N8nClient(webhook_url=None)
        
        # Try to generate PDF (should raise error)
        try:
            client.generate_pdf_and_email(
                itinerary={"city": "Jaipur", "duration_days": 1},
                sources=[],
                email="test@example.com"
            )
            print("[FAIL] Should have raised error when webhook URL not configured")
            return False
        except Exception as e:
            if "not configured" in str(e).lower():
                print("[PASS] n8n Client correctly raises error when URL not configured")
                return True
            else:
                print(f"[FAIL] Unexpected error: {e}")
                return False
    except Exception as e:
        print(f"[FAIL] n8n Client test failed: {e}")
        return False


def test_n8n_workflow_file():
    """Test that n8n workflow file exists and is valid JSON."""
    print("\n=== Testing n8n Workflow File ===")
    try:
        import json
        workflow_path = Path(__file__).parent.parent / "n8n-workflows" / "pdf-email-workflow.json"
        
        if not workflow_path.exists():
            print(f"[FAIL] Workflow file not found: {workflow_path}")
            return False
        
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        # Validate structure
        if "nodes" in workflow and "connections" in workflow:
            print("[PASS] n8n workflow file is valid JSON with required structure")
            print(f"   Nodes: {len(workflow.get('nodes', []))}")
            return True
        else:
            print("[FAIL] Workflow file missing required fields")
            return False
    except json.JSONDecodeError as e:
        print(f"[FAIL] Workflow file is not valid JSON: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error reading workflow file: {e}")
        return False


def test_pdf_endpoint_integration():
    """Test PDF endpoint integration (without actually calling n8n)."""
    print("\n=== Testing PDF Endpoint Integration ===")
    try:
        # Test that the endpoint code structure is correct
        # We can't actually test the endpoint without a running server and n8n
        from src.models.request_models import GeneratePDFRequest
        from src.models.response_models import PDFResponse
        
        # Test request model
        request = GeneratePDFRequest(
            session_id="test-session",
            email="test@example.com"
        )
        print("[PASS] GeneratePDFRequest model works")
        
        # Test response model
        response = PDFResponse(
            status="success",
            message="PDF generated",
            email_sent=True,
            email_address="test@example.com"
        )
        print("[PASS] PDFResponse model works")
        
        return True
    except Exception as e:
        print(f"[FAIL] PDF endpoint integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 8 tests."""
    print("=" * 50)
    print("Phase 8: n8n Integration - Test Suite")
    print("=" * 50)
    
    results = []
    
    results.append(("n8n Client Initialization", test_n8n_client_initialization()))
    results.append(("n8n Client (No URL)", test_n8n_client_without_url()))
    results.append(("n8n Workflow File", test_n8n_workflow_file()))
    results.append(("PDF Endpoint Integration", test_pdf_endpoint_integration()))
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All Phase 8 tests passed!")
        print("\n[NOTE] To fully test n8n integration:")
        print("  1. Set N8N_WEBHOOK_URL in backend/.env")
        print("  2. Import workflow in n8n")
        print("  3. Configure SMTP credentials")
        print("  4. Test with actual API call")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Check errors above.")


if __name__ == "__main__":
    main()
