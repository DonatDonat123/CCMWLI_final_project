import json
import requests
import time
import urllib
import config
from nlp import NLP
import os.path
from preproc import preproc
import pandas as pd
from keras.models import load_model
import pickle

URL = "https://api.telegram.org/bot{}/".format(config.TOKEN)

#///////////////////////////////////////////////


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    print("updates")
    if offset:
    	url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)

def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)
    
def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def handle_updates(updates, nlp):
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            #items = db.get_items(chat)
            message = nlp.respond(text)
            print("response = " + message)
            send_message(message, chat)
        except KeyError:
            pass

def main():
    last_update_id = None
    if not os.path.isfile("proc_data/proc_data.pkl"):
        preproc()
    if not os.path.isfile("model/encoder.h5"):
        preproc()
    df = pd.read_pickle("proc_data/proc_data.pkl")
    encoder = load_model("model/encoder.h5")
    with open("word_vectors/word_indx.csv", 'rb') as outfile:
        word_index = pickle.load(outfile)
    with open("word_vectors/embedding_matrix.csv", 'rb') as outfile:
        embedding_matrix = pickle.load(outfile)
    nlp = NLP(df, encoder, word_index, embedding_matrix, 200, 200)
    print("The bot is now active")
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates, nlp)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
