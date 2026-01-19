"""
n8n Webhook Client
Handles communication with n8n workflows for PDF generation and email.
"""

import requests
from typing import Dict, Any, Optional
import logging

try:
    from ..utils.config import settings
    from ..utils.error_handler import TravelAssistantException
except ImportError:
    from src.utils.config import settings
    from src.utils.error_handler import TravelAssistantException

logger = logging.getLogger(__name__)


class N8nClient:
    """
    Client for interacting with n8n webhooks.
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize n8n client.
        
        Args:
            webhook_url: n8n webhook URL (defaults to settings.n8n_webhook_url)
        """
        self.webhook_url = webhook_url or settings.n8n_webhook_url
        
        if not self.webhook_url:
            logger.warning("N8N_WEBHOOK_URL not configured")
        else:
            # Test DNS resolution on initialization
            self._test_dns_resolution()
    
    def _test_dns_resolution(self):
        """Test if the webhook URL domain can be resolved."""
        try:
            from urllib.parse import urlparse
            import socket
            
            parsed = urlparse(self.webhook_url)
            hostname = parsed.hostname
            
            if hostname:
                # Try to resolve the hostname
                socket.gethostbyname(hostname)
                logger.info(f"DNS resolution successful for {hostname}")
            else:
                logger.warning(f"Could not extract hostname from URL: {self.webhook_url}")
        except socket.gaierror as e:
            logger.error(
                f"DNS resolution failed for {hostname}. "
                f"The domain may not exist or there may be network/DNS issues. "
                f"Please verify the webhook URL is correct: {self.webhook_url}"
            )
        except Exception as e:
            logger.warning(f"Could not test DNS resolution: {e}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to n8n webhook.
        
        Returns:
            Dictionary with connection test results
        """
        if not self.webhook_url:
            return {
                "success": False,
                "error": "N8N_WEBHOOK_URL not configured"
            }
        
        try:
            from urllib.parse import urlparse
            import socket
            
            parsed = urlparse(self.webhook_url)
            hostname = parsed.hostname
            
            # Test DNS resolution
            try:
                ip = socket.gethostbyname(hostname)
                dns_ok = True
            except socket.gaierror:
                return {
                    "success": False,
                    "error": f"DNS resolution failed for {hostname}",
                    "hostname": hostname,
                    "webhook_url": self.webhook_url,
                    "suggestions": [
                        "Verify the domain exists: try accessing https://" + hostname + " in your browser",
                        "Check if the n8n instance was deleted or the domain changed",
                        "Try using a different DNS server (e.g., 8.8.8.8 or 1.1.1.1)",
                        "Check your network connection and firewall settings"
                    ]
                }
            
            # Test HTTP connection with a simple HEAD request
            try:
                response = requests.head(
                    self.webhook_url,
                    timeout=5,
                    allow_redirects=True
                )
                return {
                    "success": True,
                    "dns_resolved": True,
                    "ip_address": ip,
                    "http_status": response.status_code,
                    "webhook_url": self.webhook_url
                }
            except requests.RequestException as e:
                return {
                    "success": False,
                    "error": f"HTTP connection failed: {str(e)}",
                    "dns_resolved": True,
                    "ip_address": ip,
                    "webhook_url": self.webhook_url
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection test failed: {str(e)}",
                "webhook_url": self.webhook_url
            }
    
    def generate_pdf_and_email(
        self,
        itinerary: Dict[str, Any],
        sources: list,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger n8n workflow to generate PDF and send email.
        
        Args:
            itinerary: Itinerary dictionary
            sources: List of source dictionaries
            email: Optional email address
        
        Returns:
            Response dictionary with status and details
        """
        if not self.webhook_url:
            raise TravelAssistantException("N8N_WEBHOOK_URL not configured. Cannot generate PDF.")
        
        # Normalize webhook URL - n8n cloud URLs might be workflow URLs, need to convert to webhook
        webhook_url = self.webhook_url.strip()
        
        # n8n cloud webhook URLs can be in different formats:
        # 1. Production webhook: https://xxx.app.n8n.cloud/webhook/xxx
        # 2. Test webhook: https://xxx.app.n8n.cloud/webhook-test/xxx
        # 3. Workflow URL: https://xxx.app.n8n.cloud/workflow/xxx -> needs conversion
        
        # If it's a workflow URL, try to convert to webhook URL
        if '/workflow/' in webhook_url:
            logger.warning(f"URL appears to be a workflow URL, attempting webhook conversion: {webhook_url}")
            # Extract the workflow ID
            workflow_id = webhook_url.split('/workflow/')[-1].split('/')[0]
            # Convert to webhook URL
            base_url = webhook_url.split('/workflow/')[0]
            webhook_url = f"{base_url}/webhook/{workflow_id}"
            logger.info(f"Converted to webhook URL: {webhook_url}")
        
        # Check if URL is a test webhook and suggest production
        if '/webhook-test/' in webhook_url:
            logger.warning(f"Using test webhook URL. For production, use /webhook/ instead of /webhook-test/: {webhook_url}")
            # Optionally convert test to production
            webhook_url = webhook_url.replace('/webhook-test/', '/webhook/')
            logger.info(f"Converted test webhook to production: {webhook_url}")
        
        try:
            payload = {
                "itinerary": itinerary,
                "sources": sources,
                "email": email
            }
            
            logger.info(f"Calling n8n webhook: {webhook_url}")
            logger.debug(f"Payload: itinerary for {itinerary.get('city', 'unknown city')}, email: {email}")
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # PDF generation can take time - increased to 2 minutes
            )
            
            # Log response details for debugging
            logger.info(f"n8n webhook response status: {response.status_code}")
            
            response.raise_for_status()
            
            # Try to parse JSON response, but handle non-JSON responses
            result = {}
            try:
                # Check if response has content
                if response.text and response.text.strip():
                    result = response.json()
                else:
                    # Empty response - workflow may have completed but didn't return JSON
                    # This is common if "Respond to Webhook" node isn't properly configured
                    logger.warning(f"n8n webhook returned empty response (status {response.status_code}). "
                                 f"Workflow may have completed but 'Respond to Webhook' node might not be configured correctly.")
                    result = {
                        "status": "success" if response.status_code == 200 else "unknown",
                        "message": "PDF generation workflow completed (empty response received - check n8n execution for details)",
                        "email_sent": None,  # Unknown - cannot determine from empty response
                        "response_text": None
                    }
            except ValueError:
                # Response is not valid JSON
                result = {
                    "status": "success" if response.status_code == 200 else "unknown",
                    "message": f"n8n workflow responded with status {response.status_code} (non-JSON response)",
                    "email_sent": None,  # Unknown - cannot determine from non-JSON response
                    "response_text": response.text[:500] if response.text else None
                }
                logger.warning(f"n8n webhook returned non-JSON response: {response.text[:200] if response.text else 'empty'}")
            
            logger.info(f"n8n workflow completed: {result.get('status', 'unknown')}, email_sent: {result.get('email_sent')}")
            return result
        
        except requests.Timeout:
            logger.error(f"n8n webhook request timed out after 120 seconds")
            raise TravelAssistantException("PDF generation timed out. The workflow may be taking longer than expected.")
        except requests.RequestException as e:
            logger.error(f"n8n webhook request failed: {e}")
            error_message = f"Failed to generate PDF: {str(e)}"
            
            # Check for DNS resolution errors
            error_str = str(e).lower()
            if "getaddrinfo failed" in error_str or "name resolution" in error_str or "failed to resolve" in error_str:
                # Try to extract hostname for better error message
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(webhook_url)
                    hostname = parsed.hostname or "unknown"
                except:
                    hostname = "unknown"
                
                error_message = (
                    f"DNS resolution failed for n8n webhook URL: {webhook_url}\n\n"
                    f"Possible causes:\n"
                    f"1. The n8n instance domain is incorrect or doesn't exist\n"
                    f"2. Network connectivity issue - check your internet connection\n"
                    f"3. DNS server issue - try using a different DNS server (8.8.8.8 or 1.1.1.1)\n"
                    f"4. Firewall blocking the connection\n"
                    f"5. The n8n instance may have been deleted or the domain changed\n\n"
                    f"Troubleshooting steps:\n"
                    f"1. Test DNS resolution: Run 'nslookup {hostname}' or 'ping {hostname}'\n"
                    f"2. Try accessing https://{hostname} in your browser\n"
                    f"3. Verify the webhook URL in your .env file matches the Production URL from n8n\n"
                    f"4. Check if the n8n workflow is active (green toggle in n8n)\n"
                    f"5. Use the test endpoint: GET /api/test-n8n to diagnose the issue\n\n"
                    f"Original error: {str(e)}"
                )
            elif hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                response_text = e.response.text[:500]
                logger.error(f"Response status: {status_code}, Response text: {response_text}")
                
                # Provide helpful error messages for common issues
                if status_code == 404:
                    error_message = (
                        f"n8n webhook not found (404). Please check:\n"
                        f"1. The webhook URL is correct: {webhook_url}\n"
                        f"2. The n8n workflow is active (not paused)\n"
                        f"3. The webhook node is enabled in the workflow\n"
                        f"4. You're using the production webhook URL (not test webhook)\n"
                        f"Original error: {str(e)}"
                    )
                elif status_code == 401:
                    error_message = (
                        f"n8n webhook authentication failed (401). "
                        f"Please check if the webhook requires authentication. "
                        f"Original error: {str(e)}"
                    )
                elif status_code == 500:
                    error_message = (
                        f"n8n workflow error (500). The workflow may have an error. "
                        f"Check n8n execution logs. Original error: {str(e)}"
                    )
            
            raise TravelAssistantException(error_message)
        except Exception as e:
            logger.error(f"Unexpected error in n8n client: {e}", exc_info=True)
            raise TravelAssistantException(f"Unexpected error generating PDF: {str(e)}")


# Global n8n client instance
_n8n_client: Optional[N8nClient] = None


def get_n8n_client() -> Optional[N8nClient]:
    """
    Get or create global n8n client instance.
    
    Returns:
        N8nClient instance or None if not configured
    """
    global _n8n_client
    if _n8n_client is None and settings.n8n_webhook_url:
        _n8n_client = N8nClient()
    return _n8n_client
