import requests, re, time, datetime, boto3, logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class dataObject():
    def __init__(self, text):
        n = datetime.datetime.now()
        self.date = n.strftime("%Y-%m-%d")
        self.day = n.strftime("%A")
        self.time = n.strftime("%H:%M")
        self.value = text
        self.seconds = int(time.time())
        logger.info("dataObject Created: {}, {}, {}, {}".format( \
            self.seconds,self.date,self.time,self.value))

def checkGymOcc():
    logger.info("Requesting Gym info")
    r = requests.get('https://www.st-andrews.ac.uk/sport/')
    # Either request fails, html has no length, or cannot find RegEx text.
    if r.status_code != 200:
        logger.error("Gym request failed - Code: {}".format(r.status_code))
        return None
    elif len(r.text) == 0:
        logger.error("HTML is empty")
        return None
    else:
        found =  re.findall('Occupancy: (\d\d?)%',r.text)
        if len(found) == 0:
            logger.error("No Occupancy Found")
            return None
        elif len(found) > 1:
            logger.error("Multiple Regex Hits")
            return None
        else:
            logger.info("Gym value recorded successfully")
            return "{}%".format(found[0])

def makeDatabaseEntry():
    data = dataObject(checkGymOcc())

    dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
    table = dynamodb.Table('GymCheckerData')

    logger.info("Sending PUT request to Database")

    try:
        r1 = table.put_item(
            Item={
                'ID' : data.seconds,
                'date' : data.date,
                'day' : data.day,
                'time' : data.time,
                'value' : data.value
            }
        )
        logger.info("{}".format(r1))
        logger.info("PUT successful")
        return r1

    except Exception as e:
        logger.error("Failed to interface with database")
        logger.error("{}".format(e))
        return None

def lambda_handler(event, context):
    logger.info("Event logged: {}, {}".format(event,context))
    returnValue = makeDatabaseEntry()
    logger.info("Function complete.")
    return {
        "statusCode": 200,
        "body": returnValue
    }
