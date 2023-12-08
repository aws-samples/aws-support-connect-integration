# Integrate AWS Support with Amazon Connect to receive critical outbound voice notifications

Notifications for critical [AWS Support](https://aws.amazon.com/premiumsupport/) cases are essential to ensure that issues that affect your workloads are addressed quickly. AWS Support sends email notifications automatically when support cases are newly created or updated in your AWS accounts, and they can be viewed in AWS Support Center, or the [AWS Managed Services(AMS)](https://aws.amazon.com/managed-services/) console for customers using AMS. For critical or high priority cases, customers prefer voice notification for more immediate notice, especially during non-business hours. Today, customers use a variety of third-party tools to manage this requirement.

AWS Managed Services (AMS) leverages standard AWS services, and extends you team with guidance and execution of operational best practices with specialized automations, skills, and experience that are contextual to your environment and applications. In this blog, we will describe best practices from the AMS on how you can leverage [Amazon EventBridge](https://docs.aws.amazon.com/awssupport/latest/user/event-bridge-support.html), and [Amazon Connect](https://docs.aws.amazon.com/awssupport/latest/user/event-bridge-support.html) to receive voice notifications when there are critical updates to your AWS Support cases.

## Solution Architecture

With this solution, AWS Support API and Amazon EventBridge are integrated with Amazon Connect. AWS Support API provides access to AWS Support case management, allowing customers to manage the entire lifecycle of AWS Support cases, from case creation to resolution. Amazon EventBridge integration enables customers to rapidly detect and react to changes to their AWS Support cases.

This solution includes the setup and configuration of the following resources in your AWS account across multiple regions:

1. An Amazon Connect instance that is configured to send outbound voice notifications in the AWS Region where you need the notifications to be sent.

The AWS Support API and the Amazon EventBridge integration with the Support API are accessible via us-east-1 endpoint. Therefore, this part of the solution must be deployed in the us-east-1 Region. 

    **Solution components deployed in US-EAST-1 Region:**

1.	An [Amazon EventBridge rule](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rules.html) to initiate automated actions when AWS Support Cases are created or updated
1.	An [Amazon Simple Notification Service (Amazon SNS)](http://aws.amazon.com/sns) topic to which the EventBridge rule will publish when support activity has taken place.
1.	An [AWS Lambda](http://aws.amazon.com/lambda) function that gets triggered when SNS messages are received and makes Amazon Connect outbound calls to report high severity incidents

![Solution Architecture](/images/Solution-Architecture.jpg)

The solution works as follows:
1.	A Support Case is created or updated in your AWS account.
1.	An Event is put on the EventBridge event bus, and this event is evaluated by EventBridge to determine if there is a matching EventBridge rule.
1.	An EventBridge rule is triggered when the event matches the following pattern:

   ```json
   {
        "detail-type": ["Support Case Update"],
        "source": ["aws.support"],
        "detail": {
            "event-name": ["CreateCase"]
        }
    }
   ```

1.	The EventBridge rule publishes the event to a SNS Topic.
1.	The SNS Topic triggers a Lambda function, passing a copy of the message received from EventBridge to the function.
1.	The Lambda function evaluates the message, retrieves the severity of the incident from AWS Support.
1.  The Lambda function initiates an outbound voice notification to the users through Amazon Connect when the severity of the incident matches the high severity.

## Prerequisites

The following are the prerequisites to deploy this solution:
•	An AWS Account with [AWS Command Line Interface (AWS CLI)](https://aws.amazon.com/cli/) configured.
•	The AWS account must be enrolled in Business Support, Enterprise On-Ramp, or Enterprise Support to access the AWS Support API.
•	[Git](https://git-scm.com/) to download the sample file source code.

## Solution Walkthrough

Following are the steps involved in setting up the solution.
1.	Create an Amazon Connect Instance and configure to make outbound calls.
1.	Create an Amazon Connect contact flow for outbound voice contact.
1.	Deploy the CloudFormation template.
1.	Create a test AWS Support Case to verify that the solution has been implemented.

### Step 1 – Provision an Amazon Connect Instance and configure to make outbound calls
1.	The AWS Region where your Amazon Connect instance is provisioned determines which countries you can make outbound calls. [Refer to the countries you can call here](https://docs.aws.amazon.com/connect/latest/adminguide/amazon-connect-service-limits.html#country-code-allow-list). Select the appropriate AWS Region for your Amazon Connect instance where you could send outbound support notifications to your phone numbers.

1.	Follow the steps detailed below in the link to create an Amazon Connect instance https://docs.aws.amazon.com/connect/latest/adminguide/amazon-connect-instances.html. When setting up **Telephony** during the Amazon Connect Instance creation, make sure you choose **Allow outgoing calls**.

1.	Login to the Amazon Connect instance you created and claim a phone number to use for outbound voice notifications. Follow the steps described here - https://docs.aws.amazon.com/connect/latest/adminguide/contact-center-phone-number.html. Make sure the number you claim can make outbound calls to the destination country for the voice notification.

1.	Navigate to **Routing** and **Queues**. Edit the **BasicQueue** and update the below information:
    1.	**Settings** – Setup **Default caller ID name** and select the phone number you claimed for the **Outbound caller ID number**. Save the configurations

1.	Navigate to **Users** and **Routing profiles** and edit the **Basic Routing Profile**. Navigate to **Settings** and **Queues**. Navigate to **Default outbound queue** and choose **BasicQueue** to be associated with outbound calls.

### Step 2 – Create an Amazon Connect contact flow for outbound voice contact
1.	Download the contact flow json file from https://github.com/aws-samples/aws-support-connect-integration/blob/main/AMS_Outbound_Final.json
1.	Navigate to **Routing** and **Contact flows** and **Create contact flow**.
1.	Enter a name to the contact flow.
1.	Choose the **Save** dropdown button and choose **Import flow**.
1.	Select the contact flow you downloaded. The imported contact flow appears on the canvas as described below with three blocks – **Entry point**, **Play prompt** and **Disconnect**. 

    ![Amazon Connect Contact Flow](/images/Contact-flow-view.jpg)

    You will observe that the **Play prompt** block has an attribute ***SUPPORT_INCIDENT_DETAILS*** configured under **Text-to-speech or chat text**. This attribute is updated by the Lambda function deployed in the next step with the high priority support incident subject to trigger outbound voice notifications, hence do not change this attribute name. 

1.	Save the contact flow

### Step 3 – Deploy the CloudFormation template
You can deploy the CloudFormation template either by logging to the AWS Console or via AWS CLI. The CloudFormation template requires four parameters.
1.	**PhoneNumberToNotify**: Phone number that receives the Incident notification call. Phone number should be in E.164 format +(Country Code)(Phone Number)
Example: +61464646464

1.	**ConnectOutboundInstanceID**: Amazon Connect Instance ID provisioned for facilitating the Outbound Incident calls. You can find details on how to find the Instance ID here: https://aws.amazon.com/premiumsupport/knowledge-center/find-connect-instance-id/

1.	**ConnectOutboundSourcePhone**: Amazon Connect Instance outbound phone number that was claimed earlier (Step 1 (b)) to initiate the outbound incident notifications. Phone number should be in E.164 format +(Country Code)(Phone Number)

1.	**ConnectOutboundContactFlowID**: Amazon Connect Contact Flow ID configured for sending the outbound notification. You can find more details on how to find the contact flow id here: https://docs.aws.amazon.com/connect/latest/adminguide/find-contact-flow-id.html

1.	**ConnectRegion**: AWS Region where Amazon Connect is deployed in '***Step-1 - Create an Amazon Connect Instance and configure to make outbound calls***'

**Deploying the CloudFormation template via AWS CLI into the us-east-1 Region**

```bash
#Clone the Git Repository
git clone https://github.com/aws-samples/aws-support-connect-integration.git
# Change Directory into the repository
cd ./abc
# Use the AWS CLI to deploy the CloudFormation template
aws cloudformation deploy \
--template-file template.yml \
--stack-name <StackName> \
--capabilities CAPABILITY_IAM \
--region us-east-1 \
--parameter-overrides <parameters>
```

### Step 4: Create a test AWS Support Case to verify that the solution has been implemented

Using the AWS Console, AWS CLI, or APIs, create a new AWS Support Case with severity level. For test cases, use the subject TEST CASE-Please ignore.
After creating the case, you will receive a phone call on the number configured as ‘PhoneNumberToNotify’ and you will hear the incident subject. 

**Considerations for production use**

The following aspects should be considered for use in production:

**Encryption** – To automatically encrypt the messages during transit, it is recommended to use HTTPS.  To enforce only encrypted connections over HTTPS, add the aws:SecureTransport condition in the IAM policy that's attached to unencrypted SNS topics. For data protection at rest, leverage server-side encryption (SSE). SSE uses keys managed in AWS Key Management Service (KMS). Please refer to SNS security best practices - https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html 

**Logging** – As a best practice, it is recommended to include structured logging in the AWS Lambda function to help interpret and analyze programmatically. In the sample code, structured logging isn’t included. Please refer to structured logging details here - https://docs.aws.amazon.com/lambda/latest/operatorguide/parse-logs.html

**Reserved concurrency** – You may need to consider reserved concurrency if there are other Lambda functions in the Region may consume all of the available account capacity, and could prevent the Lambda function in this solution from running.

**Log retention** – The sample code provided with this post has a hard-coded Amazon CloudWatch Logs retention period of seven days. Customers should consider their own data storage retention policies when using it in production.

**Amazon Connect Security Best Practices** – Please refer to Amazon Connect security best practices - https://docs.aws.amazon.com/connect/latest/adminguide/security-best-practices.html 

**Cleanup**

You can clean-up the AWS Resources that were deployed in two steps.

1.	 From AWS CLI run the following command to delete the EventBridge setup and configurations:
```bash
aws cloudformation delete-stack --stack-name <StackName> --region us-east-1
```
2.	Delete the Amazon connect instance using the steps below:
https://docs.aws.amazon.com/connect/latest/adminguide/delete-connect-instance.html

**Conclusion**

In this blog post, we covered the solution architecture and setup of Amazon Connect and Amazon EventBridge integration with AWS Support. This solution meets the requirement of receiving voice notifications for critical cases raised via AWS Support. We started by showing how to provision and configure an Amazon Connect instance in the AWS Region where you need the notifications to be sent. Then, we showed you how to deploy the CloudFormation stack that sets up an Amazon EventBridge rule and a Lambda function to trigger notifications via the Amazon Connect when high priority incidents are updated or raised. Finally, we showed you how to test the solution and provided references to best practices for production use. For help in scaling and operating more efficiently on AWS, visit [AWS Managed Services(AMS)](https://aws.amazon.com/managed-services/) for more information.
