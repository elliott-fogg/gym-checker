#!/bin/bash

rm data/aws_package.zip

virtualenv -p python3 venv
source venv/bin/activate
pip install requests boto3
deactivate

cd venv/lib/python3.5/site-packages/
zip -rq9 ../../../../data/aws_package.zip .
cd ../../../../
zip -gq data/aws_package.zip gymchecker_aws.py

rm -r venv

echo "AWS Package Generation Complete."
