# RSOMS Deployment Guide — PythonAnywhere (Updated)
## Your username: `sv9052788`
## Your live URL: `https://sv9052788.pythonanywhere.com`

---

## STEP 1: Sign Up / Log In

1. Open browser → Go to `https://www.pythonanywhere.com`
2. Click **"Pricing & signup"** → **"Create a Beginner account"** (free, no card needed)
3. Fill the form:
   - **Username**: `sv9052788`
   - **Email**: your email
   - **Password**: pick a strong password
4. Click **"Register"**
5. Check your email inbox → click the confirmation link
6. Log in with `sv9052788` + your password

---

## STEP 2: Open Bash Console

1. Click **"Consoles"** in the top navigation bar
2. Click **"Bash"** (NOT "Python 3.13", click the BASH button)
3. A black terminal window opens

---

## STEP 3: Clone Repo & Create Virtualenv

PythonAnywhere **recommends using a virtualenv** (not `--user` pip install). Run these commands ONE BY ONE:

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
mkvirtualenv --python=/usr/bin/python3.13 rsoms-venv
```
```bash
pip install -r requirements.txt
```

Wait for install to finish (~30 seconds). You should see green "Successfully installed" messages.

### Verify:
```bash
ls -la
```
You should see: `app.py`, `config.py`, `models.py`, `requirements.txt`, `static/`, `templates/`, etc.

---

## STEP 4: Create the Database

Still in the Bash console (with virtualenv active — you'll see `(rsoms-venv)` in your prompt):

```bash
cd ~/RSOMS-Restaurant-Safety-Platform
python
```

This opens the Python REPL. Now paste this EXACT block and press Enter:

```python
import sys
sys.path.insert(0, '/home/sv9052788/RSOMS-Restaurant-Safety-Platform')
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
print("Database created!")
```

Then type `exit()` and press Enter to quit Python.

---

## STEP 5: Create Web App

1. Go to **"Web"** tab in top navigation
2. Click the big green button: **"Add a new web app"**
3. Click **"Next"** to confirm domain (`sv9052788.pythonanywhere.com`)
4. Select **"Manual configuration"** (do NOT click "Flask", click "Manual configuration")
5. Select the **same Python version** as your virtualenv — **Python 3.13**
6. Click **"Next"**

---

## STEP 6: Configure Source Code, Working Directory & Virtualenv

On the Web app configuration page:

### Source code:
```
/home/sv9052788/RSOMS-Restaurant-Safety-Platform
```

### Working directory:
```
/home/sv9052788/RSOMS-Restaurant-Safety-Platform
```

### Virtualenv:
Scroll down to the **"Virtualenv"** section. Click the red link **"Enter path to a virtualenv, if desired"** and type:
```
rsoms-venv
```
Press Enter. It will auto-expand to the full path: `/home/sv9052788/.virtualenvs/rsoms-venv`

Click **"Save"**.

---

## STEP 7: Edit WSGI File

1. Scroll up to the section **"Code"**
2. Click the link: **"WSGI configuration file"** (looks like: `/var/www/sv9052788_pythonanywhere_com_wsgi.py`)
3. The editor opens with default code. **DELETE ALL** (Ctrl+A, Delete)
4. Paste this EXACT code block:

```python
import sys

path = '/home/sv9052788/RSOMS-Restaurant-Safety-Platform'
if path not in sys.path:
    sys.path.insert(0, path)

