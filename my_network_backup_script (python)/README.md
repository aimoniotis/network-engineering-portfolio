# 🐍 Multi-Protocol Enterprise Cisco Configuration Backup Automation

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Cisco-IOS%20%2F%20IOS--XE-125578?style=for-the-badge&logo=cisco&logoColor=white" alt="Cisco">
  <img src="https://img.shields.io/badge/Protocol-SSH%20%26%20Telnet-FF6F00?style=for-the-badge" alt="SSH and Telnet">
  <img src="https://img.shields.io/badge/Scale-200%2B%20Devices-008000?style=for-the-badge" alt="Scale">
</p>
 
An enterprise-grade, multi-protocol automated backup solution engineered to handle full configuration management for **200+ critical Cisco switches and routers** across a distributed network infrastructure. 

By leveraging **SSH (`paramiko`)** for modern assets and legacy **Telnet (`telnetlib`)** for older nodes, this tool automates daily state collection, ensures configuration retention, tracks unreachable hosts, and seamlessly integrates with **Windows Task Scheduler**.

---

## ⚡ Scale & Performance Highlights

* **Scale:** Production-tested across **200+ enterprise network nodes** (Core, Distribution, and Access layers).
* **Speed & Reliability:** Sequential execution with strict socket timeouts (10s) to prevent hanging sessions on offline nodes.
* **Resilience:** Built-in exception handling ensures single-host timeouts do not break the global backup pipeline.

---

## 🛠️ Key Features

* **Dual-Protocol Support:** Native SSH functionality alongside a legacy Telnet fallback module.
* **Dynamic Target Parsing:** Automatically discovers and ingests IP lists from structured `.conf` files inside designated folders (`IPs/` and `Telnet_IPs/`).
* **Structured Archival Engine:** Dynamically generates date-stamped backup directories structured as `BackUps/DD-MM-YYYY/<Group_Name>/<IP>.txt`.
* **Failure Auditing & Logging:** Automatically records failed connections, timeouts, and authentication issues into dedicated daily log files (`failed_ssh_backup.txt`, `Failed_Telnet_Backups.txt`).
* **Credential Security:** Isolates sensitive login parameters into external `credentials.conf` files, protecting repos from accidental credential leaks.
* **Automated Batch Execution:** Ships with a Windows Batch runner (`.bat`) pre-configured for background execution and logging via Task Scheduler.

---

## 📂 Repository Architecture

```text
automation-python/
│
├── IPs/                                   # SSH Target Groups (.conf files)
│   ├── switches_core.conf
│   └── switches_distribution.conf
│
├── Telnet_IPs/                            # Telnet Target Groups (.conf files)
│   └── switches_legacy.conf
│
├── TerminalCommands.conf                  # Cisco CLI execution sequence (SSH)
├── TerminalCommandsTelnet.conf            # Cisco CLI execution sequence (Telnet)
├── credentials.conf                       # Isolated credentials file (GIT-IGNORED)
│
├── SSH_Backup_Script.py                   # Paramiko-based SSH backup engine
├── Telnet_Backup_Script.py                # Telnet-based backup engine
├── generate_report.py                     # Summary report generator
├── run_backup_tasks.bat                   # Batch script for Windows Task Scheduler
│
└── BackUps/                               # Auto-generated backup repository
    └── DD-MM-YYYY/
        ├── core_switches/
        │   ├── 10.0.0.1.txt
        │   └── 10.0.0.2.txt
        └── failed_ssh_backup.txt
