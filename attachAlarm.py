import boto3
import os
import json

cloudwatch = boto3.client('cloudwatch')

ec2 = boto3.client('ec2')

def handler(event, context):

    snsArn = os.environ['snsTopic']
    tagKey = os.environ['tagKey']
    tagValue = os.environ['tagValue']
    recoverInstance = os.environ['recoverInstance']
    createDashboard = os.environ['createDashboard']
    dashboardName = os.environ['dashboardName']
    alarmPeriod = os.environ['alarmPeriod']
    evaluationPeriods = os.environ['evaluationPeriods']
    
    print event
    instanceID = event['detail']['instance-id']
    instanceState = event['detail']['state']
    instanceRegion = event['region']


    # attaches alarm when true, turned true if tagKey and tagValue are correct
    attachAlarm = False 

    #filter down to find tags for the instance
    tag = ec2.describe_tags(
        Filters=[
            {
                'Name': 'resource-id',
                'Values': [instanceID]
            },
        ]
    )
   
    for tags in tag['Tags']:
        
        # error prevention
        instanceName = ''

        # identifying tag, named tagValue because the acual name can change
        if tags['Key'] == tagKey and tags['Value'] == tagValue:
            attachAlarm = True
            
        # finding the name of the instance
        if tags['Key'] == 'Name':
            instanceName = tags['Value']
            print instanceName
    
    print instanceState
    print attachAlarm
    print recoverInstance
    
    # recover instances   
    if instanceState == 'running' and attachAlarm and recoverInstance == 'Yes':
        print 'test: recoverInstance = Yes'
        recoverCommand = 'arn:aws:automate:' + instanceRegion + ':ec2:stop'

        #create alarm
        response = cloudwatch.put_metric_alarm(
            AlarmName = instanceID,
            AlarmDescription = ('Status Check alarm'),
            ActionsEnabled = True,
            AlarmActions = [
                snsArn,
                recoverCommand
            ],
            MetricName = 'StatusCheckFailed',
            Namespace = 'AWS/EC2',
            Statistic = 'Maximum',  #change if metric changes
            Period = int(alarmPeriod),
            #Unit='Seconds', #this breaks things 
            EvaluationPeriods = int(evaluationPeriods),
            Threshold = 1.0,
            ComparisonOperator = 'GreaterThanOrEqualToThreshold',
            Dimensions = [
                {
                'Name': 'InstanceId',
                'Value': instanceID
                },
            ],
        ) #end of put_metric_alarm   
        
    # dont recover instances
    if instanceState == 'running' and attachAlarm and recoverInstance == 'No':
        print 'test: recoverInstance = No'
        #create alarm
        response = cloudwatch.put_metric_alarm(
            AlarmName = instanceID,
            AlarmDescription = ('Status Check Alarm'),
            ActionsEnabled = True,
            AlarmActions = [
                snsArn
            ],
            MetricName = 'StatusCheckFailed',
            Namespace = 'AWS/EC2',
            Statistic = 'Maximum',  #change if metric changes
            Period = int(alarmPeriod),
            #Unit = 'Seconds', #this breaks things 
            EvaluationPeriods = int(evaluationPeriods),
            Threshold = 1.0,
            ComparisonOperator = 'GreaterThanOrEqualToThreshold',
            Dimensions = [
                {
                'Name': 'InstanceId',
                'Value': instanceID
                },
            ],
        ) #end of put_metric_alarm   
    
    print 'Create dashboard: ' + createDashboard
    # update dashboard with instance info
    if createDashboard == 'Yes':
        # get data for dashboard b/c cannot just add stuff to dash
        response = cloudwatch.get_dashboard(DashboardName = dashboardName)
        dashboardBody = response['DashboardBody']
        dashboard = json.loads(dashboardBody)
        print dashboard
        
        # this boolean is for if there is already an existing widget for the instance
        addNewWidget = True 
        
        # these for loops are checking if a widget already exists for the instance
        for widgets in dashboard['widgets']:
            for metrics in widgets['properties']['metrics']:
                for dimensions in metrics:
                    
                    if dimensions == instanceID:
                        addNewWidget = False
            # region of dashboard        
            dashRegion = widgets['properties']['region']
        
        # json stuff for widget about to be added
        if addNewWidget == True:
            newWidget = {
                "type":"metric",
                "properties":{
                    "metrics":[
                        [
                            "AWS/EC2",
                            "StatusCheckFailed",
                            "InstanceId",
                            instanceID
                        ],
                    ],
                "region": dashRegion,
                "title": instanceName + '(' + instanceID + ')',
                "stat": "Maximum",
                "view": "timeSeries"
                }
            }

            # add widget to dash json text
            dashboard['widgets'].append(newWidget)
            
            # turn into string
            newDashboard = json.dumps(dashboard)
            
             # update it 
            response = cloudwatch.put_dashboard(
                DashboardName = dashboardName,
                DashboardBody = newDashboard
                )
