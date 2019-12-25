import json
import logging, boto3

# Enable the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S %Z')
ch.setFormatter(formatter)
logger.addHandler(ch)

my_session = boto3.session.Session()
REGION = my_session.region_name


def lambda_handler(event, context):
    # Connect to AWS boto3 Client
    def aws_connect_client(service, REGION):
        try:
            # Gaining API session
            session = boto3.Session()
            # Connect the client
            conn_client = session.client(service, REGION)
        except Exception as e:
            logger.error('Could not connect to region: %s and resources: %s , Exception: %s\n' % (REGION, service, e))
            conn_client = None
        return conn_client

    def list_sg(REGION):
        ec2_client = aws_connect_client('ec2', REGION)
        security_group = ec2_client.describe_security_groups(Filters=[{
            'Name': 'tag:KubernetesCluster',
            'Values': ['demo.example.com']}])
        sg_list = [name['GroupId'] for name in security_group['SecurityGroups']]
        final_list = []
        for i in sg_list:
            x = ec2_client.describe_security_groups(GroupIds=[i])
            for k in x['SecurityGroups']:
                for n in k['IpPermissions']:
                    if n['IpProtocol'] == '-1':
                        pass
                    else:
                        final_list.append(i)
        return final_list

    def list_rules():
        # Calling list_sg functions
        final_list = list_sg(REGION)
        ec2_client = aws_connect_client('ec2', REGION)
        # Calling remove_duplicates function
        for name in remove_duplicates(final_list):
            x = ec2_client.describe_security_groups(GroupIds=[name])
            for k in x['SecurityGroups']:
                for n in k['IpPermissions']:
                    if n['IpProtocol'] == '-1' or n['IpProtocol'] == '4':
                        pass
                    else:
                        if n['FromPort'] == 3 and n['ToPort'] == 4 and n['IpProtocol'] == 'icmp':
                            security_group = ec2_client.revoke_security_group_ingress(CidrIp='0.0.0.0/0', FromPort=3,
                                                                                      GroupId=name,
                                                                                      IpProtocol='icmp', ToPort=4)
                            if (security_group['ResponseMetadata']['HTTPStatusCode']) == 200:
                                logger.info('No Security rule with Destination Unreachable')
                        logger.info("No rule found!")

    def remove_duplicates(values):
        output = []
        seen = set()
        for value in values:
            # If value has not been encountered yet,
            # ... add it to both list and set.
            if value not in seen:
                output.append(value)
                seen.add(value)
        return output

    list_rules()