from app import create_app
application = create_app('production')
```

5. Click **"Save"** (green button, top-right of editor)
6. Close the editor tab

---

## STEP 8: Add Environment Variable (SECRET_KEY)

Still on the Web page, scroll down to find the **"Environment variables"** section (usually between Virtualenv and Log files).

1. Click **"New environment variable"**
2. Fill:
   - **Name**: `SECRET_KEY`
   - **Value**: `rsoms-2026-secret-key-suraj-verma-bit`
3. Click **"Add new environment variable"**

---

## STEP 9: Add Static Files Mapping

Still on the Web page, scroll down to the **"Static files"** section.

1. Click the red **"Enter URL"** link under **URL**
2. Type: `/static/`
3. Click the red **"Enter path"** link under **Directory**
4. Type: `/home/sv9052788/RSOMS-Restaurant-Safety-Platform/static/`
5. Click **"Insert new static mapping"**

This makes PythonAnywhere serve CSS/JS/images directly instead of routing through Flask.

---

## STEP 10: Add Uploads Folder Mapping (for Photos)

Still in the **"Static files"** section, add another mapping:

1. Click **"Enter URL"**
2. Type: `/uploads/`
3. Click **"Enter path"**
4. Type: `/home/sv9052788/RSOMS-Restaurant-Safety-Platform/static/uploads/`
5. Click **"Insert new static mapping"**

---

## STEP 11: Reload & Test

1. Scroll to the top of the Web page
2. Click the big green **"Reload"** button
3. Wait 5-10 seconds
4. Open a new browser tab → Go to: `https://sv9052788.pythonanywhere.com`

### Expected result:
The RSOMS homepage with green hero section, stats cards, and premium feature cards.

---

## STEP 12: Enable HTTPS

1. On the Web page, scroll down to **"Security"** section
2. Change **"Force HTTPS"** dropdown from **"Disabled"** → **"Enabled"**
3. Click **"Save"**

---

## STEP 13: If You See Errors

### Check the Error Log:
1. On Web page, find **"Log files"** section
2. Click **"Error log"** link (`sv9052788.pythonanywhere.com.error.log`)
3. Scroll to the very bottom to see the latest error
4. Copy the last 10-15 lines and send to me

### Common Fixes:

**"No module named 'flask'"** → Virtualenv not active or packages missing:
```bash
workon rsoms-venv
cd ~/RSOMS-Restaurant-Safety-Platform
pip install -r requirements.txt
```
Then click **Reload**.

**"sqlite3.OperationalError: no such table"** → Database not created. Repeat Step 4 (database creation).

**"Not Found" or 404** → Check Step 5 (source code path) and Step 7 (WSGI file) for typos.

---

## STEP 14: Update Code Later (Future Changes)

When you push new code to GitHub:

1. Open Bash console on PythonAnywhere
2. Run:
```bash
workon rsoms-venv
cd ~/RSOMS-Restaurant-Safety-Platform
git pull origin main
```
3. Click **"Reload"** on Web tab

Changes go live in 10 seconds.

---

## SUMMARY — Quick Reference

| Step | Action | Where |
|------|--------|-------|
| 1 | Sign up | pythonanywhere.com |
| 2 | Open Bash console | Consoles → Bash |
| 3 | Clone repo + create virtualenv + install deps | Bash commands |
| 4 | Create database tables | Bash → `python` → run db.create_all() |
| 5 | Create web app | Web → Add new web app → Manual config → Python 3.13 |
| 6 | Set source code + working directory + virtualenv | Web config page |
| 7 | Edit WSGI file | Click WSGI config file link → paste code → Save |
| 8 | Add SECRET_KEY env var | Web page → Environment variables |
| 9 | Add `/static/` static files mapping | Web page → Static files |
| 10 | Add `/uploads/` static files mapping | Web page → Static files |
| 11 | Reload | Click green Reload button |
| 12 | Visit site | `https://sv9052788.pythonanywhere.com` |
| 13 | Force HTTPS | Web page → Security → Enabled |

---

## COPY-PASTE READY VALUES

**Source code:**
```
/home/sv9052788/RSOMS-Restaurant-Safety-Platform
```

**Working directory:**
```
/home/sv9052788/RSOMS-Restaurant-Safety-Platform
```

**Virtualenv:**
```
rsoms-venv
```

**WSGI file — delete everything, paste this:**
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

**Static files mappings:**
| URL | Directory |
|-----|-----------|
| `/static/` | `/home/sv9052788/RSOMS-Restaurant-Safety-Platform/static/` |
| `/uploads/` | `/home/sv9052788/RSOMS-Restaurant-Safety-Platform/static/uploads/` |

**Live URL:**
```
https://sv9052788.pythonanywhere.com
```

---

Done. Start at Step 1 and follow in order. Do NOT skip Step 3 (virtualenv) or Step 9-10 (static files).
