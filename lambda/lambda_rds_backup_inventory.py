#description     :This script will generate the RDS backup report daily.
#author          :Arunkumar
#version         :1.0
#usage           :Lambda function
#detailed docs   :
#==============================================================================
import boto3
import datetime
import time
import logging
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import subprocess
import os
from datetime import date
from datetime import timedelta

client = boto3.client('rds')
s3_client = boto3.client('s3')

x = datetime.datetime.utcnow()
hour=str(x.strftime("%H"))
day=str(x.strftime("%d"))
prev_date=x- datetime.timedelta(days=1)
prev_day=str(prev_date.strftime("%d"))
weekday=str(x.weekday())
prev_week=x - datetime.timedelta(days=28)
prev_week=str(prev_week.strftime("%d"))
month=x.strftime("%m")
year=x.strftime("%y")
prev_year=str(int(year)-1)
prev_month=str(int(month)-1)
today = date.today()

# Enable the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
logger.addHandler(ch)

rds_client = boto3.client('rds')
snapshots = rds_client.describe_db_cluster_snapshots()
my_list = []
hourly_list = []
daily_list = []
weekly_list = []
monthly_list = []
bck_list = []
dbdump_list = []

# AWS Config
EMAIL_HOST = 'email-smtp.us-west-2.amazonaws.com'
EMAIL_HOST_USER = "#########################" # Replace with your SMTP username
EMAIL_HOST_PASSWORD = "###############################" # Replace with your SMTP password
EMAIL_PORT = 587

msg = MIMEMultipart('alternative')
msg['Subject'] = "RDS Backup Report"
msg['From'] = "alerts@gmail.com"
recipients = ['alerts@gmail.com', 'alerts@gmail.com']
msg['To'] = ", ".join(recipients)

s = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
s.starttls()
s.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

def des_snap():
    for i in snapshots['DBClusterSnapshots']:
        my_list.append (i['DBClusterSnapshotIdentifier'])

def check_hourly():
    try:
        snap_name = 'prod-pg-cluster-snapshot-hourly-at-'
        for text in my_list:
            if snap_name in text:
                hourly_list.append(text)
        for i in range(8):
            try:
                t = hourly_list[i]
            except IndexError:
                hourly_list.append("NA")
    except Exception as e:
        logger.error('No Hourly Snapshot Found')
        
def check_daily():
    try:
        snap_name = 'prod-pg-cluster-snapshot-daily-for-' + day + '-' + month
        for text in my_list:
            if snap_name in text:
                daily_list.append(text)
        try:
            t = daily_list[0]
        except IndexError:
            daily_list.append("NA")
    except Exception as e:
        logger.error('No Daily Snapshot Found')

def check_weekly():
    try:
        offset = (today.weekday() - 6) % 7
        last_sunday = today - timedelta(days=offset)
        sunday = last_sunday.strftime("%d")
        snap_name = 'prod-pg-cluster-snapshot-weekely-sunday' + sunday
        for text in my_list:
            if snap_name in text:
                weekly_list.append(text)
        try:
            t = weekly_list[0]
        except IndexError:
            weekly_list.append("NA")
    except Exception as e:
        logger.error('No Weekly Snapshot Found')
        
def check_monthly():
    try:
        snap_name = 'prod-pg-cluster-snapshot-monthly-' + month + '-' + year
        for text in my_list:
            if snap_name in text:
                monthly_list.append(text)
        try:
            t = monthly_list[0]
        except IndexError:
            monthly_list.append("NA")
    except Exception as e:
        logger.error('No Monthly Snapshot Found')
        
def s3_bck():
    try:
        key = "prod_beta-"+str(prev_date.strftime("%d"))+"-"+str(today.strftime("%B")[0:3])+"-"+str(today.strftime("%y"))+"-08-00-01.sql.gz"
        print("Key=="+key)
        all_objects = s3_client.list_objects_v2(Bucket = 'prod-db-backup')
        for i in all_objects['Contents']:
            k = i['Key']
            bck_list.append(k)
        for text in bck_list:
            if key in text:
                dbdump_list.append(key)
        try:
            t = dbdump_list[0]
        except IndexError:
            dbdump_list.append("NA")
    except Exception as e:
        logger.error('DB Dump not found')

def send_mail():    
    try:
        html= """ <html>
                <head>
                    <title></title>
                </head>
                <style>
                table, th, td {
                  border: 1px solid black;
                  border-collapse: collapse;
                }
                tr{
                    align-content: center;
                    text-align: center;
                }
                </style>
                <body>
                    <table style="width:100%">
                        <caption> <h3> RDS Latest Backup Report </h3></caption>
                        <tr>
                            <th>Snapshot Cycle</th>
                            <th>Number of Latest Snapshot Available</th>
                            <th>Available Snapshot Name</th>
                        </tr>
                        <tr>
                            <tr>
                                <td rowspan="8">Hourly Available Snapshots</td>
                
                                <td rowspan="8">8</td>
                            
                                 <td>""" + hourly_list[0] + """ </td>
                            </tr>
                            <tr>    
                                <td> """ + hourly_list[1] + """ </td>
                            </tr>
                            <tr>
                                <td>""" + hourly_list[2] + """ </td>
                            </tr>
                            <tr>
                                <td>""" + hourly_list[3] + """ </td>
                            </tr>
                            <tr>
                                <td>""" + hourly_list[4] + """ </td>
                            </tr>
                            <tr>
                                <td>""" + hourly_list[5] + """ </td>
                            </tr>
                            <tr>
                                <td>""" + hourly_list[6] + """ </td>
                            </tr>
                            <tr>
                                <td>""" + hourly_list[7] + """ </td>
                            </tr>
                        </tr>
                        <tr>
                            <tr>
                                <td rowspan="3">Daily Available Snapshots</td> 
                                <td rowspan="3">1</td>
                            </tr>
                            <tr>
                                <td>""" + daily_list[0] + """ </td>
                            </tr>
                        </tr>
                        <tr>
                            <tr>
                                <td rowspan="2">Weekly Available Snapshots</td> 
                                <td rowspan="2">1</td>
                            </tr>
                            <tr>
                                <td>""" + weekly_list[0] + """ </td>
                            </tr>
                        </tr>
                        <tr>
                            <tr>
                                <td rowspan="2">Monthly Available Snapshots</td> 
                                <td rowspan="2">1</td>
                            </tr>
                            <tr>
                                <td>""" + monthly_list[0] + """ </td>
                            </tr>
                        </tr>
                    </table>
                    <table style="width:100%">
                        <caption> <h3> Latest DB Backup Available in S3 bucket </h3></caption>
                        <tr>
                            <th>Bucket Name</th>
                            <th>DB Dump Name</th>
                        </tr>
                        <tr>
                            <tr>
                                <td rowspan="2">prod-db-backup</td> 
                            </tr>
                            <tr>
                                <td>""" + dbdump_list[0] + """ </td>
                            </tr>
                        </tr>
                    </table>
                
                </body>
                </html>"""
        mime_text = MIMEText(html, 'html')
        msg.attach(mime_text)
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        s.quit()
        print("Mail Sent")
    except Exception as e:
        logger.error("Email not sent: {}".format(e))

def lambda_handler(event, context):
    des_snap()
    check_hourly()
    check_daily()
    check_weekly()
    check_monthly()
    s3_bck()
    send_mail()
