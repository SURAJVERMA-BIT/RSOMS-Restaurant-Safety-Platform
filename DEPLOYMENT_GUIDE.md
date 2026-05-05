# RSOMS Deployment Guide — PythonAnywhere
## Your username: `sv9052788`
## Your live URL: `https://sv9052788.pythonanywhere.com`

---

## STEP 1: Sign Up / Log In

1. Open browser → Go to `https://www.pythonanywhere.com`
2. Click **"Start running Python online in less than a minute"**
3. Fill the form:
   - **Username**: `sv9052788` (use this exact username)
   - **Email**: your email
   - **Password**: pick a strong password
4. Click **"Create account"**
5. Check your email → click the confirmation link
6. Log in with `sv9052788` + your password

---

## STEP 2: Open Bash Console & Clone Repo

After login, you see the PythonAnywhere Dashboard.

1. Click **"Consoles"** in top navigation bar
2. Click **"Bash"** (NOT "Python 3.10", click the BASH button)
3. A black terminal window opens

### Run these commands ONE BY ONE (copy-paste each line, press Enter):

```bash
cd ~
```
```bash
git clone https://github.com/SURAJVERMA-BIT/RSOMS-Restaurant-Safety-Platform.git
```
```bash
cd RSOMS-Restaurant-Safety-Platform
```
```bash
pip install --user -r requirements.txt
```
Wait for the install to finish (takes ~30 seconds). You should see green "Successfully installed" messages.

### Verify the folder exists:
```bash
ls -la
```
You should see files: `app.py`, `config.py`, `models.py`, `requirements.txt`, `static/`, `templates/`, etc.

---

## STEP 3: Create Web App

1. Go to **"Web"** tab in top navigation
2. Click the big green button: **"Add a new web app"**
3. Click **"Next"** on the domain confirmation (it will be `sv9052788.pythonanywhere.com`)
4. Select **"Manual configuration"** (IMPORTANT: do NOT click "Flask", click "Manual configuration")
5. Select **Python 3.10**
6. Click **"Next"**

---

## STEP 4: Configure Source Code & Working Directory

On the Web app configuration page, scroll down to find these fields:

### Source code:
```
/home/sv9052788/RSOMS-Restaurant-Safety-Platform
```

### Working directory:
```
/home/sv9052788/RSOMS-Restaurant-Safety-Platform
```

Paste exactly as shown above. Click **"Save"** button.

---

## STEP 5: Edit WSGI File

Still on the Web page:

1. Scroll up to the section **"Code"**
2. Click the link: **"WSGI configuration file"** (it looks like: `/var/www/sv9052788_pythonanywhere_com_wsgi.py`)
3. A text editor opens with some default code. **DELETE ALL THE CONTENT** (Ctrl+A, Delete)
4. Paste this EXACT code block:

```python
import sys

path = '/home/sv9052788/RSOMS-Restaurant-Safety-Platform'
if path not in sys.path:
    sys.path.insert(0, path)

from app import create_app
application = create_app('production')
```

5. Click **"Save"** button (green button at top-right of editor)
6. Close the editor tab

---

## STEP 6: Set Environment Variable (SECRET_KEY)

Still on the Web page:

1. Scroll down to **"Environment variables"** section
2. Click the **"New environment variable"** button
3. Fill:
   - **Name**: `SECRET_KEY`
   - **Value**: `rsoms-2026-secret-key-suraj-verma-bit`
4. Click **"Add new environment variable"**

---

## STEP 7: Reload & Test

At the top of the Web page:

1. Click the big green **"Reload"** button
2. Wait 5-10 seconds
3. Open a new browser tab → Go to: `https://sv9052788.pythonanywhere.com`

### Expected result:
You should see the RSOMS homepage with the green hero section, stats, and feature cards.

---

## STEP 8: If Something Goes Wrong

### If you see "Internal Server Error":

1. Go back to PythonAnywhere Web tab
2. Click the **"Error log"** link (under "Log files" section)
3. Scroll to the bottom to see the last error
4. Copy the last 10-15 lines
5. Send them to me — I'll fix it immediately

### Common fixes:

**"No module named 'flask'"** → Run in Bash console:
```bash
cd ~/RSOMS-Restaurant-Safety-Platform
pip install --user -r requirements.txt
```

**"sqlite3.OperationalError: no such table"** → Database not created. In a Python console (NOT Bash):
```python
import sys
sys.path.insert(0, '/home/sv9052788/RSOMS-Restaurant-Safety-Platform')
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
```

---

## STEP 9: Enable HTTPS (After It Works)

1. On Web tab, scroll down
2. Find **"Security"** section
3. Check **"Force HTTPS"**
4. Click **"Save"**

---

## STEP 10: Update Code Later (Future Changes)

Whenever you push new code to GitHub:

1. Open Bash console on PythonAnywhere
2. Run:
```bash
cd ~/RSOMS-Restaurant-Safety-Platform
git pull origin main
```
3. Click **"Reload"** on Web tab

That's it. Your changes go live in 10 seconds.

---

## SUMMARY

| Step | Action | Location |
|------|--------|----------|
| 1 | Sign up / Log in | pythonanywhere.com |
| 2 | Bash console → clone repo | Consoles → Bash |
| 3 | Install requirements | Bash: `pip install --user -r requirements.txt` |
| 4 | Create web app | Web → Add new web app → Manual → Python 3.10 |
| 5 | Set source code path | Web config page |
| 6 | Edit WSGI file | Click WSGI configuration file link |
| 7 | Add SECRET_KEY env var | Web page → Environment variables |
| 8 | Reload | Click green Reload button |
| 9 | Visit site | `https://sv9052788.pythonanywhere.com` |
| 10 | Force HTTPS | Web page → Security |

---

## Your Exact Values (Copy-Paste Ready)

**Source code path:**
```
/home/sv9052788/RSOMS-Restaurant-Safety-Platform
```

**Working directory:**
```
/home/sv9052788/RSOMS-Restaurant-Safety-Platform
```

**WSGI file content:**
```python
import sys

path = '/home/sv9052788/RSOMS-Restaurant-Safety-Platform'
if path not in sys.path:
    sys.path.insert(0, path)

from app import create_app
application = create_app('production')
```

**Environment variable:**
- Name: `SECRET_KEY`
- Value: `rsoms-2026-secret-key-suraj-verma-bit`

**Live URL:**
```
https://sv9052788.pythonanywhere.com
```

---

Done. Start with Step 1 and follow in order.
