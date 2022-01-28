import boto3
from datetime import datetime, timedelta, date
import re
from dateutil.tz import tzutc
from google.cloud import bigquery
from google.oauth2 import service_account
import os, sys
import process_query, process_email, process_table
import logging
import opsgenie_sdk
import hvac
import jinja2
from jinja2 import Environment, PackageLoader
from collections import OrderedDict
import time

# Enable the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S %Z')
ch.setFormatter(formatter)
logger.addHandler(ch)


class getDBCredentials:
    def __init__(self):
        self.FAILED_EXIT_CODE = 1
        self.S3BUCKETNAME = "viant.activision"
        self.GCPPROJECTID = "activision-staging"
        self.noFileCount = 0
        self.yesFileCount = 0
        self.getLastFiles = list()
        self.fCount = 0
        self.table = list()
        self.getFBucketName = list()
        self.getTableRowCount = list()
        self.gets3FullPath = list()
        self.today_str = datetime.today().strftime('%a %b %d, %Y')
        self.data = OrderedDict()


    # Connect to AWS boto3 Client
    def aws_connect_client(self, service):
        try:
            # Gaining API session
            # session = boto3.Session(aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
            session = boto3.Session()
            # Connect the resource
            conn_client = session.resource(service)
        except Exception as err:
            logger.error(
                'Could not able to connect to AWS Session and resources: {} , Exception: {}'.format(service, err))
            conn_client = None
            raise err
            sys.exit(self.FAILED_EXIT_CODE)
        return conn_client

    def getOpsgenieKey(self):
        try:
            vault_url = os.getenv('VAULT_ADDR')
            vault_token = os.getenv('VAULT_TOKEN')
            vault_client = hvac.Client(url=vault_url, token=vault_token)
            api_key = vault_client.read('/secret/service/airflow/activision-file-drop/opsgeniekey')['data']['value']
            logger.info("Able to read the vault for get opsgenine api key ")
        except Exception as err:
            logger.error("Unable to get opsgenie api key from vault. Exception : {}".format(err))
            raise err
        return api_key

    def createOpsgenie(self):
        api_key = self.getOpsgenieKey()
        self.conf = self.conf = opsgenie_sdk.configuration.Configuration()
        self.conf.api_key['Authorization'] = api_key
        self.api_client = opsgenie_sdk.api_client.ApiClient(configuration=self.conf)
        self.alert_api = opsgenie_sdk.AlertApi(api_client=self.api_client)
        body = opsgenie_sdk.CreateAlertPayload(
            message='AirFlow Job: activision_file_drop is failed',
            description='Please check the activision_file_drop dag logs in the airflow',
            responders=[{
                'name': 'DevOps',
                'type': 'team'
            }],
            priority='P3'
        )
        try:
            create_response = self.alert_api.create_alert(create_alert_payload=body)
            logger.info("Sent opsgenie notification!. Response Code - {}".format(create_response))
            time.sleep(3)
            alertID = create_response.id
            success_response = self.alert_api.add_attachment(identifier=alertID,
                                                             file='activision_report.html')
            return create_response
        except opsgenie_sdk.ApiException as err:
            logger.error("Exception when calling Opsgenie AlertApi->create_alert: {}".format(err))
            raise err

    def getS3BucketSession(self):
        s3_resource = self.aws_connect_client("s3")
        try:
            bucket = s3_resource.Bucket(self.S3BUCKETNAME)
        except Exception as err:
            logger.error('Cloud not able to connect the s3 bucket : {}'.format(self.S3BUCKETNAME))
            raise err
            sys.exit(self.FAILED_EXIT_CODE)
        return bucket

    def getS3Folders(self):
        bucket = self.getS3BucketSession()
        try:
            result = bucket.meta.client.list_objects(Bucket=bucket.name, Delimiter='/')
        except Exception as err:
            logger.error('Unable to list the ojbects from s3 bucket : {}'.format(self.S3BUCKETNAME))
            raise err
            sys.exit(self.FAILED_EXIT_CODE)
        getToday = date.today()
        getYesterday = getToday - timedelta(days=1)
        subfolders = [i.get('Prefix') for i in result.get('CommonPrefixes')]
        return getYesterday, subfolders

    def getS3BucketFiles(self):
        bucket = self.getS3BucketSession()
        getYesterday, subfolders = self.getS3Folders()
        for _folders in subfolders:
            if 'CommonPrefixes' in bucket.meta.client.list_objects(Bucket=bucket.name, Prefix=str(_folders),
                                                                   Delimiter='/'):
                getfolder = [j.get('Prefix') for j in
                             bucket.meta.client.list_objects(Bucket=bucket.name, Prefix=str(_folders), Delimiter='/')[
                                 'CommonPrefixes']]
                sub_folder_datefmt = re.split('/', str(getfolder[-1]))[1]
                if sub_folder_datefmt == str(getYesterday):
                    for objects in bucket.objects.filter(Prefix='{}{}'.format(_folders, sub_folder_datefmt)):
                        self.yesFileCount += 1
                        if objects.last_modified > datetime.now(tzutc()) - timedelta(hours=24):
                            keys = objects.key
                            fullPath = "s3://viant.activision/" + keys
                            splitFiles = re.split('/', str(keys))[-1]
                            self.getLastFiles.append(splitFiles)
                            self.gets3FullPath.append(fullPath)
                        else:
                            self.noFileCount += 1
                            logger.info("No more files last 24 hours")
                else:
                    pass
        return self.getLastFiles, self.gets3FullPath, self.noFileCount, self.yesFileCount

    def gcpConnect(self):
        try:
            key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            credentials = service_account.Credentials.from_service_account_file(
                key_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        except Exception as err:
            logger.error(
                "Please Set the GOOGLE_APPLICATION_CREDENTIALS as environment variable, Exception : {}".format(err))
            raise err
        return credentials

    def getGBQQuery(self, val):
        checkTableQuery = 'SELECT count(*) as countvalue FROM `activision-staging.ingested.{}`;'.format(val)
        checkTableSize = 'SELECT sum(size_bytes) / ( 1000 * 1000 ) as size FROM `activision-staging.ingested.__TABLES__` WHERE table_id = "{}"'.format(
            val)
        return checkTableQuery, checkTableSize

    def convertHTML(self,data):
        # # Initialize Jinja2 environment and template
        # templateLoader = jinja2.FileSystemLoader(searchpath="/Users/vpari/PycharmProjects/Personal")
        # templateEnv = jinja2.Environment(loader=templateLoader)
        env = Environment(loader=PackageLoader('spend_hourly', '.'))
        activision_stats_template = env.get_template('spend_monitor/templates/activision_report.eml.j2')
        activision_render = activision_stats_template.render(data)
        with open("activision_report.html", "w") as writer:
            writer.write(activision_render)

    def validateS3WithGBQ(self):
        getLastFiles, gets3FullPath, noFileCount, yesFileCount = self.getS3BucketFiles()
        rCount = 0
        rTCount = 0
        if noFileCount is None:
            pass
        else:
            if not getLastFiles:
                logger.info("No more files last 24 hours")
                email_str = "<b><br>Failed: No files are dropped in the s3 <br></b>"
                process_email.sendEmail(email_str, "GBQ Activision S3 Report - FAILURE".format(self.today_str),
                                        sys.argv[2])
                sys.exit(self.FAILED_EXIT_CODE)
            else:
                logger.info("The last 24 hr files are: {}".format(getLastFiles))
                getLastFilesLW = [lw.lower() for lw in getLastFiles]
                credentials = self.gcpConnect()

                try:
                    gcp_client = bigquery.Client(credentials=credentials, project=self.GCPPROJECTID)
                    tables = gcp_client.list_tables('activision-staging.ingested')
                except Exception as err:
                    logger.error("Unable to make GCP big query API: Exception : {}".format(err))
                    raise err
                    sys.exit(self.FAILED_EXIT_CODE)

                getTableIds = [table.table_id for table in tables]
                getTableIdsLW = [lw.lower() for lw in getTableIds]

                for _file, _fullpath in zip(getLastFilesLW, gets3FullPath):
                    val = _file.split(".")[0]
                    s3FilePath = _fullpath
                    if _file.endswith('.gz'):
                        logger.info("Ignoring the file as its .gz file : {}".format(s3FilePath))
                        pass
                    else:
                        if _file.endswith('.csv') and str(val) in getTableIdsLW or any(_file.split(".")[0].upper() in str(table) for table in getTableIds):
                            logger.info("The following s3 file is present in the GBQ, Files is: {}".format(_file))
                            gbqTableName = val
                            try:
                                if any(_file.split(".")[0].upper()  in str(table) for table in getTableIds):
                                    uVal = str(val).upper()
                                    uVal = uVal.replace("_CSV", "_csv")
                                    checkTableQuery, checkTableSize = self.getGBQQuery(uVal)
                                    query_check_table = gcp_client.query(checkTableQuery)
                                    query_check_tablesize = gcp_client.query(checkTableSize)
                                else:
                                    checkTableQuery, checkTableSize = self.getGBQQuery(val)
                                    query_check_table = gcp_client.query(checkTableQuery)
                                    query_check_tablesize = gcp_client.query(checkTableSize)
                                tableResult = query_check_table.result()
                                logger.info("Executed the GBQ Query to check table, Query is : {}".format(checkTableQuery))
                                tableSizeResult = query_check_tablesize.result()
                                logger.info(
                                    "Executed the GBQ Query to get size of the table, Query is : {}".format(checkTableSize))

                            except Exception as err:
                                logger.error("Unable to execute the query. Exception : {}".format(err))
                                raise err
                                sys.exit(self.FAILED_EXIT_CODE)

                            for i in tableResult:
                                gbqTotalNoRows = i['countvalue']
                            for i in tableSizeResult:
                                gbqTableSize = "{:.2f} MB".format(i['size'])
                            if gbqTotalNoRows <= 0:
                                logger.info("GBQ row count is greater than zero for the S3 file: {}".format(s3FilePath))
                                rTCount += 1
                                self.getTableRowCount.append([rTCount, s3FilePath, gbqTableName])
                            rCount += 1
                            self.table.append([rCount, s3FilePath, gbqTableName, gbqTableSize, gbqTotalNoRows])
                        else:
                            self.fCount += 1
                            self.getFBucketName.append([self.fCount, s3FilePath])

                header = ["ID", "S3 File Name", "BQ Table Name", "BQ Table Size", "BQ Table number of rows"]
                email_str = "<b><br>Total number of matched s3 / gbq : {}<br></b>".format(len(self.table)) + \
                            process_table.convert_to_html(header, self.table, "activision-file-drop")
                print(process_table.tabulate_origin(header, self.table, tablefmt="grid"))
                for iterTable in self.table:
                    self.data["s3Data"].append(iterTable)

                self.data.update[{"totalTableCount": '{}'.format(len(self.table))}]

                if self.fCount > 0 and len(self.getFBucketName) > 0:
                    logger.error("The following s3 files are not present in the GBQ : {}, Please check".format(
                        self.getFBucketName))
                    self.data.update[{"noFileCondition": True}]
                    self.data.update[{"noFileCount": '{}'.format(len(self.getFBucketName))}]
                    for iterTable in self.getFBucketName:
                        self.data["NoFileGBQ"].append(iterTable)

                    header = ["ID", "S3 File Name"]
                    email_str = email_str + "<br></br>" + \
                                "<b><br>Failed : Total number of unmatched s3 files : {}<br></b>".format(
                                    len(self.getFBucketName)) + \
                                "<br>The following s3 files are not present in the GBQ : <br>" + \
                                process_table.convert_to_html(header, self.getFBucketName, "activision-file-drop")
                    print(process_table.tabulate_origin(header, self.getFBucketName, tablefmt="grid"))
                    process_email.sendEmail(email_str, "GBQ Activision S3 Report - FAILURE - {}".format(self.today_str),
                                            sys.argv[2])
                    self.convertHTML(self.data)
                    self.createOpsgenie()
                    sys.exit(self.FAILED_EXIT_CODE)
                elif len(self.getTableRowCount) > 0:
                    logger.error(
                        "The s3 files and GBQ tables are present but the row count is greater than zero : S3 Buckets are {}, Please check".format(
                            self.getTableRowCount))
                    self.data.update[{"rowNotMatchCondition": True}]
                    self.data.update[{"GBQRowCount": '{}'.format(len(self.getTableRowCount))}]
                    for iterTable in self.getTableRowCount:
                        self.data["noRowCountGBQ"].append(iterTable)

                    header = ["ID", "S3 File Name", "BQ Table Name"]
                    email_str = email_str + "<br></br>" + \
                                "<b><br>Failed : The s3 files and GBQ tables are present but the row count is greate than zero<br></b>" + \
                                "<br>Total number of mismatched row count tables: {}<br>".format(
                                    len(self.getTableRowCount)) + \
                                "<br>The following s3 files and GBQ tables <br>" + \
                                process_table.convert_to_html(header, self.getTableRowCount, "activision-file-drop")
                    process_email.sendEmail(email_str, "GBQ Activision S3 Report - FAILURE - {}".format(self.today_str),
                                            sys.argv[2])
                    self.convertHTML(self.data)
                    self.createOpsgenie()
                    sys.exit(self.FAILED_EXIT_CODE)
                else:
                    process_email.sendEmail(email_str, "GBQ Activision S3 Report - SUCCESS - {}".format(self.today_str),
                                            sys.argv[2])
                    logger.info("Successfully sent a email")


if __name__ == '__main__':
    callFunc = getDBCredentials()
    callFunc.validateS3WithGBQ()