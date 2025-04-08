from flask import Flask, request, jsonify, render_template
import torch
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize
import numpy as np
import json
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from pymongo import MongoClient  # ✅ MongoDB

# ----------------- MongoDB Setup -----------------
MONGO_URI = "mongodb+srv://mongodb:prashanth6224@cluster0.mbfzyjv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["chatbotDB"]
chat_collection = db["chat_history"]

# ----------------- Load Bot Data -----------------
with open("intents.json", "r") as f:
    intents = json.load(f)

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data["all_words"]
tags = data["tags"]
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size)
model.load_state_dict(model_state)
model.eval()

# ----------------- Flask App -----------------
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    sentence = data["message"].lower()

    # Rule-based responses
    if "how are you" in sentence:
        bot_reply = "I'm fine, thank you!"
    elif "time" in sentence:
        bot_reply = f"The current time is {datetime.now().strftime('%H:%M:%S')}"
    elif "hindustan times" in sentence or "news" in sentence:
        bot_reply = "\n".join(get_news())
    elif "weather" in sentence:
        bot_reply = get_weather("delhi")
    elif "prime minister" in sentence:
        bot_reply = "As of now, the Prime Minister of India is Narendra Modi."
    elif "joke" in sentence:
        bot_reply = get_joke()
    else:
        # ML prediction
        tokens = tokenize(sentence)
        X = bag_of_words(tokens, all_words)
        X = torch.from_numpy(X).unsqueeze(0)
        output = model(X)
        _, predicted = torch.max(output, dim=1)
        tag = tags[predicted.item()]
        probs = torch.softmax(output, dim=1)
        prob = probs[0][predicted.item()]
        print(f"Prediction: {tag}, Probability: {prob.item()}")

        if prob.item() > 0.75:
            for intent in intents["intents"]:
                if tag == intent["tag"]:
                    bot_reply = random.choice(intent["responses"])
                    break
        else:
            bot_reply = google_search(sentence)

    # ----------------- Save to MongoDB -----------------
    chat_data = {
        "user_message": sentence,
        "bot_reply": bot_reply,
        "timestamp": datetime.utcnow()
    }
    chat_collection.insert_one(chat_data)

    return jsonify({"answer": bot_reply})

# ----------------- Helper Functions -----------------

def get_news():
    try:
        url = "https://www.hindustantimes.com/latest-news"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        headlines = soup.select("div.media-heading > h3")
        return [headline.get_text(strip=True) for headline in headlines[:5]]
    except Exception as e:
        print(f"Error fetching news: {e}")
        return ["Sorry, I couldn't fetch the news right now."]

def get_weather(city="delhi"):
    try:
        API_KEY = "9ec9285debec43badb135f04d9b7ceaf48c9f9cd4be63a36fa5f6b9444119e0f"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        r = requests.get(url)
        data = r.json()
        temp = data["main"]["temp"]
        condition = data["weather"][0]["description"]
        return f"The temperature in {city.title()} is {temp}°C with {condition}."
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return "Sorry, I couldn't fetch the weather info."

def get_joke():
    try:
        r = requests.get("https://official-joke-api.appspot.com/random_joke")
        data = r.json()
        return f"{data['setup']} ... {data['punchline']}"
    except Exception as e:
        print(f"Error fetching joke: {e}")
        return "Couldn't fetch a joke at the moment."

def google_search(query):
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": "9ec9285debec43badb135f04d9b7ceaf48c9f9cd4be63a36fa5f6b9444119e0f",
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        if "answer_box" in results:
            answer_box = results["answer_box"]
            return answer_box.get("answer") or answer_box.get("snippet", "")

        if "organic_results" in results:
            first = results["organic_results"][0]
            title = first.get("title", "")
            link = first.get("link", "")
            snippet = first.get("snippet", "")
            return f"{title}\n{link}\n{snippet}"

        return "Sorry, I couldn't find anything."
    except Exception as e:
        print("Google Search Error:", e)
        return "Sorry, I couldn't perform a live search."

# ----------------- Main -----------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)


