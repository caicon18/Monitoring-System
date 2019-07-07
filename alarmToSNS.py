import boto3
import ast
import os
import json

sns = boto3.client('sns')
ec2 = boto3.client('ec2')
iam = boto3.client('iam')

def handler(event, context):
    snsArn = os.environ['snsTopic']
    recoverInstance = os.environ['recoverInstance']
    
    # SNS passes event 
    for records in event['Records']:
        
        message = records['Sns']['Message']
        print (message)
        print (type(message)) # message is a string not a dict
        
        if isinstance(message, dict): # just in case it fixes itself
            messageDict = message
        else:
            messageDict = json.loads(message) # turn the string into a dictionary
        
        # get info
        instanceID = messageDict['AlarmName']
        instanceRegion = messageDict['Region']
        alarmState = messageDict['NewStateValue']
        alarmTime = messageDict['StateChangeTime']
            
    instanceName = '' # error prevention
    
    #get more info about the instance
    response = ec2.describe_instances(
        InstanceIds = [
            instanceID
        ]
    )

    # returns as a big list of lists and dictionaries
    for reservations in response['Reservations']:
        
        #owner of instance
        ownerID = reservations['OwnerId']

        #get account alias
        account = iam.list_account_aliases()
        for alias in account['AccountAliases']:
            ownerAlias = alias
        
        for instances in reservations['Instances']:

            #get tags - has instance name among other things if needed
            for tags in instances['Tags']:
                
                #get instance name
                if tags['Key'] == 'Name':
                    instanceName = tags['Value']
    
    #message that will be sent
    message = ('A status check alarm is failing' +
        '\nInstance: ' + instanceName + ' ' + instanceID + ' ' +
        '\nOwner: ' + ownerAlias + ' ' + ownerID +
        '\nRegion: ' + instanceRegion + 
        '\nAlarm State: ' + alarmState + 
        '\nTime: ' + alarmTime)
        
    if recoverInstance == 'Yes':
        message += '\nInstance is being restarted'
        
    print (message)
    
    #publish to sns
    response = sns.publish(
        TopicArn = snsArn,
    Message = message
    )