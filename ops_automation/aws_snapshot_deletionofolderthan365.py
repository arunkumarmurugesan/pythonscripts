import boto3
import dateutil
import pytz
import csv
from datetime import datetime, timedelta, date

#from boto import ec2
ec=boto3.resource('ec2',region_name='ap-southeast-1',aws_access_key_id='xxx',aws_secret_access_key='xxx')
reservation=ec.snapshots.filter(OwnerIds=['0123456789'])

csv_file=csv.writer(open("intv_snapshots.csv", "wb"))

for snap in reservation:
    snap_time = str(snap.start_time)
    snap_creation_time = created_date = datetime.strptime(snap_time, "%Y-%m-%d %H:%M:%S+00:00").replace(tzinfo=pytz.UTC)
    today_date=datetime.now()
    today_converted_date=today_date.replace(tzinfo=pytz.UTC)
    snap_days=today_converted_date - snap_creation_time
    if snap_days.days >= 365:
       csv_file.writerow([snap.snapshot_id, snap_days.days, snap.start_time, snap.description])
       print snap.snapshot_id, snap_days.days, snap.description
       try:
            snap.delete()
       except:
            pass
    else:
       pass
