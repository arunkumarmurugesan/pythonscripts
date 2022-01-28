import datetime
import os
from datetime import datetime, timedelta, date
import re
import logging
from dateutil.tz import tzutc
from google.cloud import bigquery
from google.oauth2 import service_account

# import pandas as pd

# Enable the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S %Z')
ch.setFormatter(formatter)
logger.addHandler(ch)


class gbqTableExpire:
    def __init__(self):
        self.FAILED_EXIT_CODE = 1
        self.GCPPROJECTID = "ecstatic-maxim-596"
        self.expiration = datetime.now(tzutc()) + timedelta(days=30)
        self.getyesterday = datetime.now(tzutc()) - timedelta(days=1)
        self.getdaybeforeyesterday = datetime.now(tzutc()) - timedelta(days=2)
        self.todayDate = datetime.now().strftime("%Y%m%d")
        self.yesterday = datetime.strftime(self.getyesterday, "%Y%m%d")
        self.daybeforeyesterday = datetime.strftime(self.getdaybeforeyesterday, "%Y%m%d")

    def gcpConnect(self):
        try:
            # key_path = "/Users/vpari/Downloads/viant-service-accounts-7013b3d7b163.json"
            key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            credentials = service_account.Credentials.from_service_account_file(
                key_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        except Exception as err:
            logger.err(
                "Please Set the GOOGLE_APPLICATION_CREDENTIALS as environment variable, Exception : {}".format(err))
            raise err
        return credentials

    def getGBQQuery1(self):
        # Run a SQL Script
        sql_script = """select T.* from `ecstatic-maxim-596.kochava.movement_{}` as T left join `ecstatic-maxim-596.kochava.movement_{}` as Y on T.device_id_value = Y.device_id_value and T.device_id_type = Y.device_id_type and T.activity_datetime = Y.activity_datetime where Y.device_id_value is null and Y.device_id_type is null and Y.activity_datetime is null;""".format(
            self.yesterday, self.daybeforeyesterday)
        print(sql_script)
        return sql_script

    def updateTableExpire(self):
        dataset_id = "kochava"
        credentials = self.gcpConnect()
        try:
            gcp_client = bigquery.Client(credentials=credentials, project=self.GCPPROJECTID)
        except Exception as e:
            if e == 'Iterator has already started'
            gcp_client = bigquery.Client(credentials=credentials, project=self.GCPPROJECTID)
            datasets = list(gcp_client.list_datasets())
            print(datasets)
        # except Exception as err:
        #     logger.error("Unable to make GCP Session: Exception : {}".format(err))
        try:
            tables = gcp_client.list_tables(dataset_id)
            for iterate_table in tables:
                # print(i.project,i.dataset_id,i.table_id)
                if "movement_" in iterate_table.table_id:
                    # print(self.todayDate, iterate_table.table_id)
                    if self.todayDate in iterate_table.table_id:
                        logger.info(
                            "Found the today's table : {}, Project:  {}, Dataset: {}".format(iterate_table.table_id,
                                                                                             iterate_table.project,
                                                                                             iterate_table.dataset_id))
                        project = gcp_client.project
                        dataset_ref = bigquery.DatasetReference(project, dataset_id)
                        table_ref = dataset_ref.table(iterate_table.table_id)
                        table = gcp_client.get_table(table_ref)
                        if table.expires:
                            logger.error("The table is already has expiration. The present expiration : {}".format(
                                table.expires))
                        else:
                            table.expires = self.expiration
                            table = gcp_client.update_table(table, ["expires"])  # API request
                            logger.info(
                                "Updated the expiration for the table: {}, Expires: {}".format(iterate_table.table_id,
                                                                                               table.expires))
                    else:
                        logger.debug("No Table found for today's date : {}".format(self.todayDate))
        except Exception as err:
            logger.error("Unable to update the expiration for the GBQ table : Exception : {}".format(err))

        try:
            destinationTable = "ecstatic-maxim-596.kochava.movement_{}".format(self.yesterday)
            logger.info("Destination Table is : {}".format(destinationTable))
            job_config = bigquery.QueryJobConfig(allow_large_results=True, destination=destinationTable, write_disposition="WRITE_TRUNCATE")
            parentJob = gcp_client.query(self.getGBQQuery1(), job_config=job_config)
            rowIterable = parentJob.result()
            for i in rowIterable:
                print(i)
            logger.info("Script created {} child jobs.".format(parentJob.num_child_jobs))
            rows = list(rowIterable)
            logger.info("Total Number of Rows : {}".format(len(rows)))
        except Exception as err:
            logger.error("Uable to query the table and perform overwrite. Exception : {}".format(err))


if __name__ == '__main__':
    callFunc = gbqTableExpire()
    callFunc.updateTableExpire()