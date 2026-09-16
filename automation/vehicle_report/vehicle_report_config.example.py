# Copy this file to  vehicle_report_config.py  and fill in your values.
# vehicle_report_config.py is git-ignored — your credentials never leave this PC.

# --- OneLap (Traccar) login — the same email/password you use at web.onelap.in ---
ONELAP_EMAIL    = "you@example.com"
ONELAP_PASSWORD = "your-onelap-password"

# --- Path to your Operations Hub git repo ---
REPO_DIR = r"C:\Users\hp\Downloads\Operationsdashboard"

# --- Email delivery (Gmail). Create an App Password: https://myaccount.google.com/apppasswords ---
# Leave SMTP_USER = None to skip email entirely.
SMTP_USER         = "you@gmail.com"
SMTP_APP_PASSWORD = "abcd efgh ijkl mnop"   # 16-char Gmail app password
EMAIL_TO          = ["satvik@nutriobox.com"]
