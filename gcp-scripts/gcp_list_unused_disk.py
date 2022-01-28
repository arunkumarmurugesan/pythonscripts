import googleapiclient.discovery
compute = googleapiclient.discovery.build('compute', 'v1')
project="firm-aria-311218"
zone="us-central1-a"
result = compute.disks().list(project=project, zone=zone).execute()

import googleapiclient.discovery
import os
from google.oauth2 import service_account

compute = googleapiclient.discovery.build('compute', 'v1')
table = []
instance_table = []
idCount = 0

project = ["firm-aria-311218", "firm-aria-311218"]
for projects in project:
    result = compute.disks().aggregatedList(project=projects).execute()
    dCount = 0
    value = 0
    for key, val in result['items'].items():
        if 'warning' in result['items'].get(key):
            pass
        else:
            values = result['items'].get(key)['disks']
            aa = [iter for iter in values if "users" not in iter]
            print("aaaa", aa, len(aa))
            value += len(aa)
            for iter in values:
                if 'users' not in iter:
                    disk_id = iter['id']
                    disk_name = iter['name']
                    disk_timestamp = iter['creationTimestamp']
                    disk_size = iter['sizeGb']
                    # print(iter['id'],iter['name'],iter['creationTimestamp'],iter['sizeGb'])
                    idCount += 1
                    # print(idCount,disk_id,disk_name,disk_timestamp,disk_size)
                    dCount += 1
                    table.append(
                        [idCount, projects, iter['name'], iter['id'], iter['creationTimestamp'], iter['sizeGb']])

    print(dCount)
    instance_table.append([projects, dCount])

    print(instance_table)