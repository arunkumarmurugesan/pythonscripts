import boto3
import csv
import sys
csvfolder ='/root/scripts/csvfolder/'
#client = boto3.client('ec2', region_name='ap-south-1')
client = boto3.client('ec2', region_name='ap-southeast-1', aws_access_key_id='xxxxxxxxxxxxxx',aws_secret_access_key='xxxxxxxxxxxxxx')
group_id = sys.argv[1]
sec_grps = client.describe_security_groups(GroupIds=[group_id])['SecurityGroups']
for sg in sec_grps:
    sg_id = sg['GroupId']
    sg_name = sg.get('GroupName', None)
    filepath = csvfolder + sg_name + "-IN.csv"
    csvfile = file(filepath, 'wt')
    fwriter = csv.writer(csvfile)
    fwriter.writerow(['Group Id', 'Name', 'Protocol', 'From', 'To', 'IPs', 'SG_List', 'SG_Name', 'Instance_Name'])

    filepath_out = csvfolder + sg_name + "-OUT.csv"
    csvfile_out = file(filepath_out, 'wt')
    fwriter_out = csv.writer(csvfile_out)
    fwriter_out.writerow(['Group Id', 'Name', 'Protocol', 'From', 'To', 'IPs', 'SG_List', 'SG_Name'])
    ip_permissions_ingress = None
    ip_permissions_egress = None
    data_list = []

    response = client.describe_instances(
        Filters=[
            {
                'Name': 'group-id',
                'Values': [
                    sg_id,
                ]
            },
        ],
    )
    name_list = []
    for i in response['Reservations']:
        for instance in i['Instances']:
            if 'terminated' in instance['State']['Name']:
                skip
            else:
                for tags in instance['Tags']:
                    if tags['Key'] == 'Name':
                        name = tags.get('Value')
                        name_list.append(name)
    print "Intiating the backup of security group id -  %s" %(sg_name)
    if 'IpPermissions' in sg:
        ip_permissions = sg['IpPermissions']
        for inbound_rule in ip_permissions:
            protocol = inbound_rule['IpProtocol']
            if protocol == '-1':
                from_port = 'ALL PORTS'
                to_port = 'ALL PORTS'
                protocol = 'All Traffic'
                ip_ranges = inbound_rule['IpRanges']
                for ip in ip_ranges:
                    cidr = ip['CidrIp']
                    data_list = [sg_id, sg_name, protocol, from_port, to_port, cidr, 'None', 'None',name_list]
                    fwriter.writerow(data_list)
                    data_list =[]
                security_groups_attached = inbound_rule['UserIdGroupPairs']
                for sg_attached in security_groups_attached:
                    sg_list = sg_attached['GroupId']
                    if 'GroupName' in sg_attached:
                        sg_name_list = sg_attached['GroupName']
                    else:
                        sg_name_list = 'None'
                    data_list = [sg_id, sg_name, protocol, from_port, to_port, 'None' , sg_list,  sg_name_list, name_list]
                    fwriter.writerow(data_list)
                    date_list = []
            else:
                from_port = inbound_rule['FromPort']
                to_port = inbound_rule['ToPort']
                ip_ranges = inbound_rule['IpRanges']
                ip_list = []
                for ip in ip_ranges:
                    cidr = ip['CidrIp']
                    data_list = [sg_id, sg_name, protocol, from_port, to_port, cidr, 'None', 'None', name_list]
                    fwriter.writerow(data_list)
                    data_list = []
                security_groups_attached = inbound_rule['UserIdGroupPairs']
                for sg_attached in security_groups_attached:
                    sg_list = sg_attached['GroupId']
                    if 'GroupName' in sg_attached:
                        sg_name_list = sg_attached['GroupName']
                    else:
                        sg_name_list = 'None'
                    data_list = [sg_id, sg_name, protocol, from_port, to_port, "None", sg_list, sg_name_list, name_list]
                    fwriter.writerow(data_list)
                    date_list = []
        print "Inbound rule  backup has been completed - please check the report - %s" %(filepath)
        csvfile.close()
        if 'IpPermissionsEgress' in sg:
                ip_permissions = sg['IpPermissionsEgress']
                for outbound_rule in ip_permissions:
                        protocol = outbound_rule['IpProtocol']
                        if protocol == '-1':
                                from_port = 'ALL PORTS'
                                to_port = 'ALL PORTS'
                                protocol = 'All Traffic'
                                ip_ranges = outbound_rule['IpRanges']
                                for ip in ip_ranges:
                                        cidr = ip['CidrIp']
                                        data_list = [sg_id, sg_name, protocol, from_port, to_port, cidr, 'None', 'None',name_list]
                                        fwriter_out.writerow(data_list)
                                        data_list =[]
                                security_groups_attached = outbound_rule['UserIdGroupPairs']
                                for sg_attached in security_groups_attached:
                                        sg_list = sg_attached['GroupId']
                                        if 'GroupName' in sg_attached:
                                                sg_name_list = sg_attached['GroupName']
                                        else:
                                                sg_name_list = 'None'
                                        data_list = [sg_id, sg_name, protocol, from_port, to_port, 'None' , sg_list,  sg_name_list, name_list]
                                        fwriter_out.writerow(data_list)
                                        date_list = []
                        else:
                                from_port = outbound_rule['FromPort']
                                to_port = outbound_rule['ToPort']
                                ip_ranges = outbound_rule['IpRanges']
                                ip_list = []
                                for ip in ip_ranges:
                                        cidr = ip['CidrIp']
                                        data_list = [sg_id, sg_name, protocol, from_port, to_port, cidr, 'None', 'None', name_list]
                                        fwriter_out.writerow(data_list)
                                        data_list = []
                                security_groups_attached = outbound_rule['UserIdGroupPairs']
                                for sg_attached in security_groups_attached:
                                        sg_list = sg_attached['GroupId']
                                        if 'GroupName' in sg_attached:
                                                sg_name_list = sg_attached['GroupName']
                                        else:
                                                sg_name_list = 'None'
                                                data_list = [sg_id, sg_name, protocol, from_port, to_port, "None", sg_list, sg_name_list, name_list]
                                                fwriter_out.writerow(data_list)
                                                date_list = []
                print "Outbound rule  backup has been completed - please check the report - %s" %(filepath_out)
                csvfile_out.close()
