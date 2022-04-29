import boto3
import json
import os
import requests
from string import punctuation

RAPIDAPI_KEY = os.environ['rapidapi_key']
WORDS_URL = 'https://wordsapiv1.p.rapidapi.com/words/'
SLACK_URL = 'https://slack.com/api/'
SLACK_TOKEN = os.environ['slack_token']

ddb_client = boto3.resource('dynamodb', 'us-east-1')
syllables_cache_table = ddb_client.Table(os.environ['syllables_cache_table'])

def syllables_from_wordsapi(word):
    headers = { 'X-Mashape-Key': RAPIDAPI_KEY }
    word_info = json.loads(requests.get(f'{WORDS_URL}{word}', headers=headers).text)
    if 'syllables' in word_info:
        return int(word_info['syllables']['count'])
    else:
        print(f'No syllable count for {word} - defaulting to 1')
        return None


def syllables(word):
    check_cache = syllables_cache_table.get_item(Key={'word':word})
    if 'Item' in check_cache:
        return int(check_cache['Item']['syllables'])
    else:
        count = syllables_from_wordsapi(word)
        if count is None:
            syllables_cache_table.put_item(Item={'word':word, 'syllables':1, 'needs_review':True})
        else:
            syllables_cache_table.put_item(Item={'word':word, 'syllables':count})
        return count or 1
        
def user_from_id(id):
    return requests.post(
        f'{SLACK_URL}users.profile.get',
        headers={'Authorization': f'Bearer {SLACK_TOKEN}'},
        data={
            'user': id
        }
        ).json()

def send_message(text, channel_id, thread_ts):
    return requests.post(
            f'{SLACK_URL}chat.postMessage', 
            headers={
                'Content-Type': 'application/json; charset=utf8',
                'Authorization': f'Bearer {SLACK_TOKEN}'
            },
            json={
                'channel': channel_id, 
                'text': text,
                'thread_ts': thread_ts
            }
        )
        
def should_ignore(slack_event):
    if 'bot_id' in slack_event:
        return True
    if 'text' not in slack_event:
        return True
    if slack_event['type'] != 'message':
        return True
    if not (slack_event['channel_type'] == 'channel' or slack_event['channel_type'] == 'group'):
        return True
    return False
    
def haiku_ify(input_text):
    words = input_text.split(' ')
    line_count = 0
    syllable_count = 0
    current_line = ''
    output_text = ''
    for i, word in enumerate(words):
        if len(current_line) == 0:
            current_line += word.capitalize()
        else:
            current_line += word
        current_line += ' '
        syllable_count += syllables(word.strip(punctuation).lower())
        if syllable_count == 5 or syllable_count == 12 or syllable_count == 17:
            output_text += current_line
            output_text += '\n'
            current_line = ''
            line_count += 1
    print(f'{line_count} ; {syllable_count}')
    if line_count == 3 and syllable_count == 17:
        return output_text
    else:
        return None

def lambda_handler(event, context):
    slack_event = json.loads(event['body'])['event']
    print(slack_event)
    if should_ignore(slack_event):
        return {
            'statusCode': 200
        }

    channel_id = slack_event['channel']
    input_text = slack_event['text'].replace('-', ' ').replace('...', '... ')
    haiku = haiku_ify(input_text)
    
    if haiku:
        print('this is a haiku')
        haiku = haiku.strip().replace("\n", "\n>")
        user = user_from_id(slack_event['user'])['profile']['real_name']
        ts = slack_event['ts']
        haiku = f'>{haiku}\n -{user}'
        print(send_message(haiku, channel_id, ts).text)
    return {
        'statusCode': 200,
        'body': haiku
    }
