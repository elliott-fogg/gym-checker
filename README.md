# gymchecker

### Definition

The <b>gymchecker</b> repository is a collection of scripts to be used with the
AWS Lambda and DynamoDB services to monitor and analyse the occupancy of the
St Andrews Athletic Union Gym over time.

##

### Script Functions:

##### aws_function.py
An AWS Lambda script that scrapes the HTML text of my local gym for its current capacity,
and uploads that value to an AWS DynamoDB entity. Requires a virtualenv to run,
as it requires the 'Requests' library to be installed.


##### <u>database_class.py</u>

A python file describing the <b><i>databaseObject</i></b> class, which is used to
download and locally store the data from the AWS DynamoDB entity, for further
use.


* <b><u>update_aws_package.sh</u></b>
<br>
A shell script that updates the <b>data/aws_package.zip</b> file to be uploaded to
the AWS Lambda function, by creating a VirtualEnv, downloading the required
dependencies, zipping them up along with the <b>aws_function.py</b> script, and
then deleting the VirtualEnv.

* <b><u>data/</u></b>
<br>
The <b>data/</b> folder currently holds data files, such as an example response
from the AWS DynamoDB entity, and the <b>aws_package.zip</b> file.

* <b><u>demos/</u></b>
The <b>demos/</b> directory holds scripts that are still in experimental stages
and are not yet ready to be considered part of the main program, as well as
proof-of-concept scripts.
