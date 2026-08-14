import telnetlib
import os
import time
import logging
from datetime import datetime
 
# === Logging Setup ===
logging.basicConfig(level=logging.INFO, format='🔎 %(asctime)s - %(levelname)s - %(message)s')

# === Load Telnet Credentials ===
def load_credentials(path="credentials.conf"):
    creds = {}
    try:
        with open(path) as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    creds[key.strip()] = val.strip()
        logging.info("🔐 Loaded credentials from credentials.conf")
    except FileNotFoundError:
        logging.error(f"❌ credentials.conf file not found — using fallback values.")
# TELNET credentials (Enter your credentials bellow!)
    return creds.get("username", "enter-username-here"), creds.get("password", "enter-password-here")

# === Load IPs ===
def load_ips_from_file(file_path):
    ips = set()
    try:
        with open(file_path, 'r') as f:
            for line in f:
                ip = line.strip()
                if ip:
                    ips.add(ip)
    except FileNotFoundError:
        logging.warning(f"⚠️ File not found: {file_path}")
    return list(ips)

# === Telnet Session Logic ===
def run_telnet_session(ip, commands, username, password, output_path):
    try:
        tn = telnetlib.Telnet(ip, timeout=10)
        tn.read_until(b": ", timeout=5)
        tn.write(username.encode('ascii') + b"\n")
        tn.read_until(b": ", timeout=5)
        tn.write(password.encode('ascii') + b"\n")

        for cmd in commands.splitlines():
            tn.write(cmd.encode('ascii') + b"\n")
            time.sleep(0.3)

        tn.write(b"exit\n")
        result = tn.read_all().decode('utf-8')

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("-" * 46 + "\n")
            f.write(f"ip: {ip}\n")
            f.write("-" * 46 + "\n")
            f.write(result)

        logging.info(f"✅ Backup saved: {output_path}")
        return True

    except Exception as e:
        logging.error(f"❌ Failed Telnet to {ip}: {e}")
        return False

# === Main Execution ===
config_dir = "Telnet_IPs"
os.makedirs(config_dir, exist_ok=True)
ip_files = [os.path.join(config_dir, f) for f in os.listdir(config_dir) if f.lower().endswith(".conf")]

if not ip_files:
    logging.warning("⚠️ No .conf files found—add them to 'Telnet_IPs'")
    exit(1)

try:
    with open("TerminalCommandsTelnet.conf", "r") as cmd_file:
        commands = cmd_file.read()
except FileNotFoundError:
    logging.error("Missing TerminalCommands.conf. Please add it.")
    exit(1)

username, password = load_credentials()

date_folder = datetime.today().strftime("BackUps/%d-%m-%Y")
failed_ips = []

for conf_path in ip_files:
    base_name = os.path.splitext(os.path.basename(conf_path))[0]
    backup_subfolder = os.path.join(date_folder, base_name)
    os.makedirs(backup_subfolder, exist_ok=True)

    switch_ips = load_ips_from_file(conf_path)

    for ip in switch_ips:
        logging.info(f"🔌 Connecting to {ip} (from {base_name}.conf)...")
        output_file = os.path.join(backup_subfolder, f"{ip}.txt")
        success = run_telnet_session(ip, commands, username, password, output_file)
        if not success:
            failed_ips.append(ip)

# === Failed Backups ===
if failed_ips:
    failed_log_path = os.path.join(date_folder, "Failed_Telnet_Backups.txt")
    with open(failed_log_path, "w", encoding="utf-8") as f:
        f.write("❌ IPs that failed to back up:\n")
        for ip in failed_ips:
            f.write(ip + "\n")
    logging.info(f"📄 Failed IPs saved: {failed_log_path}")