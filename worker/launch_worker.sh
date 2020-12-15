#!/bin/bash
mkdir /home/ec2-user/.aws
mkdir /home/ec2-user/.nfs
region="REGION"
access_key="ACCESS_KEY"
secret_access_key="SECRET_ACCESS_KEY"
session_token="SESSION_TOKEN"
printf "[default]\naws_access_key_id=$access_key\naws_secret_access_key=$secret_access_key\naws_session_token=$session_token\nregion=$region" > /home/ec2-user/.aws/credentials
work_url="WORK_QUEUE_URL"
unsolved_url="UNSOLVED_QUEUE_URL"
solving_url="SOLVING_QUEUE_URL"
printf "$work_url\n$unsolved_url\n$solving_url" > /home/ec2-user/.aws/queues
yum update
yum install -y amazon-efs-utils
yum install -y docker
mount -t efs "FILE_SYSTEM_ID": /home/ec2-user/.nfs
systemctl start docker
systemctl enable docker
docker pull alexjcarolan/worker:1.0
docker run -v /home/ec2-user/.aws/:/root/.aws/ -v /home/ec2-user/.nfs/:/root/.nfs/ --user=root -d alexjcarolan/worker:1.0