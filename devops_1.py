import boto3
import time

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
            systemctl start httpd
            echo '<html>' > index.html
            echo 'Private IP address: ' >> index.html
            TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
            curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html
            cp index.html /var/www/html/index.html"""
    )

time.sleep(3) # Sleep for 3 seconds

print ("Created new EC2 instances:")
print ("ID: ", new_instances[0].id)
print ("Name: ", new_instances[0].tags[0]['Value'])
#print ("IP Address: ", new_instances[0].public_ip_address)

#for inst in ec2.instances.all():
#    print(inst.id, inst.state, inst.instance_type, inst.public_ip_address)


inst = ec2.Instance(new_instances[0].id)
print("TEST", inst.id, inst.state, inst.instance_type, inst.public_ip_address)
print("http://"+inst.public_ip_address)
