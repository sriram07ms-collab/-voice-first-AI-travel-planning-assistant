# Gmail App Password - Step-by-Step Guide

A detailed guide to generate a Gmail App Password for n8n SMTP configuration.

## 📋 Prerequisites

Before generating an App Password, you need:
- ✅ A Gmail account
- ✅ 2-Step Verification enabled on your Google Account

---

## 🚀 Step-by-Step Instructions

### Step 1: Sign in to Your Google Account

1. **Open your web browser**
2. **Go to**: [myaccount.google.com](https://myaccount.google.com)
3. **Sign in** with your Gmail account credentials

---

### Step 2: Navigate to Security Settings

1. **Look at the left sidebar** (or top menu on mobile)
2. **Click on "Security"** (it has a shield icon 🔒)
3. You'll see various security options

---

### Step 3: Enable 2-Step Verification (If Not Already Enabled)

**⚠️ IMPORTANT**: App Passwords can only be created if 2-Step Verification is enabled.

#### Check if 2-Step Verification is Enabled:

1. **Scroll down** on the Security page
2. **Look for "2-Step Verification"** section
3. **Check the status**:
   - ✅ **If it says "On"** → You can skip to Step 4
   - ❌ **If it says "Off"** → Follow the steps below to enable it

#### Enable 2-Step Verification:

1. **Click on "2-Step Verification"**
2. **Click "Get Started"** button
3. **Enter your password** if prompted
4. **Choose your phone number** (or add one)
5. **Choose verification method**:
   - **Text message** (SMS) - Recommended
   - **Phone call**
   - **Authenticator app** (Google Authenticator, etc.)
6. **Enter the verification code** sent to your phone
7. **Click "Turn On"**
8. **Click "Done"**

✅ **2-Step Verification is now enabled!**

---

### Step 4: Generate App Password

1. **Go back to the Security page**:
   - Click "Security" in the left sidebar
   - Or go back to [myaccount.google.com/security](https://myaccount.google.com/security)

2. **Scroll down** to find **"App passwords"** section
   - It's located under "Signing in to Google"
   - You may need to scroll past "2-Step Verification"

3. **Click on "App passwords"**
   - You might be asked to sign in again for security

4. **If you see "App passwords aren't available"**:
   - This means 2-Step Verification is not enabled
   - Go back to Step 3 and enable it first

---

### Step 5: Create the App Password

1. **Select App**:
   - Click the dropdown that says **"Select app"**
   - Choose **"Mail"** from the list
   - (If "Mail" is not visible, choose "Other (Custom name)")

2. **Select Device**:
   - Click the dropdown that says **"Select device"**
   - Choose **"Other (Custom name)"**
   - A text box will appear

3. **Enter Custom Name**:
   - Type: **"n8n"** (or any name you prefer, like "Travel Assistant")
   - This helps you identify what this password is for

4. **Generate Password**:
   - Click the **"Generate"** button

---

### Step 6: Copy Your App Password

**⚠️ CRITICAL**: Copy this password immediately! You won't be able to see it again.

1. **You'll see a 16-character password** displayed
   - It looks like: `abcd efgh ijkl mnop`
   - Format: 4 groups of 4 characters, separated by spaces

2. **Copy the password**:
   - **Option 1**: Click the **"Copy"** button (if available)
   - **Option 2**: Select all text and copy (Ctrl+C / Cmd+C)
   - **Option 3**: Write it down temporarily (but delete it after use!)

3. **Important Notes**:
   - ⚠️ **Remove spaces** when using in n8n (it should be 16 characters without spaces)
   - ⚠️ **Don't share** this password with anyone
   - ⚠️ **Store it securely** until you've configured n8n

4. **Click "Done"** to close the dialog

---

## 📝 Visual Guide (What You'll See)

### Security Page Layout:
```
Google Account
├── Personal info
├── Data & privacy
├── Security ← Click here
│   ├── How you sign in to Google
│   │   ├── Password
│   │   ├── 2-Step Verification ← Must be ON
│   │   └── App passwords ← Click here
│   └── ...
```

### App Password Generation Form:
```
App passwords

Select app: [Mail ▼]
Select device: [Other (Custom name) ▼]
Custom name: [n8n____________]

[Generate] button
```

### Generated Password Display:
```
Your app password for Mail on n8n:

abcd efgh ijkl mnop

[Copy] [Done]
```

---

## 🔧 Using the App Password in n8n

### Step 1: Open n8n Workflow

1. **Open your n8n instance**
2. **Open the workflow** (Travel Itinerary PDF & Email)
3. **Click on the "Send Email" node**

### Step 2: Add SMTP Credential

1. **Click "Add Credential"** button
2. **Select "SMTP Account"** from the list

### Step 3: Fill in Gmail SMTP Settings

Fill in the form with these values:

| Field | Value | Required |
|-------|-------|----------|
| **Name** | `Gmail SMTP` (or any name) | ✅ Yes |
| **Host** | `smtp.gmail.com` | ✅ Yes |
| **Port** | `587` | ✅ Yes |
| **User** | Your Gmail address (e.g., `yourname@gmail.com`) | ✅ Yes |
| **Password** | The 16-character app password (remove spaces!) | ✅ Yes |
| **Secure** | `TLS` | ✅ Yes |
| **Client Host Name** | Leave **empty** or use `localhost` | ❌ Optional |

**Note on Client Host Name**:
- This field is **optional** for Gmail SMTP
- You can **leave it empty** (recommended)
- If required by n8n, use: `localhost` or your server's hostname
- Gmail doesn't require this field, so leaving it blank is fine

**Example Password Entry**:
- ❌ **Wrong**: `abcd efgh ijkl mnop` (with spaces)
- ✅ **Correct**: `abcdefghijklmnop` (16 characters, no spaces)

### Step 4: Save and Test

1. **Click "Save"** to save the credential
2. **The "Send Email" node** should now show your Gmail credential
3. **Test the workflow** to verify it works

---

## 🐛 Troubleshooting

### Problem: "App passwords" option is not visible

**Solution**:
- ✅ Make sure 2-Step Verification is enabled
- ✅ Refresh the Security page
- ✅ Try signing out and signing back in

### Problem: "App passwords aren't available for your account"

**Possible Causes**:
1. **2-Step Verification not enabled** → Enable it first
2. **Google Workspace account** → May have different settings
3. **Account type** → Some account types don't support app passwords

**Solution**:
- Enable 2-Step Verification
- Contact your Google Workspace admin if using a work account

### Problem: "Invalid login credentials" in n8n

**Solutions**:
- ✅ **Check password**: Make sure you removed all spaces (16 characters total)
- ✅ **Verify email**: Use your full Gmail address (e.g., `name@gmail.com`)
- ✅ **Check port**: Use port `587` with `TLS` (or `465` with `SSL`)
- ✅ **Regenerate password**: If it still doesn't work, generate a new app password

### Problem: "Connection timeout" in n8n

**Solutions**:
- ✅ **Check firewall**: Port 587 might be blocked
- ✅ **Try port 465**: Use SSL instead of TLS
- ✅ **Check network**: Ensure n8n can reach Gmail servers

### Problem: SSL/TLS Error - "wrong version number" or "0A00010B"

**Error Message**: 
```
error:0A00010B:SSL routines:tls_validate_record_header:wrong version number
```

**Cause**: Port and security type mismatch

**Solutions**:

1. **Check Your Current Configuration**:
   - If using **Port 587** → Must use **TLS** (not SSL)
   - If using **Port 465** → Must use **SSL** (not TLS)

2. **Fix Port 587 Configuration** (Recommended):
   - **Port**: `587`
   - **Secure**: `TLS` (NOT SSL)
   - Verify these settings match exactly

3. **Alternative: Use Port 465**:
   - **Port**: `465`
   - **Secure**: `SSL` (NOT TLS)
   - This is an alternative if port 587 doesn't work

4. **Step-by-Step Fix**:
   - Open n8n workflow
   - Click "Send Email" node
   - Edit the SMTP credential
   - **Verify Port**: Should be `587`
   - **Verify Secure**: Should be `TLS` (not SSL)
   - Save and test again

5. **If Still Not Working**:
   - Try switching to port `465` with `SSL`
   - Or check if your network/firewall is interfering

### Problem: Can't find "App passwords" section

**Solution**:
1. Make sure you're on the Security page
2. Scroll down past "2-Step Verification"
3. Look for "App passwords" under "Signing in to Google"
4. If still not visible, ensure 2-Step Verification is ON

---

## 🔒 Security Best Practices

1. **Use App Passwords, not regular passwords**
   - Regular Gmail passwords won't work for SMTP
   - App passwords are more secure

2. **One password per application**
   - Generate separate app passwords for different apps
   - This allows you to revoke access individually

3. **Revoke unused passwords**
   - If you stop using n8n, revoke the app password
   - Go to Security → App passwords → Revoke

4. **Don't share app passwords**
   - Treat them like regular passwords
   - Keep them secure

5. **Regenerate if compromised**
   - If you suspect the password is compromised
   - Generate a new one and update n8n

---

## 📱 Alternative: Using Google Authenticator

If you prefer using an authenticator app instead of SMS:

1. **Enable 2-Step Verification** (as in Step 3)
2. **Choose "Authenticator app"** instead of phone
3. **Follow the setup** for Google Authenticator
4. **Then proceed** to generate App Password (Step 4)

---

## ✅ Quick Checklist

Before using the app password in n8n, verify:

- [ ] 2-Step Verification is enabled
- [ ] App password is generated (16 characters)
- [ ] Password is copied (without spaces)
- [ ] Gmail address is correct
- [ ] n8n SMTP credential is configured
- [ ] Test email is sent successfully

---

## 🆘 Still Having Issues?

### Common Mistakes:

1. **Using regular Gmail password** → Must use App Password
2. **Leaving spaces in password** → Remove all spaces
3. **Wrong email format** → Use full email: `name@gmail.com`
4. **Wrong port/security** → Use `587` with `TLS`
5. **2-Step Verification not enabled** → Enable it first

### Need More Help?

- Check n8n execution logs for detailed error messages
- Verify Gmail account is not locked or restricted
- Try generating a new app password
- Test SMTP connection in n8n node settings

---

## 📚 Related Documentation

- [n8n Workflow README](../n8n-workflows/README.md)
- [n8n Integration Guide](./N8N_INTEGRATION_GUIDE.md)
- [n8n Quick Reference](./N8N_QUICK_REFERENCE.md)

---

**Last Updated**: 2024-01-15  
**Status**: ✅ Complete Step-by-Step Guide
