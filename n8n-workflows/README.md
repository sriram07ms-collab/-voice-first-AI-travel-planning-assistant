# n8n Workflows

This directory contains n8n workflow definitions for the Travel Assistant.

## PDF & Email Workflow

**File:** `pdf-email-workflow.json`

### Workflow Steps

1. **Webhook Trigger** - Receives itinerary data from backend
2. **Generate HTML** - Creates HTML template for PDF
3. **Generate PDF** - Converts HTML to PDF using HTTP Request to PDF API (htmlpdfapi.com, Gotenberg, etc.)
4. **Send Email** - Sends PDF as attachment via SMTP
5. **Respond to Webhook** - Returns success/failure status

> **Note**: The PDF generation node has been fixed to use HTTP Request instead of the broken PDF node. See [PDF Fix Documentation](../docs/N8N_PDF_FIX.md) for setup instructions.

### Setup Instructions

1. **Import Workflow:**
   - Open n8n (self-hosted or n8n.cloud)
   - Click "Import from File"
   - Select `pdf-email-workflow.json`

2. **Configure Webhook:**
   - The webhook URL will be generated automatically
   - Copy the webhook URL
   - Set `N8N_WEBHOOK_URL` in backend `.env` file

3. **Configure Gmail SMTP (Recommended):**
   
   **Step 1: Enable Gmail App Password**
   - Go to your [Google Account](https://myaccount.google.com/)
   - Navigate to **Security** → **2-Step Verification** (enable if not already enabled)
   - Scroll down to **App passwords**
   - Click **Select app** → Choose "Mail"
   - Click **Select device** → Choose "Other (Custom name)" → Enter "n8n"
   - Click **Generate**
   - **Copy the 16-character app password** (you'll need this in n8n)
   
   **Step 2: Configure in n8n**
   - Click on the **"Send Email"** node in your workflow
   - Click **"Add Credential"** → Select **"SMTP Account"**
   - Fill in the following:
     - **Name**: `Gmail SMTP` (or any name you prefer)
     - **Host**: `smtp.gmail.com`
     - **Port**: `587`
     - **User**: Your Gmail address (e.g., `yourname@gmail.com`)
     - **Password**: The 16-character app password (NOT your regular Gmail password)
     - **Secure**: Select **TLS**
     - **Client Host Name**: Leave **empty** (optional - not required for Gmail)
   - Click **Save** to save the credential
   - The "Send Email" node should now show your Gmail credential
   
   **Important Notes:**
   - ⚠️ You MUST use an App Password, not your regular Gmail password
   - ⚠️ 2-Step Verification must be enabled on your Google account
   - ✅ The app password is a 16-character code (no spaces)

4. **Configure PDF Generation:**
   - Set up a PDF generation service (see [PDF Fix Guide](../docs/N8N_PDF_FIX.md))
   - **Option 1 (Quick Start)**: Use htmlpdfapi.com (free tier: 100 PDFs/month)
     - Sign up at [htmlpdfapi.com](https://htmlpdfapi.com)
     - Get your API key
   - **Option 2 (Production)**: Use Gotenberg (self-hosted, unlimited)
     - Run: `docker run -d -p 3000:3000 gotenberg/gotenberg:7`

5. **Environment Variables (n8n):**
   - `SMTP_FROM_EMAIL` - Your Gmail address (e.g., `yourname@gmail.com`)
   - `PDF_API_URL` - PDF generation API URL (default: `https://api.htmlpdfapi.com/v1/pdf`)
   - `PDF_API_KEY` - PDF API key (required for htmlpdfapi.com, not needed for Gotenberg)
   
   **To set environment variables in n8n:**
   - Go to **Settings** → **Environment Variables**
   - Click **Add Variable**
   - Add each variable with its value
   - Click **Save**

### Webhook Payload

The workflow expects a POST request with this structure:

```json
{
  "itinerary": {
    "city": "Jaipur",
    "duration_days": 3,
    "pace": "moderate",
    "day_1": {
      "morning": { "activities": [...] },
      "afternoon": { "activities": [...] },
      "evening": { "activities": [...] }
    },
    ...
  },
  "sources": [
    {
      "type": "openstreetmap",
      "poi": "Hawa Mahal",
      "source_id": "way:123456",
      "url": "..."
    },
    ...
  ],
  "email": "user@example.com"
}
```

### Response Format

```json
{
  "status": "success",
  "message": "PDF generated and emailed successfully",
  "email_sent": true,
  "email_address": "user@example.com",
  "generated_at": "2024-01-15T12:00:00.000Z"
}
```

### Alternative: Simplified Workflow

If you don't have n8n set up, you can use a simplified version that just returns the HTML for PDF generation on the backend side.

### Testing

1. Use the webhook URL in backend tests
2. Send a test request with sample itinerary data
3. Verify PDF is generated and email is sent

---

## Gmail SMTP Troubleshooting

### Common Issues:

**"Invalid login credentials"**
- ✅ Make sure you're using an **App Password**, not your regular Gmail password
- ✅ Verify 2-Step Verification is enabled on your Google account
- ✅ Check that the app password was copied correctly (16 characters, no spaces)

**"Connection timeout"**
- ✅ Verify port `587` is not blocked by firewall
- ✅ Try port `465` with SSL instead of TLS (if port 587 doesn't work)

**"Email not received"**
- ✅ Check spam/junk folder
- ✅ Verify `SMTP_FROM_EMAIL` matches your Gmail address
- ✅ Check n8n execution logs for detailed error messages

**"Authentication failed"**
- ✅ Regenerate app password if it's not working
- ✅ Make sure you selected "TLS" (not SSL) for port 587
- ✅ For port 465, use "SSL" instead

**SSL/TLS Error - "wrong version number"**
- ✅ **Port 587** must use **TLS** (NOT SSL)
- ✅ **Port 465** must use **SSL** (NOT TLS)
- ✅ Verify port and security type match exactly
- ✅ Common mistake: Using SSL with port 587 or TLS with port 465
- ✅ Fix: Edit SMTP credential and ensure correct combination

## Notes

- **PDF Generation**: The workflow uses HTTP Request node to call external PDF APIs (htmlpdfapi.com, Gotenberg, etc.)
- **No Plugin Required**: Uses built-in n8n nodes - works with all n8n versions
- **Email Provider**: Configured for Gmail SMTP (recommended for quick setup)
- **Alternative Email Providers**: Can be customized for SendGrid, Mailgun, etc. (see [Integration Guide](../docs/N8N_INTEGRATION_GUIDE.md))
- **Troubleshooting**: See [PDF Fix Guide](../docs/N8N_PDF_FIX.md) for common issues and solutions
