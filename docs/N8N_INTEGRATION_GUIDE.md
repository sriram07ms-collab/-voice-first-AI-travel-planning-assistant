# n8n Integration Guide

A comprehensive guide to integrating n8n workflows for PDF generation and email delivery in the Voice-First AI Travel Planning Assistant.

## 📋 Table of Contents

1. [Overview](#overview)
2. [What is n8n?](#what-is-n8n)
3. [Architecture](#architecture)
4. [Prerequisites](#prerequisites)
5. [Step-by-Step Setup](#step-by-step-setup)
6. [Workflow Details](#workflow-details)
7. [Backend Integration](#backend-integration)
8. [Frontend Integration](#frontend-integration)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Customization](#advanced-customization)
12. [Production Deployment](#production-deployment)

---

## Overview

The n8n integration enables automatic PDF generation and email delivery of travel itineraries. When a user completes their trip planning, they can request a PDF version of their itinerary, which is automatically generated and emailed to them.

### Key Features

- ✅ **Automated PDF Generation**: Converts itinerary data into a professional PDF document
- ✅ **Email Delivery**: Sends PDF as attachment via SMTP
- ✅ **Professional Formatting**: Beautiful, print-ready PDF with all trip details
- ✅ **Source Citations**: Includes all sources and references
- ✅ **Asynchronous Processing**: Non-blocking workflow execution

---

## What is n8n?

**n8n** is an open-source workflow automation tool that allows you to connect different services and automate tasks. Think of it as a visual programming tool where you can:

- Create workflows using a drag-and-drop interface
- Connect APIs, databases, and services
- Automate complex business processes
- Handle webhooks and API integrations

### Why n8n for This Project?

1. **Visual Workflow Design**: Easy to create and modify PDF generation workflows
2. **Built-in PDF Generation**: Native support for HTML-to-PDF conversion
3. **Email Integration**: Built-in SMTP and email service connectors
4. **Webhook Support**: Easy API integration with our backend
5. **Self-Hosted Option**: Can run on your own infrastructure
6. **Cost-Effective**: Open-source with optional cloud hosting

### n8n Options

- **n8n.cloud**: Managed hosting (paid, easy setup)
- **Self-Hosted**: Run on your own server (free, more control)
- **Docker**: Containerized deployment (recommended)

---

## Architecture

```
┌─────────────────┐
│   Frontend      │
│  (Next.js)      │
└────────┬────────┘
         │ POST /api/generate-pdf
         │ { session_id, email }
         ▼
┌─────────────────┐
│   Backend       │
│  (FastAPI)      │
│                 │
│  - Validates    │
│  - Retrieves    │
│    itinerary    │
│  - Calls n8n    │
└────────┬────────┘
         │ POST webhook
         │ { itinerary, sources, email }
         ▼
┌─────────────────┐
│   n8n Workflow  │
│                 │
│  1. Webhook     │
│  2. Generate    │
│     HTML        │
│  3. Generate    │
│     PDF         │
│  4. Send Email  │
│  5. Respond     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  User's Email   │
│  (PDF Attached) │
└─────────────────┘
```

### Data Flow

1. **User Request**: Frontend calls `/api/generate-pdf` with `session_id` and `email`
2. **Backend Processing**:
   - Validates session exists
   - Retrieves itinerary and sources from session
   - Calls n8n webhook with complete data
3. **n8n Workflow**:
   - Receives webhook payload
   - Generates HTML template from itinerary data
   - Converts HTML to PDF
   - Sends email with PDF attachment
   - Returns success response
4. **Response**: Backend returns status to frontend

---

## Prerequisites

Before setting up n8n integration, ensure you have:

### Required

- ✅ n8n instance (cloud or self-hosted)
- ✅ SMTP email account (Gmail, SendGrid, Mailgun, etc.)
- ✅ Backend server running
- ✅ Valid itinerary session

### Optional but Recommended

- ✅ Domain name (for production webhook URLs)
- ✅ SSL certificate (HTTPS for production)
- ✅ Email service API key (SendGrid, Mailgun for better deliverability)

---

## Step-by-Step Setup

### Step 1: Set Up n8n Instance

#### Option A: n8n.cloud (Easiest)

1. Go to [n8n.cloud](https://n8n.cloud)
2. Sign up for an account
3. Create a new workflow
4. Your webhook URL will be: `https://your-instance.n8n.cloud/webhook/...`

#### Option B: Self-Hosted with Docker (Recommended for Development)

1. **Install Docker** (if not already installed)

2. **Run n8n container**:
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

3. **Access n8n**: Open `http://localhost:5678` in your browser

4. **Create account**: First-time setup will prompt you to create an account

#### Option C: Docker Compose (Production-Ready)

Create `docker-compose.n8n.yml`:
```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your-secure-password
      - N8N_HOST=your-domain.com
      - N8N_PROTOCOL=https
    volumes:
      - n8n_data:/home/node/.n8n
    restart: unless-stopped

volumes:
  n8n_data:
```

Run with:
```bash
docker-compose -f docker-compose.n8n.yml up -d
```

---

### Step 2: Import Workflow

1. **Open n8n** (cloud or self-hosted)

2. **Import Workflow**:
   - Click "Workflows" → "Import from File"
   - Select `n8n-workflows/pdf-email-workflow.json`
   - Click "Import"

3. **Verify Workflow**:
   - You should see 5 nodes:
     1. Webhook (trigger)
     2. Generate HTML (Code node)
     3. Generate PDF (PDF node)
     4. Send Email (Email node)
     5. Respond to Webhook (Response node)

---

### Step 3: Configure Webhook

1. **Click on "Webhook" node**

2. **Configure Settings**:
   - **HTTP Method**: POST
   - **Path**: `generate-pdf` (or leave default)
   - **Response Mode**: "Respond to Webhook"
   - **Authentication**: None (or add if needed)

3. **Activate Workflow**:
   - Toggle "Active" switch in top-right
   - Copy the **Webhook URL** (e.g., `https://your-instance.n8n.cloud/webhook/generate-pdf`)

4. **Save Webhook URL**:
   - You'll need this for backend configuration

---

### Step 4: Configure Gmail SMTP (Recommended)

**Gmail SMTP is recommended for quick setup and testing. Follow these steps:**

#### Step 4.1: Enable Gmail App Password

1. **Go to Google Account**:
   - Visit [myaccount.google.com](https://myaccount.google.com/)
   - Sign in with your Gmail account

2. **Enable 2-Step Verification** (if not already enabled):
   - Click **Security** in the left sidebar
   - Under "Signing in to Google", click **2-Step Verification**
   - Follow the prompts to enable it
   - This is **required** to generate app passwords

3. **Generate App Password**:
   - Go back to **Security** page
   - Scroll down to **"App passwords"** section
   - Click **App passwords**
   - You may need to sign in again
   - Click **Select app** dropdown → Choose **"Mail"**
   - Click **Select device** dropdown → Choose **"Other (Custom name)"**
   - Type: `n8n` (or any name you prefer)
   - Click **Generate**
   - **IMPORTANT**: Copy the 16-character password immediately (it won't be shown again)
   - The password looks like: `abcd efgh ijkl mnop` (remove spaces when using)

#### Step 4.2: Configure in n8n

1. **Open Workflow**:
   - In n8n, open your imported workflow
   - Click on the **"Send Email"** node

2. **Add SMTP Credential**:
   - Click **"Add Credential"** button
   - Select **"SMTP Account"** from the list
   - Fill in the credential form:
     - **Name**: `Gmail SMTP` (or any descriptive name)
     - **Host**: `smtp.gmail.com`
     - **Port**: `587`
     - **User**: Your full Gmail address (e.g., `yourname@gmail.com`)
     - **Password**: The 16-character app password (paste without spaces)
     - **Secure**: Select **TLS** from dropdown
     - **Client Host Name**: Leave **empty** (optional - Gmail doesn't require this)
   - Click **Save** to save the credential

3. **Verify Configuration**:
   - The "Send Email" node should now show your Gmail credential
   - The "From Email" field should use: `{{ $env.SMTP_FROM_EMAIL || 'yourname@gmail.com' }}`

#### Step 4.3: Set Environment Variable

1. **In n8n Settings**:
   - Go to **Settings** → **Environment Variables**
   - Click **Add Variable**
   - **Name**: `SMTP_FROM_EMAIL`
   - **Value**: Your Gmail address (e.g., `yourname@gmail.com`)
   - Click **Save**

**Important Notes:**
- ⚠️ **Never use your regular Gmail password** - it won't work and may lock your account
- ⚠️ **App passwords are required** - Gmail doesn't allow regular passwords for SMTP
- ✅ **App passwords are secure** - they can be revoked individually if compromised
- ✅ **Port 587 with TLS** is recommended (alternative: port 465 with SSL)

#### Alternative Email Providers

If you prefer not to use Gmail, here are alternatives:

**Option B: SendGrid** (Paid service, better for production)

1. **Create SendGrid Account**: [sendgrid.com](https://sendgrid.com)
2. **Generate API Key**: Settings → API Keys → Create API Key
3. **In n8n**: Use "SendGrid" node instead of "Send Email"

**Option C: Mailgun** (Paid service)

1. **Create Mailgun Account**: [mailgun.com](https://mailgun.com)
2. **Get SMTP Credentials**: Domain → SMTP credentials
3. **In n8n**: Use "Mailgun" node or SMTP with Mailgun credentials

**Option D: Other SMTP Providers**

Any SMTP service can be used with the "Send Email" node:
- Outlook/Hotmail: `smtp-mail.outlook.com:587`
- Yahoo: `smtp.mail.yahoo.com:587`
- Custom SMTP server

---

### Step 5: Configure Environment Variables

In n8n, set environment variables:

1. **Go to Settings** → **Environment Variables**

2. **Add Required Variables**:
   - **Name**: `SMTP_FROM_EMAIL`
     - **Value**: Your Gmail address (e.g., `yourname@gmail.com`)
   - **Name**: `PDF_API_URL` (optional, has default)
     - **Value**: `https://api.htmlpdfapi.com/v1/pdf`
   - **Name**: `PDF_API_KEY` (required if using htmlpdfapi.com)
     - **Value**: Your PDF API key

3. **Save** all variables

---

### Step 6: Configure Backend

1. **Update `.env` file** in `backend/`:

```env
N8N_WEBHOOK_URL=https://your-instance.n8n.cloud/webhook/generate-pdf
```

2. **Restart Backend**:
```bash
cd backend
python -m uvicorn src.main:app --reload
```

3. **Verify Configuration**:
```bash
# Check if environment variable is loaded
curl http://localhost:8000/health
```

---

### Step 7: Test the Integration

1. **Create a Test Session**:
   - Use the frontend or API to plan a trip
   - Note the `session_id`

2. **Call PDF Endpoint**:
```bash
curl -X POST http://localhost:8000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "email": "test@example.com"
  }'
```

3. **Check Email**: You should receive the PDF within a few seconds

4. **Check n8n Execution**: In n8n, go to "Executions" to see workflow runs

---

## Workflow Details

### Workflow Structure

The n8n workflow consists of 5 nodes:

```
Webhook → Generate HTML → Generate PDF → Send Email → Respond
```

### Node 1: Webhook Trigger

**Purpose**: Receives POST request from backend

**Configuration**:
- **HTTP Method**: POST
- **Path**: `generate-pdf`
- **Response Mode**: Respond to Webhook

**Expected Payload**:
```json
{
  "itinerary": {
    "city": "Jaipur",
    "duration_days": 3,
    "pace": "moderate",
    "day_1": {
      "morning": {
        "activities": [
          {
            "activity": "Hawa Mahal",
            "time": "09:00",
            "duration_minutes": 60,
            "travel_time_from_previous": 0,
            "description": "Famous palace..."
          }
        ]
      },
      "afternoon": { "activities": [...] },
      "evening": { "activities": [...] }
    },
    "day_2": { ... },
    "day_3": { ... }
  },
  "sources": [
    {
      "type": "openstreetmap",
      "poi": "Hawa Mahal",
      "source_id": "way:123456",
      "url": "https://www.openstreetmap.org/way/123456"
    }
  ],
  "email": "user@example.com"
}
```

### Node 2: Generate HTML

**Purpose**: Creates HTML template from itinerary data

**Type**: Code Node (JavaScript)

**Code**: See `pdf-email-workflow.json` for full implementation

**Output**: HTML string with:
- Professional header
- Day-wise sections
- Time blocks (Morning/Afternoon/Evening)
- Activity details
- Sources section
- Styled with CSS

**Key Features**:
- Responsive design
- Print-friendly styling
- Icons for time blocks
- Clickable source links

### Node 3: Generate PDF

**Purpose**: Converts HTML to PDF

**Type**: PDF Node

**Configuration**:
- **Operation**: Generate from HTML
- **Format**: A4
- **Margins**: 20mm all sides
- **Print Background**: Enabled

**Output**: Binary PDF data

### Node 4: Send Email

**Purpose**: Sends PDF as email attachment

**Type**: Email Send Node

**Configuration**:
- **From**: `{{ $env.SMTP_FROM_EMAIL }}`
- **To**: `{{ $json.email }}`
- **Subject**: `Your Travel Itinerary: {{ city }}`
- **Body**: Text summary
- **Attachments**: PDF binary data

**Email Template**:
```
Please find your travel itinerary attached.

Trip: [City]
Duration: [X] days

Enjoy your trip!
```

### Node 5: Respond to Webhook

**Purpose**: Returns response to backend

**Type**: Respond to Webhook Node

**Response Format**:
```json
{
  "status": "success",
  "message": "PDF generated and emailed successfully",
  "email_sent": true,
  "email_address": "user@example.com",
  "generated_at": "2024-01-15T12:00:00.000Z"
}
```

---

## Backend Integration

### n8n Client Service

**File**: `backend/src/services/n8n_client.py`

**Class**: `N8nClient`

**Key Method**:
```python
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
```

**Usage**:
```python
from src.services.n8n_client import get_n8n_client

n8n_client = get_n8n_client()
if n8n_client:
    result = n8n_client.generate_pdf_and_email(
        itinerary=itinerary,
        sources=sources,
        email="user@example.com"
    )
```

### API Endpoint

**Endpoint**: `POST /api/generate-pdf`

**Request Model**:
```python
class GeneratePDFRequest(BaseModel):
    session_id: str
    email: Optional[str] = None
```

**Response Model**:
```python
class PDFResponse(BaseModel):
    status: str
    message: str
    email_sent: bool
    pdf_url: Optional[str] = None
    email_address: Optional[str] = None
    generated_at: Optional[str] = None
```

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123",
    "email": "user@example.com"
  }'
```

**Example Response**:
```json
{
  "status": "success",
  "message": "PDF generated and emailed successfully",
  "email_sent": true,
  "email_address": "user@example.com",
  "generated_at": "2024-01-15T12:00:00.000Z"
}
```

### Error Handling

The backend handles various error scenarios:

1. **Session Not Found** (404):
```json
{
  "status": "error",
  "error_type": "SESSION_NOT_FOUND",
  "message": "Session not found. Please plan a trip first."
}
```

2. **No Itinerary** (400):
```json
{
  "status": "error",
  "error_type": "NO_ITINERARY",
  "message": "No itinerary found. Please plan a trip first."
}
```

3. **n8n Not Configured** (503):
```json
{
  "status": "error",
  "error_type": "SERVICE_UNAVAILABLE",
  "message": "PDF generation service is not configured. Please set N8N_WEBHOOK_URL."
}
```

4. **PDF Generation Failed** (500):
```json
{
  "status": "error",
  "error_type": "PDF_GENERATION_FAILED",
  "message": "Failed to generate PDF: [error details]"
}
```

---

## Frontend Integration

### API Client

**File**: `frontend/src/services/api.ts`

**Method**:
```typescript
async generatePDF(request: GeneratePDFRequest): Promise<PDFResponse> {
  const response = await this.client.post<PDFResponse>(
    '/api/generate-pdf',
    request
  );
  return response.data;
}
```

### Usage in Components

**Example**: Add PDF generation button to itinerary view

```typescript
import { apiClient } from '@/services/api';
import { useState } from 'react';

function ItineraryView({ sessionId }: { sessionId: string }) {
  const [generating, setGenerating] = useState(false);
  const [email, setEmail] = useState('');

  const handleGeneratePDF = async () => {
    if (!email) {
      alert('Please enter your email address');
      return;
    }

    setGenerating(true);
    try {
      const result = await apiClient.generatePDF({
        session_id: sessionId,
        email: email
      });

      if (result.email_sent) {
        alert(`PDF sent to ${result.email_address}!`);
      }
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div>
      {/* Itinerary display */}
      
      <div className="pdf-section">
        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button
          onClick={handleGeneratePDF}
          disabled={generating}
        >
          {generating ? 'Generating...' : 'Generate PDF'}
        </button>
      </div>
    </div>
  );
}
```

### TypeScript Types

**File**: `frontend/src/types/index.ts`

```typescript
export interface GeneratePDFRequest {
  session_id: string;
  email?: string;
}

export interface PDFResponse {
  status: string;
  message: string;
  email_sent: boolean;
  pdf_url?: string;
  email_address?: string;
  generated_at?: string;
}
```

---

## Testing

### Unit Tests

**File**: `tests/test_phase8.py`

**Test Cases**:
1. ✅ n8n Client Initialization
2. ✅ n8n Client (No URL) - Error handling
3. ✅ n8n Workflow File - JSON validation
4. ✅ PDF Endpoint Integration - Models validation

**Run Tests**:
```bash
cd tests
pytest test_phase8.py -v
```

### Integration Testing

#### Test 1: End-to-End PDF Generation

```bash
# 1. Start backend
cd backend
python -m uvicorn src.main:app --reload

# 2. Plan a trip (create session)
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "user_input": "Plan a 3-day trip to Jaipur"
  }'

# 3. Generate PDF
curl -X POST http://localhost:8000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "email": "test@example.com"
  }'

# 4. Check email inbox
# 5. Verify PDF attachment
```

#### Test 2: Error Scenarios

```bash
# Test missing session
curl -X POST http://localhost:8000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "non-existent",
    "email": "test@example.com"
  }'
# Expected: 404 error

# Test missing n8n URL
# Remove N8N_WEBHOOK_URL from .env
# Expected: 503 error
```

#### Test 3: n8n Workflow Execution

1. **Open n8n** → **Executions**
2. **Trigger workflow manually**:
   - Click "Execute Workflow"
   - Use test payload from workflow documentation
3. **Verify**:
   - HTML generation works
   - PDF is created
   - Email is sent
   - Response is returned

### Manual Testing Checklist

- [ ] Webhook receives POST request
- [ ] HTML template is generated correctly
- [ ] PDF is created with proper formatting
- [ ] Email is sent with PDF attachment
- [ ] Response is returned to backend
- [ ] Error handling works for invalid sessions
- [ ] Error handling works for missing n8n configuration
- [ ] Email validation works
- [ ] PDF contains all itinerary data
- [ ] Sources are included in PDF

---

## Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Requests

**Symptoms**: n8n workflow doesn't trigger

**Solutions**:
- ✅ Check webhook URL is correct in backend `.env`
- ✅ Verify workflow is **Active** in n8n
- ✅ Check n8n logs for errors
- ✅ Test webhook URL directly:
```bash
curl -X POST https://your-n8n-instance.com/webhook/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

#### 2. PDF Generation Fails

**Symptoms**: Workflow stops at PDF node

**Solutions**:
- ✅ Check HTML output from "Generate HTML" node
- ✅ Verify PDF node configuration (format, margins)
- ✅ Check n8n execution logs
- ✅ Ensure Puppeteer dependencies are installed (if self-hosted)

#### 3. Email Not Sending

**Symptoms**: PDF generated but email not received

**Solutions**:
- ✅ Verify SMTP credentials are correct
- ✅ Check email is not in spam folder
- ✅ Test SMTP connection separately
- ✅ Verify `SMTP_FROM_EMAIL` environment variable
- ✅ Check email service quotas/limits
- ✅ Review n8n execution logs for email errors

#### 4. Backend Returns 503 Error

**Symptoms**: "PDF generation service is not configured"

**Solutions**:
- ✅ Check `N8N_WEBHOOK_URL` is set in `.env`
- ✅ Restart backend after adding environment variable
- ✅ Verify URL format is correct
- ✅ Check backend logs for configuration errors

#### 5. Session Not Found Error

**Symptoms**: 404 error when calling PDF endpoint

**Solutions**:
- ✅ Ensure trip is planned first (session exists)
- ✅ Verify `session_id` is correct
- ✅ Check session hasn't expired
- ✅ Review conversation manager logs

#### 6. HTML Template Issues

**Symptoms**: PDF formatting is incorrect

**Solutions**:
- ✅ Check HTML output in n8n "Generate HTML" node
- ✅ Verify CSS styles are included
- ✅ Test HTML in browser first
- ✅ Adjust PDF node margins if needed

### Debugging Tips

1. **Enable n8n Debug Mode**:
   - Settings → Log Level → Debug
   - Review detailed execution logs

2. **Test Individual Nodes**:
   - Click "Execute Node" on each node
   - Verify output at each step

3. **Check Backend Logs**:
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m uvicorn src.main:app --reload
```

4. **Inspect Webhook Payload**:
   - Add a "Set" node after Webhook
   - Log the payload to see what's received

5. **Test Email Separately**:
   - Create a simple workflow with just email node
   - Test SMTP connection independently

---

## Advanced Customization

### Custom PDF Template

**Modify HTML Generation**:

1. **Open n8n workflow**
2. **Click "Generate HTML" node**
3. **Edit JavaScript code**:
   - Customize CSS styles
   - Add logos or branding
   - Modify layout structure
   - Add additional sections

**Example**: Add company logo
```javascript
html += `
  <div class="header">
    <img src="https://your-domain.com/logo.png" alt="Logo" style="height: 50px;">
    <h1>Trip to ${city}</h1>
  </div>
`;
```

### Multiple Email Recipients

**Modify "Send Email" node**:

```javascript
// In Generate HTML node, support multiple emails
const emails = Array.isArray(body.email) ? body.email : [body.email];

// In Send Email node, use loop or multiple email nodes
```

### PDF Download URL (Alternative to Email)

**Add HTTP Request Node**:

1. **After PDF generation**, upload to cloud storage (S3, Google Cloud Storage)
2. **Get public URL**
3. **Return URL in response** instead of emailing

**Example**:
```javascript
// Upload to S3
const s3Url = await uploadToS3(pdfBuffer, 'itineraries/');

// Return in response
return {
  status: 'success',
  pdf_url: s3Url,
  download_url: s3Url
};
```

### Custom Email Templates

**Modify "Send Email" node**:

- Use HTML email body
- Add personalized greeting
- Include trip summary
- Add social media links

**Example**:
```javascript
const emailBody = `
  <html>
    <body>
      <h2>Hello!</h2>
      <p>Your ${durationDays}-day trip to ${city} itinerary is ready!</p>
      <p>Please find the PDF attached.</p>
      <p>Have a great trip!</p>
    </body>
  </html>
`;
```

### Error Notifications

**Add Error Handling Node**:

1. **Add "IF" node** after each step
2. **Check for errors**
3. **Send notification** (email, Slack, etc.) on failure

**Example**:
```
Generate PDF → IF (error) → Send Error Email → Stop
                ↓ (success)
            Send Email
```

### Workflow Versioning

**Best Practices**:
- Export workflows regularly
- Version control workflow JSON files
- Test changes in separate workflow first
- Document changes in workflow notes

---

## Production Deployment

### Security Considerations

1. **Webhook Authentication**:
   - Add authentication to webhook node
   - Use API keys or tokens
   - Validate requests in backend

2. **HTTPS Only**:
   - Use HTTPS for all webhook URLs
   - SSL certificates for n8n instance
   - Secure SMTP connections

3. **Environment Variables**:
   - Never commit credentials
   - Use secure secret management
   - Rotate credentials regularly

4. **Rate Limiting**:
   - Implement rate limiting in backend
   - Monitor n8n execution limits
   - Set up alerts for abuse

### Monitoring

1. **n8n Execution Monitoring**:
   - Monitor workflow execution times
   - Set up alerts for failures
   - Track success rates

2. **Backend Monitoring**:
   - Log all PDF generation requests
   - Monitor error rates
   - Track response times

3. **Email Delivery Monitoring**:
   - Track email delivery rates
   - Monitor bounce rates
   - Set up alerts for failures

### Scaling

1. **n8n Instance**:
   - Use n8n.cloud for automatic scaling
   - Or scale Docker containers
   - Load balance if needed

2. **Backend**:
   - Handle concurrent PDF requests
   - Implement request queuing if needed
   - Cache session data

3. **Email Service**:
   - Use dedicated email service (SendGrid, Mailgun)
   - Monitor sending quotas
   - Implement retry logic

### Backup and Recovery

1. **Workflow Backup**:
   - Export workflows regularly
   - Version control workflow files
   - Document configuration

2. **Data Backup**:
   - Backup n8n data directory
   - Backup backend session data
   - Test recovery procedures

---

## Summary

This guide covers:

✅ **Complete n8n setup** (cloud and self-hosted)  
✅ **Workflow configuration** and customization  
✅ **Backend integration** with error handling  
✅ **Frontend integration** examples  
✅ **Testing strategies** and troubleshooting  
✅ **Advanced customization** options  
✅ **Production deployment** best practices  

### Quick Reference

- **Workflow File**: `n8n-workflows/pdf-email-workflow.json`
- **Backend Client**: `backend/src/services/n8n_client.py`
- **API Endpoint**: `POST /api/generate-pdf`
- **Environment Variable**: `N8N_WEBHOOK_URL`

### Next Steps

1. ✅ Set up n8n instance
2. ✅ Import workflow
3. ✅ Configure SMTP
4. ✅ Test integration
5. ✅ Deploy to production

---

**Need Help?** Check the troubleshooting section or review the execution logs in n8n for detailed error messages.
