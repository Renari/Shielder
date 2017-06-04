from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, JoinEvent, LeaveEvent
)
from pytz import timezone
from datetime import datetime
import random
import requests
import json
import HTMLParser
import urllib
import logging
import requests_toolbelt.adapters.appengine

requests_toolbelt.adapters.appengine.monkeypatch()

app = Flask(__name__)

#get config data
with open('config.json') as config_file:
    config = json.load(config_file)


line_bot_api = LineBotApi(config['accesstoken'])
handler = WebhookHandler(config['secret'])
fgogroup = config['fgogroup']
jst = timezone('Asia/Tokyo')

def days(x):
    return {
    'Mon':'archer materials and lancer, assassin, berserker experience',
    'Tue':'lancer materials and saber, rider and berserker experience',
    'Wed':'berserker materials and archer, caster, berserker experience',
    'Thu':'rider materials and lancer, assassin, berserker experience',
    'Fri':"caster materials and saber, rider, berserker experience",
    'Sat':"assassin materials and archer, caster, berserker experience",
    'Sun':'saber materials and all class experience',
    }[x]

@app.route('/dailies', methods=['GET'])
def dailies():
    global jst, fgogroup
    line_bot_api.push_message(fgogroup, TextSendMessage(text="The dailies are now "+days(datetime.now(jst).strftime("%a"))+"."))
    return 'OK'

@app.route('/login', methods=['GET'])
def login():
    line_bot_api.push_message(fgogroup, TextSendMessage(text="You have presents Senpai!"))
    return 'OK'

@app.route('/callback', methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info('Request body: ' + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if (event.message.text[0] == '!'):
        if(event.message.text[1:] == 'daily'):
            sendDailies(event.reply_token)
        if(event.message.text[1:] == 'time'):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="It's currently " + datetime.now(jst).strftime('%H:%M %Z') + '.'))
        if(event.message.text[1:] == 'hug'):
            if random.randint(1, 10) >= 5 or line_bot_api.get_profile(event.source.sender_id).display_name == "Renari":
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Um... thanks Senpai. *blushes*'))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='The dailies are ' + days(datetime.now(jst).strftime('%a')) + ', Senpai.'))
        if(event.message.text[1:] == 'joke'):
            joke = requests.get('http://api.icndb.com/jokes/random/')
            joke = joke.json()['value']['joke']
            joke = urllib.unquote(joke).decode('utf8')
            joke = HTMLParser.HTMLParser().unescape(joke)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=joke))

@handler.add(JoinEvent)
def handle_join(event):
    logging.info('joined: ' + str(event))

@handler.add(LeaveEvent)
def handle_leave():
    logging.info('left group')

def sendDailies(token):
    global jst
    line_bot_api.reply_message(token, TextSendMessage(text='The dailies are ' + days(datetime.now(jst).strftime('%a')) + ', Senpai.'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
