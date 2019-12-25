import os, sys
import boto3

my_session = boto3.session.Session()
my_region = my_session.region_name


def lambda_handler(event, context):
    Answer = event['answer']
    Priority = event['priority']
    Loadbalancer = event ['loadbalancer']
    RulePath = event ['rulepath']
    TargetGroup = event['targergroup']
	
    if not Answer:
        return "Unable to get the answer variable. Its shoule True or False"
    elif not Priority:
        return "Unable to get the priority variable value."
    elif not Loadbalancer:
        return "Unable to get the Loadbalancer variable value."
    elif not RulePath:
        return "Unable to get the RulePath variable value."
    elif not TargetGroup:
        return "Unable to get the TargetGroup variable value"

    
    def connect_region():
        try:
            #Get current Regions
            session = boto3.Session(region_name=my_region)
            print ("Connected the Region: %s" %my_region) 
            conn = session.client('elbv2',my_region)
        except Exception, e:
            sys.stderr.write('Could not connect to region: %s. Exception: %s\n' % (my_region, e))
            conn = None
        return conn
      
    def add_rule():

        conn = connect_region()
        if not conn:
            sys.stderr.write('Could not connect to region: %s. Skipping\n' % my_region)
            exit(0)
        try:
            loadbalancer = conn.describe_load_balancers().get('LoadBalancers', [])
        except Exception, e:
            sys.stderr.write('Could not get ALB details from region: %s. Skipping (problem: %s)\n' % (loadbalancer, e.error_message))
            exit(0)
        for load in loadbalancer:
            lb_arn = load["LoadBalancerArn"]
            alb_name = load['LoadBalancerName']
            response = conn.describe_listeners(LoadBalancerArn=lb_arn)
            if alb_name == Loadbalancer:
                for i in response['Listeners']:
                    targetgrp = conn.describe_target_groups(LoadBalancerArn=lb_arn)
                    TargetGroups_list = targetgrp['TargetGroups']
                    for j in TargetGroups_list:
                        targetgroup_name = j['TargetGroupName']
                        if targetgroup_name == TargetGroup:
                            TargetGroupArn = j['TargetGroupArn']
                            ListenerArn = i['ListenerArn']
                            desc_rule = conn.describe_rules(ListenerArn=ListenerArn)
                            rule_list= desc_rule['Rules']
                            for k in rule_list:
                                rule_arn = k['RuleArn']
                                condition=  k['Conditions']
                                for h in condition:
                                    values = h["Values"]
                                    values01 = str(values).strip('[]')
                                    val1=  str(values01).replace("'", "")
                                    if val1 == RulePath:
                                        print ("The Given RulePath : %s already exist...") %(RulePath)
                            
                            response = conn.create_rule(
                                                Actions=[
                                                    {
                                                        'TargetGroupArn': TargetGroupArn,
                                                        'Type': 'forward',
                                                    },
                                                ],
                                                Conditions=[
                                                    {
                                                        'Field': 'path-pattern',
                                                        'Values': [
                                                            RulePath,
                                                        ],
                                                    },
                                                ],
                                                ListenerArn=ListenerArn,
                                                Priority=int(Priority),
                                            )
                            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                                print ("Successfully Added the RulePath: %s in Loadbalancer: %s" %(RulePath,Loadbalancer))
                                        
   
    def remove_rule():    
        conn = connect_region()
        if not conn:
            sys.stderr.write('Could not connect to region: %s. Skipping\n' % my_region)
            exit(0)
        try:
            loadbalancer = conn.describe_load_balancers().get('LoadBalancers', [])
        except Exception, e:
            sys.stderr.write('Could not get ALB details from region: %s. Skipping (problem: %s)\n' % (loadbalancer, e.error_message))
            exit(0)
        
        for load in loadbalancer:
            lb_arn = load["LoadBalancerArn"]
            alb_name = load['LoadBalancerName']
            response = conn.describe_listeners(LoadBalancerArn=lb_arn)
            if alb_name == Loadbalancer:
                for i in response['Listeners']:
                    ListenerArn = i['ListenerArn']
                    desc_rule = conn.describe_rules(ListenerArn=ListenerArn)
                    rule_list= desc_rule['Rules']
                    for j in rule_list:
                        rule_arn = j['RuleArn']
                        condition=  j['Conditions']
                        for k in condition:
                            values = k["Values"]
                            values01 = str(values).strip('[]')
                            val1=  str(values01).replace("'", "")
                            if val1 == RulePath:                    
                                response = conn.delete_rule(RuleArn=rule_arn)
                                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                                    print ("Successfully removed the RulePath: %s in Loadbalancer: %s" % (RulePath, Loadbalancer))
                            else:
                                print ("The Given RulePath: %s doesn't Exist...." %RulePath)
        
    if 'True' == Answer:
        add_rule()                            
    elif 'False' == Answer: 
        remove_rule()
