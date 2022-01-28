import os, sys
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import logging

# Enable the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S %Z')
ch.setFormatter(formatter)
logger.addHandler(ch)

class gcpStopStart:
    def __init__(self):
        self.GCPPROJECTID = "ecstatic-maxim-596"
        self.ZONE = "us-east4-a"

    def gcpConnect(self):
        try:
            # key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            # credentials = service_account.Credentials.from_service_account_file(
            #     key_path,
            #     scopes=["https://www.googleapis.com/auth/cloud-platform"],
            # )
            ## local testing
            credentials = GoogleCredentials.get_application_default()
        except Exception as err:
            logger.error(
                "Please Set the GOOGLE_APPLICATION_CREDENTIALS as environment variable, Exception : {}".format(err))
            raise err
        return credentials

    def startInstances(self,compute_client,instanceID, instanceName):
        try:
            request = compute_client.instances().start(project=self.GCPPROJECTID, zone=self.ZONE,
                                                      instance=instanceID).execute()
            logger.info("The following instance is started - Instance Name: {}, Instance ID: {}".format(instanceName,instanceID))
        except Exception as err:
            logger.error("Unable to start the instance ID {}. Exception : {}".format(instanceName,err))

    def stopInsances(self,compute_client,instanceID, instanceName):
        try:
            request = compute_client.instances().stop(project=self.GCPPROJECTID, zone=self.ZONE,
                                                      instance=instanceID).execute()
            logger.info("The following instance is stopped - Instance Name: {}, Instance ID: {}".format(instanceName,instanceID))
        except Exception as err:
            logger.error("Unable to stop the instance ID {}. Exception : {}".format(instanceName,err))

    def initiateTask(self,action,environmentValue):
        logger.info("The script is started")
        try:
            compute_client = discovery.build('compute', 'v1', credentials=self.gcpConnect())
            instances_result = compute_client.instances().list(project=self.GCPPROJECTID, zone=self.ZONE).execute()
            if "items" in instances_result:
                for instance_row in instances_result["items"]:
                    for i in instance_row["metadata"]["items"]:
                        if i['key'] == "environment" and i['value'] == str(environmentValue):
                            if action == "stop":
                                if instance_row["status"] == "RUNNING":
                                    self.stopInsances(self.gcpConnect(),instance_row["id"],instance_row["name"])
                                else:
                                    logger.info(
                                        "Instance is already stopped/terminated state. Current state of the instance is : {}, Instance Name: {}".format(
                                            instance_row["status"], instance_row["name"]))
                            elif action == "start":
                                if instance_row["status"] == "TERMINATED":
                                    self.startInstances(self.gcpConnect(),instance_row["id"],instance_row["name"])
                                else:
                                    logger.info(
                                        "Instance is already Running state. Current state of the instance is : {}, Instance Name: {}".format(
                                            instance_row["status"], instance_row["name"]))
        except Exception as err:
            print("unable to execute the projects, Exception : {}".format(err))
            raise err
        logger.info("The script is ended")


if __name__ == '__main__':
    try:
        ACTION = os.environ.get("ACTION")
        ENVIRONMENT = os.environ.get("ENVIRONMENT")
    except Exception as err:
        logger.error(
            "Please Set the ACTION and ENVIRONMENT as environment variable, Exception : {}".format(err))
        raise err
    callFunc = gcpStopStart()
    callFunc.initiateTask(ACTION,ENVIRONMENT)