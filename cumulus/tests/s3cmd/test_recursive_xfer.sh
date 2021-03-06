#!/bin/bash

bucket_name=CumulusTest$RANDOM
fname=GRP$RANDOM
src_dir=`mktemp -d`
dest_dir=`mktemp -d`

for i in `seq 1 10`
do
    cp /etc/group $src_dir
done

s3cmd mb s3://$bucket_name
# just run it a few times for races
s3cmd -r put $src_dir s3://$bucket_name/
if [ "X$?" != "X0" ]; then
    echo "recursive put failed"
    exit 1
fi
s3cmd -r get s3://$bucket_name/ $dest_dir
if [ "X$?" != "X0" ]; then
    echo "recursive get failed"
    exit 1
fi

x=`basename $src_dir`
diff -r -q $src_dir $dest_dir/$x
if [ "X$?" != "X0" ]; then
    echo "diff failed"
    exit 1
fi
rm -rf $src_dir
rm -rf $dest_dir

s3cmd -r --force del s3://$bucket_name/
if [ "X$?" != "X0" ]; then
    echo "ERROR: delete bucket failed"
    exit 1
fi
exit 0
