📌 Project Description
A Python-powered real-time IP monitoring system developed for the IT infrastructure team to detect, log, and prevent IP downtimes. The system continuously pings a predefined list of IPs, tracks their response times, logs their online/offline status into Microsoft SQL Server, and visualizes the live status using Fine BI dashboards. This allows the IT team to act proactively before any critical IP goes down, ensuring high availability of network services.

The solution is designed for 24×7 operation, runs every 10 minutes, and has been packaged as an .exe for seamless deployment.

🖥️ What This Dashboard Shows (From Fine BI Screenshot)
Live Ping Status Indicators:

Green light shows the number of currently active (Up) IPs.

Red light shows the number of inactive (Down) IPs.

The system also logs how long an IP has been down (e.g., “7 days 02:16:34”).

Real-Time IP Ping Graphs:

Visualizes ping response times (in milliseconds) for each IP.

Clearly marks Timeouts in red for quick identification of failing endpoints.

IP Fetch Log:

Shows which system (identified by IP) performed the pinging for each target IP.

Helps trace and audit monitoring responsibility.

🔍 Key Contributions
✅ Developed Python scripts that:

Ping multiple IPs and log their response times.

Detect and calculate real-time downtime from previous “Up” status.

Automatically insert new IPs into the SQL schema when needed.

Push data into three key SQL tables: ip_ping_status, live_ping_status, and PingResponse.

✅ Converted the script into an .exe to ensure non-technical users (IT admins) can run it with a single click.

✅ Configured the script to run in 10-minute intervals continuously 24×7 on production machines.

✅ Enabled Outlook-based email alerts in case the script fails, ensuring no silent failures.

✅ Integrated with Fine BI to:

Display real-time dashboards of IP status.

Help the IT infrastructure team monitor, analyze, and respond to issues before they escalate.

Ensure high uptime of critical network services by visualizing “Timeout” and “Down” trends.

🛠️ Tech Stack
Language: Python

Database: Microsoft SQL Server

Visualization: Fine BI

Libraries Used: pandas, pyodbc, subprocess, socket, datetime, win32com.client

Platform: Windows (for compatibility with Outlook and the ping command)

Deployment: Packaged as a .exe for automated background execution

⚠️ Note: This is a demo version built for portfolio purposes. Original production code is confidential and cannot be shared.
