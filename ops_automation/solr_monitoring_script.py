"""
Author: Arun M
Purpose: Solr Monitor script
Team: Cloud Guardians
Date: 18/11/2018
"""
import subprocess
import json
import re
import boto3
import paramiko
from subprocess import *
import time
import logging

## logging settings###
#set the log file name
timestr = time.strftime("%Y%m%d")
log = "/home/ubuntu/solr_monitor_" + timestr + "_.log"


#Enable the logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#create file handler and set level to debug

handler = logging.FileHandler(log)
handler.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch and handler
ch.setFormatter(formatter)
handler.setFormatter(formatter)

# add ch and handler  to logger
logger.addHandler(ch)
logger.addHandler(handler)

#variables

ec2 = boto3.resource('ec2', region_name='ap-south-1')
elb_client = boto3.client('elbv2', region_name='ap-south-1')
command = "/home/ubuntu/solr/server/scripts/cloud-scripts/zkcli.sh -zkhost zookeeper1.example.com:2181/solrtest -cmd get /clusterstate.json"
target_group_arn = "arn:aws:elasticloadbalancing:ap-south-1:xxxx:targetgroup/solrtest/xxxx"
target_instance_id = []

def get_instance_id(ip):
    solr_instances_id = []
    import boto3  # to import boto3 library
    ec2 = boto3.resource('ec2', region_name='ap-south-1')  # call ec2 recourse to perform further actions
    try:
        response = ec2.instances.filter(Filters=[{'Name': 'tag:module', 'Values': ['solr-dev']}])
    except Exception as e:
        logger.error("Error in filter the solr instances - {}".format(e))
    for instance in response:
        solr_instances_id.append(instance.id)
        if instance.private_ip_address == ip:
            master_instance_id = instance.id
    return master_instance_id,solr_instances_id

def ssh_into_server_check_DEV_queue():
    response = ec2.instances.filter(
        Filters=[{'Name': 'tag:module', 'Values': ['qworker']}, {'Name': 'instance-state-name', 'Values': ['running']}])
    # Get information for all running instances
    for instance in response:
        q_ip = instance.private_ip_address
        logger.info("Login into the Qworker instance - {} to stop the DEV Queue".format(q_ip))
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(hostname=q_ip, username="ubuntu")
        cmd = "sudo supervisorctl status | grep -i 'DEV' | awk '{print $1}'"
        stdin, stdout, stderr = c.exec_command(cmd)
        output = stdout.read()
        if output:
            output = "'{}'".format(output)
            #cmd = "sudo supervisorctl stop DEVQueue_bbasync:*"
            #stdin, stdout, stderr = c.exec_command(cmd)
            stdin, stdout, stderr = c.exec_command("sudo supervisorctl status " + output)
            j = stdout.read()
            logger.info("Found the DEV Queue on the Qworker - {} and stopped DEV Queue - {}".format(q_ip, j))
        else:
            logger.info("DEV Queue is not found on the Qworker - {}".format(q_ip))



def condition_first(ip, replica_state_count,master_state_count):
    if replica_state_count >= 4 and master_state_count == 1:
        logger.info("First condition is matched. The total number of replica  nodes is greater than or equal to four and master count is greater than one")
        # get the instance id of the master node
        master_instance_id,solr_instances_id = get_instance_id(ip)
        logger.info("The master instance id - {}".format(master_instance_id))
        # Check the current master node is registered with solr target group
        try:
            response = elb_client.describe_target_health(
                TargetGroupArn=target_group_arn
            )
        except Exception as e:
            logger.error("Error in describe the solr target groups - {}".format(e))
        for target_id in response['TargetHealthDescriptions']:
            target_instance_id.append(target_id['Target']['Id'])
        #if master instance is registered with solr target group, then will de-register it and register the remianing node.
        if master_instance_id in target_instance_id:
            logger.info("The solr master instance - {} is as part of the target group".format(master_instance_id))
            try:
                response = elb_client.deregister_targets(
                    TargetGroupArn=target_group_arn,
                    Targets=[
                        {
                            'Id': master_instance_id
                        },
                    ]
                )
                logger.info("De-registering the master instance - {} from the target grpup".format(master_instance_id))
            except Exception as e:
                logger.error("Error in deregister master instance from solr target groups -{} " .format(e))
            for solr_id in solr_instances_id:
                if solr_id != master_instance_id and solr_id not in target_instance_id:
                    try:
                        response = elb_client.register_targets(
                            TargetGroupArn=target_group_arn,
                            Targets=[
                            {
                                'Id': solr_id
                            },
                        ]
                    )
                        logger.info("Registering the other instances - {} to the solr target group".format(solr_id))
                    except Exception as e:
                        logger.error("Error in register the solr instances to solr target groups - {}".format(e))
        else:
            logger.info("There is no change in master instance and it's not  registered under the target group")
    else:
        logger.info("The first condition is not matching")
