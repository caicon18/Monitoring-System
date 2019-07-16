# Monitoring-System
System to monitor EC2 instances in AWS

HOW TO SET UP (Also in Documentation.pdf file)
-
  - Add a tag to all EC2 Instances to identify which ones will be monitored

  - Copy all of the files in this repo to an S3 bucket 
  
  - Make sure you have permissions to create IAM Roles and policies

  - Create a CloudFormation stack using the monitoringSystem.yml file

  Parameters:
-
   - The EC2TagKey and the EC2TagValue should be the key and value of the tag that was added to the EC2 instances earlier
   - Make sure the BucketName is the name of the bucket where the template and the code is in
   - If you want to add more SNS endpoints, sign up manually to the monitorNotification SNS topic that is created by the CFN          template
   - RestartInstances specifies whether the instance is turned back on when instance is accidentally turned off
   - RecoverStatusCheck specifies whether to recover the instance after a status check failure
      - Turns the instance on and off again
      - RestartInstances must be turned on

  Review:
-
   - Can ignore options page
   - In the review screen, make sure to check the Capabilities box 
      - "I acknowledge that AWS CloudFormation might create IAM resources with custom names."
      
  - It takes a little bit for the alarms to be attached
  - To change resource names, you have to edit the maps in the YAML template
  - Remember to confirm email
  - View the Documentation.pdf file for how the system works 
