import praw
import scraping
import re
import praw.exceptions
from prawcore.exceptions import PrawcoreException
import time
import credentials
import boto3
from datetime import datetime
import pytz

tz_IN = pytz.timezone('Asia/Kolkata')
datetime_IN = datetime.now(tz_IN)

reddit = praw.Reddit(
    client_id=credentials.client_id,
    client_secret=credentials.client_secret,
    user_agent=credentials.user_agent,
    username=credentials.username,
    password=credentials.password
)
print(reddit.user.me())
print('praw initialized successfully')
s3 = boto3.client('s3',
                  aws_access_key_id=credentials.accessKey,
                  aws_secret_access_key=credentials.secretAccessKey)

s3Bucket = "aoe2-bot-logs"
s3FileKeyLog = "log.txt"
s3FileKeyLogID = "log_id.txt"

subreddit = reddit.subreddit("aoe2")
*tech_keys, = scraping.tech_all

dynamodb = boto3.client('dynamodb', region_name="us-east-1",
                        aws_access_key_id=credentials.accessKey,
                        aws_secret_access_key=credentials.secretAccessKey)

print('aws initialized successfully')
cid = []
count = 0
while True:
    try:
        response = dynamodb.get_item(TableName='aoe-bot-table',
                                     Key={
                                         "id": {"S": str(count+1)}
                                     }
                                     )
        cid.append(response["Item"]["cid"]["S"])
        count += 1
    except:
        break
print('logs retrieved')
print("count: ", count)
print("cid: ", cid)
prev_id = cid
print('searching for comments now')
try:
    for comment in subreddit.stream.comments(skip_existing=True):
        if hasattr(comment, "body") and comment.id not in prev_id:
            search_word = comment.body.replace("\\", "")
            word = re.findall(r"\[([A-Za-z0-9-\s]+)\]", search_word)
            if word is not None and len(word) > 0:
                for i in range(0, len(word)):
                    if word[i].lower() in tech_keys:
                        word[i] = word[i].lower()
                        print("Match: ", word[i])
                        comment.reply(word[i] + ": " + scraping.tech_all[word[i]])
                        print(scraping.tech_all[word[i]])
                        dynamodb.put_item(TableName="aoe-bot-table",
                                          Item={
                                              'id': {'S': str(count+1)},
                                              'Body': {'S': str(comment.body)},
                                              'cid': {'S': str(comment.id)},
                                              'Time': {"S": str(datetime_IN)}}
                                          )
                        print('comment stored in database')
                        count += 1
                        prev_id.append(comment.id)
                        print('count: ', count)
                    print("Continuing search")
        time.sleep(.15)
except KeyboardInterrupt:
    print("Interrupted by Keyboard")
    print('count: ', count)
    print(prev_id)
except PrawcoreException as e:
    print("Interrupted by ", e)
