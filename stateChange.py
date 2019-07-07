import boto3
import os

ec2 = boto3.client('ec2')
sns = boto3.client('sns')
iam = boto3.client('iam')

def handler(event,context):
    # information from cloudformation template
    snsArn = os.environ['snsTopic']
    tagKey = os.environ['tagKey']
    tagValue = os.environ['tagValue']
    restartInstance = os.environ['restartInstance']
    
    #getting instance state and id from event     
    instanceState = event['detail']['state']
    instanceID = event['detail']['instance-id']
    instanceRegion = event['region']
    time = event['time']
    instanceName = '' # error prevention
    
    #get some info about the instance
    response = ec2.describe_instances(
        InstanceIds = [
            instanceID
        ]
    )

    # if false don't send a message. Turned true with tags defined in cf template
    sendMessage = False
    
    for reservations in response['Reservations']:
        
        #owner of instance
        ownerID = reservations['OwnerId']
        #get account alias
        account = iam.list_account_aliases(
            )
        for alias in account['AccountAliases']:
            ownerAlias = alias
        
        
        for instances in reservations['Instances']:

            #get tags
            for tags in instances['Tags']:
                if tags['Key'] == tagKey and tags['Value'] == tagValue:
                    print tags['Key']
                    print tags['Value']
                    sendMessage = True
                    print 'send message is true'
                
                #get instance name
                if tags['Key'] == 'Name':
                    instanceName = tags['Value']
    
    print sendMessage
    print instanceState
    if sendMessage and instanceState == 'stopped':
        
        #message that will be sent
        message = ('An EC2 instance has been stopped or terminated that was not supposed to' +
            '\nInstance: ' + instanceName + ' ' + instanceID + ' ' +
            '\nOwner: ' + ownerAlias + ' ' + ownerID +
            '\nRegion: ' + instanceRegion +
            '\nTime: ' + time)
        
        print restartInstance
        if restartInstance == 'Yes':
            
            # start the instance
            response = ec2.start_instances(
                InstanceIds=[
                    instanceID,
                ]
            )
            
            # update the message
            message = message + '\nThe instance has been restarted'
        
        print 'test'
        print snsArn
        print message
        #publish to sns
        response = sns.publish(
            TopicArn= snsArn,
            Message = message
        )