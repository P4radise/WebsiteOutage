#!/usr/bin/env python3
import boto3
import botocore
import json
import os
import uuid
import pandas
import datetime
import onevizion

# Handle command arguments
import argparse
Description="""Pull Outages from AWS Alerts for Websites down.  Gather the downtime and push into Trackor.
"""
EpiLog = onevizion.PasswordExample + """\n\n
"""
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description=Description,epilog=EpiLog)
parser.add_argument(
	"-v",
	"--verbose",
	action='count',
	default=0,
	help="Print extra debug messages and save to a file. Attach file to email if sent."
	)
parser.add_argument(
	"-p",
	"--parameters",
	metavar="ParametersFile",
	help="JSON file where parameters are stored.",
	default="SettingsFile.integration"
	)
args = parser.parse_args()
ParametersFile = args.parameters
onevizion.Config["Verbosity"] = args.verbose
Message = onevizion.Message
TraceMessage = onevizion.TraceMessage

# Load in Passwords from protected file.
ParameterData = onevizion.GetParameters(ParametersFile)

# Setup Variables
AWSRegion=ParameterData["AWSConfig"]["Region"]
AWSAccessKey=ParameterData["AWSConfig"]["AccessKey"]
AWSSecretKey=ParameterData["AWSConfig"]["SecretAccessKey"]
DateFormatStr = "%Y-%m-%d %H:%M:%S"

FileNameHead = __file__[:-3]
FileDateFooter = datetime.datetime.now().strftime('%Y-%m-%d')

NNow = datetime.datetime.now()
Today= datetime.datetime(NNow.year,NNow.month,NNow.day)
Yesterday = Today - datetime.timedelta(days=25)


def myconverter(o):
	if isinstance(o, datetime.datetime):
		return o.strftime(DateFormatStr)


##################################
# Main Program starts here
#################################
Locker = onevizion.Singleton()
onevizion.Config['Err'] = False

# Get Website alarm list
TraceMessage("Getting Alarm List for Websites.")
client = boto3.client(
	'cloudwatch',
	region_name=AWSRegion,
	aws_access_key_id=AWSAccessKey,
	aws_secret_access_key=AWSSecretKey
	)


AlarmsList  = client.describe_alarms(
	AlarmNamePrefix='Website',
	MaxRecords=100
	)["MetricAlarms"]
#AlarmsList = AlarmsList[len(AlarmsList)-1:]
TraceMessage(json.dumps(AlarmsList,indent=2,default=myconverter),2)

#Go through Alarm List and get data for each
TraceMessage("Get Data for each Alarm")
Alarms = {}
OutageList=[]
for alarm in AlarmsList:
	AlarmData = client.describe_alarm_history(
		AlarmName=alarm["AlarmName"],
		HistoryItemType='StateUpdate',
		MaxRecords=100
		)
	TraceMessage("***************\nData for {WebSite}\n***************".format(WebSite=alarm["AlarmName"][10:]),2)
	TraceMessage(json.dumps(AlarmData,indent=2,default=myconverter),2)
	#Alarms[alarm["AlarmName"]] = json.loads(AlarmData["AlarmHistoryItems"][0]["HistoryData"])
	#TraceMessage(json.dumps(Alarms[alarm["AlarmName"]],indent=2,default=myconverter),2)
	for HistItem in AlarmData["AlarmHistoryItems"]:
		if HistItem["HistorySummary"] == "Alarm updated from ALARM to OK":
			ahi = json.loads(HistItem["HistoryData"])
			sd = datetime.datetime.strptime(ahi["oldState"]["stateReasonData"]["queryDate"],'%Y-%m-%dT%H:%M:%S.%f%z')
			ed = datetime.datetime.strptime(ahi["newState"]["stateReasonData"]["queryDate"],'%Y-%m-%dT%H:%M:%S.%f%z')
			diff=ed-sd
			oli = {
				"key":alarm["AlarmName"][10:]+"-"+sd.strftime(DateFormatStr),
				"website":alarm["AlarmName"][10:],
				"WEBOUT_DOWN":sd,
				"WEBOUT_UP":ed,
				"WEBOUT_DOWNTIME": diff.seconds
				}
			OutageList.append(oli)

TraceMessage("***************\nFinal Outage List Dump\n***************",2)
TraceMessage(json.dumps(OutageList,indent=2,default=myconverter),2)

TraceMessage("Writing Alarms.csv")
df = pandas.DataFrame(OutageList)
df.to_csv('Alarms-{DateStamp}.csv'.format(DateStamp=FileDateFooter),index = False, date_format=DateFormatStr)

# Push Import of data into Trackor
Imp = onevizion.Import(
	impSpecId=100092649,
	file='Alarms-{DateStamp}.csv'.format(DateStamp=FileDateFooter),
	action='INSERT_UPDATE',
	paramToken='trackor.onevizion.com'
	)

#Clean up temporary file
os.remove('Alarms-{DateStamp}.csv'.format(DateStamp=FileDateFooter))















