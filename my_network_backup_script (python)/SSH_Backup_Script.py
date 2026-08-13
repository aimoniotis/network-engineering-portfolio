import paramiko
import os
from datetime import datetime

def load_ips_from_file(file_path):
    """Return a list of unique IPs from one file."""
    ips = set()
    try:
        with open(file_path, 'r') as f:
            for line in f:
                ip = line.strip()
                if ip:
                    ips.add(ip)
    except FileNotFoundError:
        print(f"⚠️ File not found: {file_path}")
    return list(ips)

# 1. Define and create the folder for your .conf files
config_dir = "IPs"
os.makedirs(config_dir, exist_ok=True)
print(f"🔍 Looking for .conf files in '{config_dir}/'")

# 2. Dynamically list all .conf files in that folder
ip_files = [
    os.path.join(config_dir, fname)
    for fname in os.listdir(config_dir)
    if fname.lower().endswith(".conf")
]

if not ip_files:
    print(
        "⚠️ No .conf files found—"
        " drop your test.conf, test1.conf, etc. into the 'IPs' folder."
    )
    exit(1)

# 3. Read your commands once
with open("TerminalCommands.conf", "r") as cmd_file:
    commands = cmd_file.read()

# 4. SSH credentials (Enter your credentials bellow!)
# username = "enter-username-here"
# password = "enter-pass-here"

# 5. Base folder for today’s backups
date_folder = datetime.today().strftime("BackUps/%d-%m-%Y")
os.makedirs(date_folder, exist_ok=True)

# 6. Track failed IPs
failed_ips = []

# 7. Begin processing each .conf file
for conf_path in ip_files:
    base_name = os.path.splitext(os.path.basename(conf_path))[0]
    backup_subfolder = os.path.join(date_folder, base_name)
    os.makedirs(backup_subfolder, exist_ok=True)

    switch_ips = load_ips_from_file(conf_path)

    for ip in switch_ips:
        print(f"🔌 Connecting to {ip} (source: {base_name}.conf)...")
        output_file = os.path.join(backup_subfolder, f"{ip}.txt")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(ip, username=username, password=password, timeout=10)
            shell = ssh.invoke_shell()
            shell.send(commands + '\n')
            shell.settimeout(2)

            result = ""
            while True:
                try:
                    chunk = shell.recv(1024).decode("utf-8")
                    if not chunk:
                        break
                    result += chunk
                except Exception:
                    break

            # Save full backup output
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("-" * 46 + "\n")
                f.write(f"ip: {ip}\n")
                f.write("-" * 46 + "\n")
                f.write(result)

            print(f"✅ Backup saved: {output_file}")

        except Exception as e:
            print(f"❌ Failed to back up {ip}: {e}")
            failed_ips.append(f"{ip} ({base_name}.conf): {e}")

        finally:
            ssh.close()

# 8. Save failed IPs to log file
if failed_ips:
    failed_log_path = os.path.join(date_folder, "failed_ssh_backup.txt")
    with open(failed_log_path, "w", encoding="utf-8") as log_file:
        log_file.write("Failed IPs Log\n")
        log_file.write("=" * 30 + "\n")
        for entry in failed_ips:
            log_file.write(entry + "\n")
    print(f"📄 Logged {len(failed_ips)} failed IPs to: {failed_log_path}")
else:
    print("🎉 All backups succeeded!")
