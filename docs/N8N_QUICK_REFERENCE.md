# n8n Integration Quick Reference

A quick reference guide for n8n integration setup and troubleshooting.

## 🚀 Quick Setup (5 Minutes)

### 1. Start n8n
```bash
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
```

### 2. Import Workflow
- Open `http://localhost:5678`
- Workflows → Import from File
- Select `n8n-workflows/pdf-email-workflow.json`
- Activate workflow

### 3. Configure Gmail SMTP
**Step 1: Get Gmail App Password**
- 📖 **Detailed Guide**: See [Gmail App Password Guide](./GMAIL_APP_PASSWORD_GUIDE.md) for step-by-step instructions
- Quick steps:
  - Go to [Google Account Security](https://myaccount.google.com/security)
  - Enable **2-Step Verification** (if not enabled)
  - Go to **App passwords** → Generate for "Mail" → Device "n8n"
  - Copy the 16-character password (remove spaces!)

**Step 2: Configure in n8n**
- Click "Send Email" node → Add Credential → SMTP Account
- **Host**: `smtp.gmail.com`
- **Port**: `587`
- **User**: Your Gmail address
- **Password**: App password (16-char, no spaces)
- **Secure**: TLS
- Set `SMTP_FROM_EMAIL` = Your Gmail address

### 4. Configure Backend
```env
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/generate-pdf
```

### 5. Test
```bash
curl -X POST http://localhost:8000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "email": "test@example.com"}'
```

---

## 📋 Workflow Nodes

| Node | Purpose | Key Settings |
|------|---------|--------------|
| **Webhook** | Receives POST request | Method: POST, Path: `generate-pdf` |
| **Generate HTML** | Creates HTML template | JavaScript code in node |
| **Generate PDF** | Converts HTML to PDF | Format: A4, Margins: 20mm |
| **Send Email** | Sends PDF attachment | SMTP credentials required |
| **Respond** | Returns response | JSON format |

---

## 🔧 Configuration

### Environment Variables

**Backend** (`.env`):
```env
N8N_WEBHOOK_URL=https://your-instance.n8n.cloud/webhook/generate-pdf
```

**n8n** (Settings → Environment Variables):
```env
SMTP_FROM_EMAIL=yourname@gmail.com
PDF_API_URL=https://api.htmlpdfapi.com/v1/pdf
PDF_API_KEY=your-pdf-api-key
```

### Gmail SMTP Settings

| Setting | Value | Required |
|---------|-------|----------|
| **Host** | `smtp.gmail.com` | ✅ Yes |
| **Port** | `587` (or `465` for SSL) | ✅ Yes |
| **User** | Your full Gmail address | ✅ Yes |
| **Password** | 16-character App Password | ✅ Yes |
| **Secure** | TLS (for port 587) or SSL (for port 465) | ✅ Yes |
| **Client Host Name** | Leave **empty** (or `localhost`) | ❌ Optional |

**⚠️ Important**: 
- Must use App Password, not regular Gmail password!
- **Client Host Name** can be left empty - Gmail doesn't require it

---

## 📡 API Endpoint

### Request
```bash
POST /api/generate-pdf
Content-Type: application/json

{
  "session_id": "abc123",
  "email": "user@example.com"
}
```

### Response (Success)
```json
{
  "status": "success",
  "message": "PDF generated and emailed successfully",
  "email_sent": true,
  "email_address": "user@example.com",
  "generated_at": "2024-01-15T12:00:00.000Z"
}
```

### Response (Error)
```json
{
  "status": "error",
  "error_type": "SESSION_NOT_FOUND",
  "message": "Session not found. Please plan a trip first."
}
```

---

## 🐛 Common Issues

### Webhook Not Working
- ✅ Check workflow is **Active**
- ✅ Verify webhook URL in backend `.env`
- ✅ Test webhook URL directly with curl

### Email Not Sending (Gmail)
- ✅ **Using App Password?** (not regular password)
- ✅ **2-Step Verification enabled?** (required for app passwords)
- ✅ **Port 587 with TLS?** (or 465 with SSL)
- ✅ **Check spam folder**
- ✅ **Verify `SMTP_FROM_EMAIL` matches Gmail address**
- ✅ **Test SMTP connection** in n8n node

### SSL/TLS Error - "wrong version number"
**Error**: `error:0A00010B:SSL routines:tls_validate_record_header:wrong version number`

**Fix**:
- ✅ **Port 587** must use **TLS** (not SSL)
- ✅ **Port 465** must use **SSL** (not TLS)
- ✅ Check port and security type match correctly
- ✅ Try switching: Port 465 + SSL if 587 + TLS doesn't work

### PDF Generation Fails
- ✅ Check HTML output in "Generate HTML" node
- ✅ Verify PDF node configuration
- ✅ Review n8n execution logs

### Backend 503 Error
- ✅ Check `N8N_WEBHOOK_URL` is set
- ✅ Restart backend after adding env var
- ✅ Verify URL format is correct

---

## 📁 File Locations

| File | Location |
|------|----------|
| Workflow JSON | `n8n-workflows/pdf-email-workflow.json` |
| Backend Client | `backend/src/services/n8n_client.py` |
| API Endpoint | `backend/src/main.py` (line ~177) |
| Frontend API | `frontend/src/services/api.ts` |
| Documentation | `docs/N8N_INTEGRATION_GUIDE.md` |

---

## 🔍 Testing Checklist

- [ ] n8n instance running
- [ ] Workflow imported and activated
- [ ] Webhook URL copied to backend `.env`
- [ ] Gmail App Password generated
- [ ] Gmail SMTP credentials configured in n8n
- [ ] `SMTP_FROM_EMAIL` environment variable set
- [ ] PDF API configured (htmlpdfapi.com or Gotenberg)
- [ ] Backend restarted
- [ ] Test request sent
- [ ] Email received with PDF (check spam if not in inbox)
- [ ] PDF opens correctly
- [ ] All itinerary data present

---

## 💡 Tips

1. **Always activate workflow** before testing
2. **Check n8n Executions** tab for detailed logs
3. **Test with simple payload** first
4. **Use Gmail App Password** (not regular password)
5. **Enable debug logging** in n8n for troubleshooting
6. **Export workflow** regularly for backup

---

## 📚 Full Documentation

For detailed information, see:
- **Complete Guide**: `docs/N8N_INTEGRATION_GUIDE.md`
- **Workflow README**: `n8n-workflows/README.md`
- **Phase 8 Completion**: `docs/PHASE8_COMPLETION.md`

---

## 🆘 Quick Commands

### Start n8n (Docker)
```bash
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
```

### Test Webhook
```bash
curl -X POST https://your-n8n-instance.com/webhook/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Check Backend Health
```bash
curl http://localhost:8000/health
```

### View n8n Logs
```bash
docker logs n8n
```

---

**Last Updated**: 2024-01-15
