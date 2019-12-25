import boto3
# Defaults, can be modified
AWS_ACCESS_KEY = 'xx'
AWS_SECRET_KEY = 'xx'
AWS_REGIONS = 'ap-southeast-1'


session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
conn = session.client('iam')

resource = session.resource('iam')
client = session.client("iam")

# for user in resource.users.all():
#     print user

def find_user_and_groups():
    for userlist in conn.list_users()['Users']:
        userGroups = conn.list_groups_for_user(UserName=userlist['UserName'])
        print("Username: "  + userlist['UserName'])
        managed_user_policies = client.list_attached_user_policies(UserName=userlist['UserName'])
        print managed_user_policies
        # print("Assigned groups: ")
        # for groupName in userGroups['Groups']:
        #     print(groupName['GroupName'])
        # print("----------------------------")

if __name__ == '__main__':
    find_user_and_groups()
