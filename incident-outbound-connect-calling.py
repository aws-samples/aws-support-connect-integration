---
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import json
import boto3


# Read the environment variables
PHONE_NUMBERS_TO_NOTIFY = os.environ.get("PHONE_NUMBER_TO_NOTIFY")
CONNECT_OUTBOUND_INSTANCE_ID = os.environ.get("CONNECT_OUTBOUND_INSTANCE_ID")
CONNECT_OUTBOUND_SOURCE_PHONE = os.environ.get("CONNECT_OUTBOUND_SOURCE_PHONE")
CONNECT_OUTBOUND_CONTACT_FLOW_ID = os.environ.get("CONNECT_OUTBOUND_CONTACT_FLOW_ID")
CONNECT_REGION = os.environ.get("CONNECT_REGION")

awssupport_client = boto3.client("support")
connect_client = boto3.client("connect", region_name=CONNECT_REGION)

def process_and_notify_support_activity(activity):
    "Function processes the messages from EventBridge and invokes Amazon Connect notifications"
    activity = json.loads(activity["Sns"]["Message"])
    case_display_id = activity["detail"]["display-id"]
    case_id = activity["detail"]["case-id"]

    print("Case Display ID:" + case_display_id)

    retrieve_case = awssupport_client.describe_cases(
        caseIdList=[case_id]
    )

    case_severity = retrieve_case['cases'][0]['severityCode']

    print("Case severity:" + case_severity)

    if case_severity == "urgent" or case_severity == "critical":
        # Retrieve the case subject to update the outbound connect message
        case_subject = retrieve_case['cases'][0]['subject']

        # Make the outbound call with the Incident subject
        connect_client.start_outbound_voice_contact(
                DestinationPhoneNumber=PHONE_NUMBERS_TO_NOTIFY,
                ContactFlowId=CONNECT_OUTBOUND_CONTACT_FLOW_ID,
                InstanceId=CONNECT_OUTBOUND_INSTANCE_ID,
                SourcePhoneNumber=CONNECT_OUTBOUND_SOURCE_PHONE,
                Attributes={'SUPPORT_INCIDENT_DETAILS':case_subject}
                )
        print("Outbound call initiated to: " + PHONE_NUMBERS_TO_NOTIFY)
                
def handler(event, context):
    print(event)
    if "Records" not in event:
        return
    for activity in event["Records"]:
        process_and_notify_support_activity(activity)
