#!/bin/bash
#this script will upload the content of code directory to s3 bucket and update the cfn serverless template with updated uri
set -ex -o pipefail
if [ $# == 2 ];then
  cd code
  zip -r /tmp/latest.zip *
  cd -
  s3Path=s3://${2}/${1}-$(sha256sum /tmp/latest.zip|cut -c-8).zip 
  sed -i s%s3://.*%${s3Path}% templates/sam-stacks.j2
  aws s3 cp /tmp/latest.zip ${s3Path} 
else
  echo "Specify appname and s3 bucket name"
fi
