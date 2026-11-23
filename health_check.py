"""
Network health check - sample lab version.

Connects to Cisco IOS devices, checks interface status, OSPF neighbours and
CPU load, then saves a CSV report.

Setup:  pip install netmiko
Usage:  set NET_USER and NET_PASS as environment variables, then run:
        python health_check.py
"""
import csv
import os
import re
from datetime import datetime

from netmiko import ConnectHandler

DEVICES = ["192.0.2.11", "192.0.2.12"]  # lab devices (example addresses)
USER = os.getenv("NET_USER")
PASSWORD = os.getenv("NET_PASS")


def check_device(host):
    conn = ConnectHandler(
        device_type="cisco_ios", host=host, username=USER, password=PASSWORD
    )
    interfaces = conn.send_command("show ip interface brief")
    ospf = conn.send_command("show ip ospf neighbor")
    cpu = conn.send_command("show processes cpu | include CPU utilization")
    conn.disconnect()

    # Interfaces reported as down (includes administratively down)
    down = [
        line.split()[0]
        for line in interfaces.splitlines()
        if "down" in line.lower() and not line.startswith("Interface")
    ]
    full_neighbours = len(re.findall(r"\bFULL\b", ospf))
    cpu_match = re.search(r"five seconds: (\d+)%", cpu)

    return {
        "device": host,
        "interfaces_down": ", ".join(down) or "none",
        "ospf_full_neighbours": full_neighbours,
        "cpu_5s_percent": cpu_match.group(1) if cpu_match else "n/a",
    }


def main():
    rows = []
    for host in DEVICES:
        try:
            rows.append(check_device(host))
        except Exception as error:  # keep going if one device fails
            rows.append({"device": host, "interfaces_down": f"ERROR: {error}"})

    filename = f"health_report_{datetime.now():%Y%m%d_%H%M}.csv"
    fields = ["device", "interfaces_down", "ospf_full_neighbours", "cpu_5s_percent"]
    with open(filename, "w", newline="") as report:
        writer = csv.DictWriter(report, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Report saved: {filename}")


if __name__ == "__main__":
    main()
