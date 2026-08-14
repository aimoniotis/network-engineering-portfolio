import os
from datetime import datetime
 
def generate_daily_report(backup_base_dir="BackUps"):
    # 1. Determine today's backup directory (e.g., BackUps/13-08-2026)
    today_str = datetime.today().strftime("%d-%m-%Y")
    today_folder = os.path.join(backup_base_dir, today_str)

    print("=" * 60)
    print(f"📊 AUTOMATED NETWORK BACKUP REPORT - {today_str}")
    print("=" * 60)

    if not os.path.exists(today_folder):
        print(f"⚠️ No backup directory found for today ({today_folder}).")
        print("Please run the SSH or Telnet backup scripts first.")
        return

    # 2. Count successful backups (.txt files excluding failure log files)
    successful_backups = []
    failed_entries = []

    for root, dirs, files in os.walk(today_folder):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Check if file is a failure log
            if file in ["failed_ssh_backup.txt", "Failed_Telnet_Backups.txt"]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        # Capture lines containing IPs/errors
                        for line in lines:
                            line_clean = line.strip()
                            if line_clean and not line_clean.startswith("Failed") and not line_clean.startswith("="):
                                failed_entries.append(line_clean)
                except Exception as e:
                    print(f"⚠️ Error reading failure log {file_path}: {e}")
            
            # Check if file is a device backup (.txt)
            elif file.endswith(".txt"):
                group_name = os.path.basename(root)
                ip_address = os.path.splitext(file)[0]
                successful_backups.append(f"{group_name} -> {ip_address}")

    total_success = len(successful_backups)
    total_failed = len(failed_entries)
    total_processed = total_success + total_failed

    # 3. Output Summary Statistics
    print(f"\n📈 SUMMARY STATISTICS:")
    print(f"  • Total Devices Processed : {total_processed}")
    print(f"  • Successful Backups     : {total_success} ✅")
    print(f"  • Failed Attempt(s)      : {total_failed} ❌")

    if total_processed > 0:
        success_rate = (total_success / total_processed) * 100
        print(f"  • Success Rate           : {success_rate:.1f}%")

    # 4. Success Details by Group
    if successful_backups:
        print("\n✅ SUCCESSFUL BACKUPS LIST:")
        for entry in sorted(successful_backups):
            print(f"  [+] {entry}")

    # 5. Failure Details
    if failed_entries:
        print("\n❌ FAILED BACKUPS LIST:")
        for failure in failed_entries:
            print(f"  [-] {failure}")
    else:
        print("\n🎉 PERFECT RUN: Zero connection or authentication failures detected!")

    print("\n" + "=" * 60)
    print(f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    generate_daily_report()