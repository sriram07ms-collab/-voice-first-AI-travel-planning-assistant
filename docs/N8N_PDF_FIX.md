# n8n PDF Generation Node Fix

## Problem

The original workflow used `n8n-nodes-base.pdf` node which is not available in all n8n versions, causing the "Generate PDF" node to show a `?` icon and fail.

## Solution

The workflow has been updated to use an **HTTP Request** node that calls an external PDF generation API. This approach:

- ✅ Works with all n8n versions
- ✅ No additional n8n plugins required
- ✅ Supports multiple PDF service providers
- ✅ More reliable and maintainable

## Setup Options

### Option 1: htmlpdfapi.com (Recommended for Quick Start)

**Free Tier**: 100 PDFs/month

1. **Sign up**: Go to [htmlpdfapi.com](https://htmlpdfapi.com) and create a free account
2. **Get API Key**: Copy your API key from the dashboard
3. **Configure n8n**:
   - Go to Settings → Environment Variables
   - Add:
     - `PDF_API_URL` = `https://api.htmlpdfapi.com/v1/pdf`
     - `PDF_API_KEY` = `your-api-key-here`
4. **Test**: The workflow will now use htmlpdfapi.com

### Option 2: Gotenberg (Self-Hosted - Recommended for Production)

**Advantages**: 
- No API limits
- Full control
- No external dependencies
- Free and open-source

**Setup**:

1. **Run Gotenberg with Docker**:
```bash
docker run -d -p 3000:3000 gotenberg/gotenberg:7
```

2. **Configure n8n**:
   - Go to Settings → Environment Variables
   - Add:
     - `PDF_API_URL` = `http://localhost:3000/forms/chromium/convert/html`
     - `PDF_API_KEY` = (leave empty, not needed for Gotenberg)

3. **Update Workflow** (if using Gotenberg):
   - The HTTP Request node needs to use `multipart-form-data` instead of JSON
   - See "Gotenberg Configuration" section below

### Option 3: PDFShift (Paid Service)

**Pricing**: Starts at $9/month for 1,000 PDFs

1. **Sign up**: [pdfshift.io](https://pdfshift.io)
2. **Get API Key**: From dashboard
3. **Configure n8n**:
   - `PDF_API_URL` = `https://api.pdfshift.io/v3/convert/pdf`
   - `PDF_API_KEY` = `your-api-key`
   - Update HTTP Request node to use Basic Auth instead of header

### Option 4: Other PDF Services

Any PDF generation API that accepts HTML and returns PDF can be used:
- PaperAPI
- PDF Generator API
- Custom API endpoint

## Current Workflow Configuration

The workflow now uses:

**Node**: HTTP Request  
**Method**: POST  
**URL**: `{{ $env.PDF_API_URL || 'https://api.htmlpdfapi.com/v1/pdf' }}`  
**Headers**:
- `Content-Type`: `application/json`
- `X-API-Key`: `{{ $env.PDF_API_KEY }}`

**Body** (JSON):
```json
{
  "html": "{{ HTML content }}",
  "format": "A4",
  "margin": {
    "top": "20mm",
    "right": "20mm",
    "bottom": "20mm",
    "left": "20mm"
  },
  "printBackground": true
}
```

**Response**: Binary PDF file

## Gotenberg Configuration (Alternative)

If you prefer to use Gotenberg, update the HTTP Request node:

1. **Change Body Content Type**: `multipart-form-data`
2. **Update Body Parameters**:
   - `html`: `{{ $json.html }}`
   - `marginTop`: `0.787402` (20mm in inches)
   - `marginBottom`: `0.787402`
   - `marginLeft`: `0.787402`
   - `marginRight`: `0.787402`
   - `paperFormat`: `A4`
   - `printBackground`: `true`

3. **Remove API Key Header**: Gotenberg doesn't require authentication

## Testing

1. **Import Updated Workflow**: 
   - Delete old workflow
   - Import `n8n-workflows/pdf-email-workflow.json`

2. **Set Environment Variables**:
   ```env
   PDF_API_URL=https://api.htmlpdfapi.com/v1/pdf
   PDF_API_KEY=your-key-here
   SMTP_FROM_EMAIL=your-email@example.com
   ```

3. **Activate Workflow**

4. **Test with Sample Request**:
```bash
curl -X POST http://localhost:8000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "email": "test@example.com"
  }'
```

5. **Check n8n Executions**: 
   - Go to Executions tab
   - Verify "Generate PDF" node succeeds
   - Check for any errors

## Troubleshooting

### Error: "PDF_API_KEY is required"

**Solution**: Set `PDF_API_KEY` environment variable in n8n

### Error: "Failed to generate PDF: 401 Unauthorized"

**Solution**: 
- Verify API key is correct
- Check API key has not expired
- Ensure API key has proper permissions

### Error: "Failed to generate PDF: 429 Too Many Requests"

**Solution**: 
- You've exceeded free tier limits
- Upgrade plan or switch to Gotenberg (self-hosted)

### PDF is Generated but Email Fails

**Solution**:
- Check SMTP credentials
- Verify `SMTP_FROM_EMAIL` is set
- Check email is not in spam folder

### HTTP Request Node Shows Error

**Solution**:
- Verify `PDF_API_URL` is correct
- Check API endpoint is accessible
- Review n8n execution logs for detailed error

## Migration from Old Workflow

1. **Export Current Workflow** (backup)
2. **Delete Old "Generate PDF" Node**
3. **Import New Workflow** OR manually add HTTP Request node
4. **Configure Environment Variables**
5. **Test and Activate**

## Workflow Structure (Updated)

```
Webhook 
  → Generate HTML (Code Node)
  → Generate PDF (HTTP Request Node) ← FIXED
  → Send Email (Email Node)
  → Respond to Webhook
```

## Benefits of This Fix

1. ✅ **Universal Compatibility**: Works with all n8n versions
2. ✅ **No Plugin Dependencies**: Uses built-in HTTP Request node
3. ✅ **Flexible**: Easy to switch PDF providers
4. ✅ **Reliable**: External APIs are more stable
5. ✅ **Scalable**: Can handle high volumes
6. ✅ **Maintainable**: Standard HTTP requests are easier to debug

## Next Steps

1. Choose a PDF service provider (htmlpdfapi.com recommended for quick start)
2. Set up API key
3. Configure environment variables in n8n
4. Import updated workflow
5. Test and verify PDF generation works
6. Monitor usage and upgrade plan if needed

---

**Last Updated**: 2024-01-15  
**Status**: ✅ Fixed and Tested
