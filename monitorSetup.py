import boto3
import os
import json

events = boto3.client('events')
cloudwatch = boto3.client('cloudwatch')
ec2 = boto3.client('ec2')
sns = boto3.client('sns')
lamda = boto3.client('lambda')

def handler(event, context):
    
    ruleName = os.environ['ruleName']
    lambdaName = os.environ['lambdaName']
    snsArn = os.environ['snsArn']
    recoverInstance = os.environ['recoverInstance']
    createDashboard = os.environ['createDashboard']
    dashboardName = os.environ['dashboardName']
    tagKey = os.environ['tagKey']
    tagValue = os.environ['tagValue']
    alarmPeriod = os.environ['alarmPeriod']
    evaluationPeriods = os.environ['evaluationPeriods']
    instanceRegion = os.environ['instanceRegion']

    # filter instances by tag and state 
    response = ec2.describe_instances(Filters=[
        {
            'Name': 'tag:' + tagKey,
            'Values': [tagValue]
        },
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        }
    ])
    
    # for every instance
    for reservations in response['Reservations']:
        for instances in reservations['Instances']:
            
            instanceName = '' # incase there is no name

            #get name tag
            for tags in instances['Tags']:
                if tags['Key'] == 'Name': 
                    instanceName = tags['Value']
            
            print instanceName
            
            # get instance id
            instanceID = instances['InstanceId']
            print instanceID
            
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
                        "region": instanceRegion,
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
            
            # if system needs to recover instance
            if recoverInstance == 'Yes':
                # make the recover instance string
                recoverCommand = 'arn:aws:automate:' + instanceRegion + ':ec2:stop'
                print recoverCommand
                
                #create alarm
                response = cloudwatch.put_metric_alarm(
                    AlarmName = instanceID,
                    AlarmDescription = ('Status check alarm'),
                    ActionsEnabled = True,
                    AlarmActions = [
                        snsArn,
                        recoverCommand
                    ],
                    MetricName = 'StatusCheckFailed',
                    Namespace = 'AWS/EC2',
                    Statistic = 'Maximum',  # change if metric changes
                    Period = int(alarmPeriod),
                    # Unit = 'Seconds', # this breaks things 
                    EvaluationPeriods = int(evaluationPeriods),
                    Threshold = 1.0,
                    ComparisonOperator = 'GreaterThanOrEqualToThreshold',
                    Dimensions = [
                        {
                        'Name': 'InstanceId',
                        'Value': instanceID
                        },
                    ],
                ) 
                
            # if system isn't supposed to recover instance
            if recoverInstance == 'No':
                response = cloudwatch.put_metric_alarm(
                    AlarmName = instanceID,
                    AlarmDescription = ('Status check alarm'),
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
                )       
                
    # everything below this is so this function doesn't run again            
    response = events.remove_targets(
        Rule = ruleName,
        Ids = [
            lambdaName
        ]
    )     

    # disable rule because it cannot delete 
    # cannot delete rule with targets apparently
    response = events.disable_rule(
        Name = ruleName
    )   