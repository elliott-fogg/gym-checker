# gymchecker

### Definition

The **gymchecker** repository is a collection of scripts to be used with the
AWS Lambda and DynamoDB services to monitor and analyse the occupancy of the
St Andrews Athletic Union Gym over time.

##

### Script Functions:

###### aws_function.py

    An AWS Lambda script that scrapes the HTML text of my local gym for its current capacity,
    and uploads that value to an AWS DynamoDB entity. Requires a virtualenv to run,
    as it requires the *Requests* library to be installed.


###### database_class.py

    A python file describing the _**databaseObject**_ class, which is used to
    download and locally store the data from the AWS DynamoDB entity, for further
    use.


**update_aws_package.sh**

    A shell script that updates the **data/aws_package.zip** file to be uploaded to
    the AWS Lambda function, by creating a VirtualEnv, downloading the required
    dependencies, zipping them up along with the **aws_function.py** script, and
    then deleting the VirtualEnv.


**data/**

    The **data/** folder currently holds data files, such as an example response
    from the AWS DynamoDB entity, and the **aws_package.zip** file.


**demos/**

    The **demos/** directory holds scripts that are still in experimental stages
    and are not yet ready to be considered part of the main program, as well as
    proof-of-concept scripts.
