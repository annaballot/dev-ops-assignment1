import boto3

ec2 = boto3.resource('ec2')
new_instances = ec2.create_instances(
    ImageId='ami-0277155c3f0ab2930',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.nano',
    KeyName='abstudentkey',
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags' : [
                {
                'Key': 'Name',
                'Value': 'Annas Assignment 1 Web Server'
                },
            ]
        },
    ],
    SecurityGroups=[
        'httpssh',
    ],
    UserData="""#!/bin/bash
            yum install httpd -y
            systemctl enable httpd
            systemctl start httpd"""
    )

print ("ID: ", new_instances[0].id)
print ("Name: ", new_instances[0].tags[0]['Value'])
