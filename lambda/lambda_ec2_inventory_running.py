#description     :This script will get triggered daily which will get all running ec2 instance and send email report.
#author          :Arunkumar
#version         :1.0
#usage           :Lambda function
#detailed docs   :
#==============================================================================
import jinja2
import boto3
import datetime
import time
import logging
import json
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#Importing ec2 client
client = boto3.client('ec2')

#Declaring list which will be getting used
RunningInstances = []
Time = []
Name = []
Region = []
Account = []
status = []
length = []

# Enable the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
logger.addHandler(ch)

# AWS Config
EMAIL_HOST = 'email-smtp.us-west-2.amazonaws.com'
EMAIL_HOST_USER = "#######################" # Replace with your SMTP username
EMAIL_HOST_PASSWORD = "##############################" # Replace with your SMTP password
EMAIL_PORT = 587

msg = MIMEMultipart('alternative')
msg['Subject'] = "Dev Account Running Instance"
msg['From'] = "alerts@gmail.com"
recipients = ['alerts@gmail.com', 'alerts01@gmail.com']
msg['To'] = ", ".join(recipients)

def ec2_list():
    try:
        j = 0
        regDesc = client.describe_regions()
        for regions in regDesc['Regions']:
            region = regions['RegionName']
            ec2 = boto3.client('ec2', region_name=region)
            response = ec2.describe_instances(
                Filters = [{'Name'   : 'instance-state-name', 'Values' : ['running'] }] )
            for i in response['Reservations']:
                for tag in i['Instances'][0]['Tags']:
                    if tag['Key'] == "Name":
                        value=tag['Value']
                        Name.append(value)
                date = i['Instances'][0]['LaunchTime']
                day = str(date.strftime("%c"))
                Time.append(day)
                RunningInstances.append(i['Instances'][0]['InstanceId'])
                Region.append(region)
                Account.append("Dev")
                status.append("Running")
                length.append(j)
                j = j + 1
        logger.info("Data collected Successfully")
    except Exception as e:
        logger.error("Data Not collected: {}".format(e))
    
def send_mail():
    try:
        ec2_list()
    except Exception as e:
        logger.error("EC2 Function did not executed: {}".format(e))
    try:
        html= jinja2.Template (""" <html>
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
                <caption> <h3> EC2 Instances Running in Dev Account </h3></caption>
                <br>
                    <table border="0" cellspacing="0" cellpadding="0" width="896" style="width:671.95pt;border-collapse:collapse">
                <tbody>
                <tr style="height:15.75pt">
                <td valign="bottom" style="border:solid black 1.0pt;background:#cfe2f3;padding:1.5pt 2.35pt 1.5pt 2.35pt;height:15.75pt">
                <p><b><span style="color:black">Sr. No.</span></b></p>
                </td>
                <td valign="bottom" style="border:solid black 1.0pt;background:#cfe2f3;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt">
                <p><b><span style="color:black">Account</span></b></p>
                </td>
                <td width="157" valign="bottom" style="width:117.4pt;border:solid black 1.0pt;border-left:none;background:#cfe2f3;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                <p><b><span style="color:black">Instance ID</span></b></p>
                </td>
                <td width="56" valign="bottom" style="width:41.7pt;border:solid black 1.0pt;border-left:none;background:#cfe2f3;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                <p><b><span style="color:black">Region</span></b></p>
                </td>
                <td valign="bottom" style="border:solid black 1.0pt;border-left:none;background:#cfe2f3;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                <p><b><span style="color:black">Instance Name</span></b></p>
                </td>
                <td valign="bottom" style="border:solid black 1.0pt;border-left:none;background:#cfe2f3;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                <p><b><span style="color:black">Launch Time</span></b></p>
                </td>
                <td valign="bottom" style="border:solid black 1.0pt;border-left:none;background:#cfe2f3;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                <p><b><span style="color:black">State</span></b></p>
                </td>
                </tr>
                {%for i in length %}
                    <tr style="height:15.75pt">
                        <td valign="bottom" style="border:solid black 1.0pt;border-top:none;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                        <p><span style="color:black">{{i+1}}</span></p>
                        </td>
                        <td valign="bottom" style="border:solid black 1.0pt;border-top:none;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                        <p><span style="color:black">{{Account[i]}}</span></p>
                        </td>
                        <td width="157" valign="bottom" style="width:117.4pt;border-top:none;border-left:none;border-bottom:solid black 1.0pt;border-right:solid black 1.0pt;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                        <p><span style="color:black">{{RunningInstances[i]}}</span></p>
                        </td>
                        <td width="56" valign="bottom" style="width:41.7pt;border-top:none;border-left:none;border-bottom:solid black 1.0pt;border-right:solid black 1.0pt;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                        <p><span style="color:black">{{Region[i]}}</span></p>
                        </td>
                        <td valign="bottom" style="border-top:none;border-left:none;border-bottom:solid black 1.0pt;border-right:solid black 1.0pt;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                        <p><span style="color:black">{{Name[i]}}</span></p>
                        </td>
                        <td valign="bottom" style="border-top:none;border-left:none;border-bottom:solid black 1.0pt;border-right:solid black 1.0pt;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                        <p><span style="color:black">{{Time[i]}}</span></p>
                        </td>
                        <td valign="bottom" style="border-top:none;border-left:none;border-bottom:solid black 1.0pt;border-right:solid black 1.0pt;padding:1.5pt 2.25pt 1.5pt 2.25pt;height:15.75pt;overflow:hidden">
                        <p><span style="color:black">{{status[i]}}</span></p>
                        </td>
                    </tr>
                {%-endfor%}
                    </table>
                
                </body>
                </html>""")
        temp=html.render(Account = Account, RunningInstances = RunningInstances, Region = Region, Name = Name, Time = Time, status = status, length = length)
        s = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        s.starttls()
        s.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        mime_text = MIMEText(temp, 'html')
        msg.attach(mime_text)
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        s.quit()
        logger.info("Mail Sent")
    except Exception as e:
        logger.error("Email not sent: {}".format(e))
     
def lambda_handler(event, context):
    # TODO implement
    try:
        send_mail()
    except Exception as e:
        logger.error("Lambda handler error: {}".format(e))
