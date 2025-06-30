import subprocess
import pandas as pd
from datetime import datetime, timedelta
import socket
import pyodbc
import time
import win32com.client as win32
import traceback

def send_error_mail(subject, body):
    try:
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = 'NVTI.IT@nvtpower.com'
        mail.Subject = subject
        mail.Body = body
        mail.Send()
    except Exception as e:
        print("Failed to send error mail:", e)

try:

    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=#####;'
        'DATABASE=#####;'
        'UID=######;'
        'PWD=######;'
    )
    cursor = conn.cursor()

    
    ip_df = pd.read_sql("SELECT ip_address FROM ip", conn)
    ping_list = ip_df['ip_address'].tolist()


    def ensure_ip_columns_exist(ip_list):
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='PingResponse'")
        existing_columns = {row[0] for row in cursor.fetchall()}
        for ip in ip_list:
            if ip not in existing_columns:
                cursor.execute(f"ALTER TABLE PingResponse ADD [{ip}] VARCHAR(50)")
        conn.commit()

    ensure_ip_columns_exist(ping_list)

    
    ip_data_excel = pd.read_sql("SELECT * FROM ip_ping_Status", conn)

    new_records = []
    data_matrix = []
    running_time = 60 
    interval = 1  
    start_time = time.time()

    while time.time() - start_time < running_time:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        row_matrix = {"Timestamp": timestamp}
        for ip in ping_list:
            try:
                status = "Up" if subprocess.run(f"ping -n 1 {ip}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.find("Reply from") != -1 else "Down"
                response_time = "Timeout"
                output = subprocess.check_output(f'ping -n 1 {ip}', shell=True, text=True)
                for line in output.split("\n"):
                    if "time=" in line:
                        response_time = line.split("time=")[-1].split("ms")[0].strip() + "ms"
                        break
            except subprocess.CalledProcessError:
                status = "Down"
                response_time = "Timeout"

            downtime = "0:00:00"
            try:
                if status == "Down" and not ip_data_excel.empty:
                    past_up_records = ip_data_excel[(ip_data_excel["IP"] == ip) & (ip_data_excel["Status"] == "Up")]
                    if not past_up_records.empty:
                        last_up_date = past_up_records.iloc[-1]["Date"]
                        last_up_time = datetime.strptime(str(past_up_records.iloc[-1]["Start_time"]), "%H:%M:%S").time()
                        last_up_datetime = datetime.combine(last_up_date, last_up_time)
                        downtime_duration = now - last_up_datetime
                    else:
                        past_down_records = ip_data_excel[(ip_data_excel["IP"] == ip) & (ip_data_excel["Status"] == "Down")]
                        if not past_down_records.empty:
                            first_down_date = past_down_records.iloc[0]["Date"]
                            first_down_time = datetime.strptime(str(past_down_records.iloc[0]["Start_time"]), "%H:%M:%S").time()
                            first_down_datetime = datetime.combine(first_down_date, first_down_time)
                            downtime_duration = now - first_down_datetime
                        else:
                            downtime_duration = None

                    if downtime_duration:
                        days = downtime_duration.days
                        hours, remainder = divmod(downtime_duration.seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        downtime = f"{days} days {hours:02}:{minutes:02}:{seconds:02}"
            except Exception as e:
                print(f"Downtime calculation error for IP {ip}: {e}")

            local_ip = socket.gethostbyname(socket.gethostname())
            new_records.append({
                "IP": ip,
                "Date": now.date(),
                "Start_time": now.time().replace(microsecond=0),
                "Status": status,
                "Downtime": downtime,
                "IP_fetched_by": local_ip
            })
            row_matrix[ip] = response_time

        data_matrix.append(row_matrix)
        time.sleep(interval)

    
    df_to_insert = pd.DataFrame(new_records).rename(columns={
        'IP': 'ip',
        'Date': 'date',
        'Start_time': 'start_time',
        'Status': 'status',
        'Downtime': 'downtime',
        'IP_fetched_by': 'ip_fetched_by'
    })

    def insert_ip_data(df):
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO ip_ping_status (ip, date, start_time, status, downtime, ip_fetched_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, row['ip'], row['date'], row['start_time'], row['status'], str(row['downtime']), row['ip_fetched_by'])
        conn.commit()

    insert_ip_data(df_to_insert)

    
    ip_data_excel = pd.concat([ip_data_excel, pd.DataFrame(new_records)], ignore_index=True)
    latest_record = []

    for ip in ping_list:
        condition = (ip_data_excel["IP"] == ip) & (ip_data_excel["Date"] == datetime.now().date()) & (ip_data_excel["Status"] == "Down")
        if ip not in ip_data_excel.columns:
            ip_data_excel[ip] = 0
        else:
            ip_data_excel[ip] = ip_data_excel[ip].fillna(0)

        ip_data_excel.loc[condition, ip] = 1
        ip_data_excel[f"Cumulative_{ip}"] = ip_data_excel[ip].cumsum()

        ip_filtered = ip_data_excel[ip_data_excel["IP"] == ip]
        if not ip_filtered.empty:
            latest_ip_row_copy = ip_filtered.iloc[-1].copy()
            latest_record.append(latest_ip_row_copy)

    live_ping_status = pd.DataFrame(latest_record).fillna(0)
    live_ping_status["Downtime_Counter"] = ""
    for ip in ping_list:
        live_ping_status.loc[live_ping_status["IP"] == ip, "Downtime_Counter"] = live_ping_status[f"Cumulative_{ip}"]
        live_ping_status.drop(columns=[ip, f"Cumulative_{ip}"], inplace=True)

    def update_live_ping_status(df):
        cursor.execute("TRUNCATE TABLE live_ping_status")
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO live_ping_status (ip, date, start_time, status, downtime, ip_fetched_by, downtime_counter)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, row['IP'], row['Date'], row['Start_time'], row['Status'], str(row['Downtime']), row['IP_fetched_by'], int(row['Downtime_Counter']))
        conn.commit()

    update_live_ping_status(live_ping_status)

    
    matrix_df = pd.DataFrame(data_matrix)
    cursor.execute("TRUNCATE TABLE PingResponse")
    for _, row in matrix_df.iterrows():
        columns = ["Timestamp"] + [ip for ip in ping_list]
        placeholders = ["?"] * len(columns)
        values = [row[col] if col in row else "Timeout" for col in columns]
        insert_query = f"INSERT INTO PingResponse ({', '.join(f'[{col}]' for col in columns)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(insert_query, values)
    conn.commit()

except Exception as e:
    error_message = traceback.format_exc()
    print("An error occurred:\n", error_message)
    send_error_mail("Ping Monitoring Script Failed", error_message)

finally:
    try:
        cursor.close()
        conn.close()
        print("DATABASE UPDATED SUCCESSFULLY")
    except:
        pass
