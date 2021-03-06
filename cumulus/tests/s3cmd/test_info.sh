#!/bin/bash

bucket_name=CumulusTest$RANDOM
fname=GRP$RANDOM
s3cmd mb s3://$bucket_name
s3cmd put /etc/group s3://$bucket_name/$fname
if [ "X$?" != "X0" ]; then
    echo "ERROR"
    exit 1
fi
s3cmd -d info s3://$bucket_name/$fname 
if [ "X$?" != "X0" ]; then
    echo "ERROR: info failed"
    exit 1
fi

s3cmd del s3://$bucket_name/$fname
if [ "X$?" != "X0" ]; then
    echo "ERROR: delete failed"
    exit 1
fi

s3cmd rb s3://$bucket_name
if [ "X$?" != "X0" ]; then
    echo "ERROR: delete bucket failed"
    exit 1
fi

exit 0