def condition_two(ip,replica_state_count,master_state_count):
    if replica_state_count == 2 and master_state_count == 1:
        logger.info("Second condition is matched. The total number of active replica nodes is equal to two - Condition two is executing")
        # get the instance id of the master node
        master_instance_id, solr_instances_id = get_instance_id(ip)
        logger.info("The master instance id - {}".format(master_instance_id))
        # Check the current master node is registered with solr target group
        try:
            response = elb_client.describe_target_health(
                TargetGroupArn=target_group_arn
            )
        except Exception as e:
            logger.error("Error in describe the solr target groups - {}".format(e))
        for target_id in response['TargetHealthDescriptions']:
            target_instance_id.append(target_id['Target']['Id'])
        #if master instance is registered with solr target group, then will de-register it and register the remianing node.
        if master_instance_id in target_instance_id:
            logger.info("The solr master instance - {} is as part of the target group".format(master_instance_id))
        else:
            # registered the current master node with solr target group
            try:
                response = elb_client.register_targets(TargetGroupArn=target_group_arn, Targets=[{'Id': master_instance_id}])
                logger.info("Registering the master instance - {} to the solr target group".format(master_instance_id))
            except Exception as e:
                logger.error("Error in register master instance to te solr target groups - {} ".format(e))
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            ssh_into_server_check_DEV_queue()
    else:
        logger.info("The second condition is not matching")

def condition_third(ip,total_cluster_count,master_state_count):
    if total_cluster_count == 2:
        logger.info("Third condition is matched. The total number of active nodes is equal to two - Condition third is executing")
        # get the instance id of the master node
        master_instance_id, solr_instances_id = get_instance_id(ip)
        logger.info("The master instance id - {}".format(master_instance_id))
        # Check the current master node is registered with solr target group
        try:
            response = elb_client.describe_target_health(
                TargetGroupArn=target_group_arn
            )
        except Exception as e:
            logger.error("Error in describe the solr target groups - {}".format(e))
        for target_id in response['TargetHealthDescriptions']:
            target_instance_id.append(target_id['Target']['Id'])



    else:
        logger.info()

def main():
    replica_state_count = 0
    master_state_count = 0
    total_cluster_count = 0
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    except Exception as e:
        logger.error("Unable to execute the command : %s"(e))
    (out, err) = proc.communicate()
    out_json = json.loads(out)
    node_out = out_json['bbconfig']['shards']['shard1']['replicas']
    for core_node in node_out.keys():
        # check which node is leader
        if 'leader' in node_out[core_node]:
            base_url = node_out[core_node]['base_url']
            pattern = re.compile("http://(.*):")
            ip = pattern.match(base_url).group(1)
            logger.info("The IP address of the master instance - {}".format(ip))
            master_state =  node_out[core_node]['state']
            if master_state == "active":
                master_state_count += 1
            logger.info("The master instance active state count - {}".format(master_state_count))
        else:
            # get the status of other nodes and it's count
            state = node_out[core_node]['state']
            if state == "active":
                replica_state_count += 1
    logger.info("The total number of active nodes apart from matster node - {}".format(replica_state_count))
    total_cluster_count = replica_state_count + master_state_count
    #If the master has changed to some other node, change the elb target nodes respectively .This scenario will be applicable if 4 or more nodes are active
    condition_first(ip, replica_state_count,master_state_count)
    #If there are only 2 active(not in recovery and down status) replica nodes and an active master at a given time
    condition_two(ip, replica_state_count,master_state_count)
    #If there are only 2 active nodes in the cluster at a given time, add all active nodes to elb and stop DEV consumers immediately(Ensure this is done inside a 1 min).
    condition_third(ip,total_cluster_count,master_state_count)
if __name__ == '__main__':
    main()