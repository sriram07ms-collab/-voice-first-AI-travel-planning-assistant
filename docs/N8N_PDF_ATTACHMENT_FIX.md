# n8n PDF Attachment Fix

## Problem
Email is being sent successfully, but the PDF attachment is missing.

## Root Cause
The PDF attachment reference in the "Send Email" node was incorrect. The binary data from the "Generate PDF" node needs to be accessed correctly.

**Key Issue**: When the HTTP Request node has `outputPropertyName: "data"`, the binary data structure becomes nested. Instead of `$binary.data`, you need to access it as `$binary.data.data` because:
- The HTTP Request node stores the binary response in a property named "data" (as specified by `outputPropertyName`)
- This creates a nested structure: `$binary.data.data` where:
  - `$binary.data` is the property name from the HTTP Request node
  - `.data` is the actual binary data within that property

## Solution Applied

### 1. Fixed Attachment Reference

**Before (Incorrect):**
```javascript
"attachments": "={{ [{ name: 'itinerary.pdf', data: $('Generate PDF').binary.data, type: 'application/pdf' }] }}"
```

**After (Correct):**
```javascript
"attachments": "={{ (() => {
  try {
    // The Generate PDF node outputs binary data with property name 'data'
    // When outputPropertyName is 'data', binary is accessed as $binary.data.data
    
    // Primary method: $binary.data.data (recommended in n8n docs)
    if ($binary && $binary.data && $binary.data.data) {
      return [{
        name: 'itinerary.pdf',
        data: $binary.data.data,
        type: 'application/pdf'
      }];
    }
    
    // Fallback 1: Direct node reference $('Generate PDF').item.binary.data
    const pdfNode = $('Generate PDF');
    if (pdfNode && pdfNode.item && pdfNode.item.binary && pdfNode.item.binary.data) {
      const binaryData = pdfNode.item.binary.data.data || pdfNode.item.binary.data;
      return [{
        name: 'itinerary.pdf',
        data: binaryData,
        type: 'application/pdf'
      }];
    }
    
    // Fallback 2: Try $binary.data (for different n8n versions)
    if ($binary && $binary.data) {
      return [{
        name: 'itinerary.pdf',
        data: $binary.data,
        type: 'application/pdf'
      }];
    }
    
    // Fallback 3: Try input item binary
    if ($input && $input.item && $input.item.binary && $input.item.binary.data) {
      const inputBinary = $input.item.binary.data.data || $input.item.binary.data;
      return [{
        name: 'itinerary.pdf',
        data: inputBinary,
        type: 'application/pdf'
      }];
    }
    
    console.log('WARNING: PDF binary data not found - email will be sent without attachment');
    console.log('Binary keys:', $binary ? Object.keys($binary) : 'no binary');
    
    // Return empty array - email will be sent without PDF
    return [];
  } catch (error) {
    console.log('Error in attachment configuration:', error.message);
    return [];
  }
})() }}"
```

### 2. Verify PDF Generation Node

Ensure the "Generate PDF" HTTP Request node has:
- **Response Format**: Set to "File"
- **Output Property Name**: `data`
- **Timeout**: 30 seconds (added)

### 3. Check PDF API Configuration

The PDF generation requires:
- **PDF_API_URL**: Set in n8n environment variables
- **PDF_API_KEY**: Set in n8n environment variables (if using PDFShift)

## How to Apply the Fix

### Step 1: Update the Workflow

1. **Open your n8n workflow**: "Travel Itinerary PDF & Email"
2. **Click on "Send Email" node**
3. **Find the "Attachments" field**
4. **Replace the attachments expression** with the updated code from above
5. **Save the workflow**

### Step 2: Verify PDF Generation

1. **Check "Generate PDF" node**:
   - Response Format should be "File"
   - Output Property Name should be "data"
   - Timeout should be set (30 seconds)

2. **Test the workflow**:
   - Generate a test itinerary
   - Check n8n execution logs
   - Verify "Generate PDF" node succeeds
   - Check if binary data is present

### Step 3: Check PDF API

If PDF generation is failing:

1. **Check PDF API credentials**:
   - Go to n8n Settings → Environment Variables
   - Verify `PDF_API_URL` is set
   - Verify `PDF_API_KEY` is set (if required)

2. **Test PDF API directly**:
   ```bash
   curl -X POST https://api.pdfshift.io/v3/convert/pdf \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_API_KEY" \
     -d '{
       "source": "<html><body><h1>Test</h1></body></html>"
     }' \
     --output test.pdf
   ```

## Troubleshooting

### Issue: PDF still not attaching

**Check n8n execution logs:**
1. Go to n8n → Executions
2. Find the latest execution
3. Click on "Generate PDF" node
4. Check:
   - Status (should be green/success)
   - Response (should show binary data)
   - Error messages (if any)

**Check "Send Email" node:**
1. Click on "Send Email" node in execution
2. Check console output for warnings
3. Verify attachments array is not empty

### Issue: PDF API returning error

**Common errors:**
- `401 Unauthorized` → API key is incorrect or missing
- `429 Too Many Requests` → API quota exceeded
- `500 Internal Server Error` → API service issue

**Solutions:**
- Verify API key in n8n environment variables
- Check API quota/limits
- Try a different PDF service (htmlpdfapi.com, Gotenberg)

### Issue: Binary data not flowing

**Possible causes:**
1. PDF generation node not outputting binary correctly
2. Node connection issue
3. Binary data format incorrect

**Solutions:**
1. Verify "Generate PDF" node Response Format is "File"
2. Check node connections in workflow
3. Test PDF generation node individually

## Testing

After applying the fix:

1. **Generate a test itinerary** in your app
2. **Click "Generate PDF & Send Email"**
3. **Check your email**:
   - Should receive email with subject "Your Travel Itinerary: [City]"
   - Email body should contain full itinerary
   - **PDF attachment should be present** ✅

4. **Check n8n execution**:
   - All nodes should be green (success)
   - No errors in console
   - Binary data should be present in "Generate PDF" node

## Expected Result

✅ Email received with:
- Full itinerary content in HTML format
- PDF attachment named "itinerary.pdf"
- Proper formatting and styling

---

**Last Updated**: 2024-01-17  
**Status**: ✅ Fixed
