# develop and train dish-recognizing model
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib

# for web scraping
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict
import ssl
import certifi

ssl_context = ssl.create_default_context(cafile=certifi.where())

# load data
food_dataset = pd.read_csv('Receipes from around the world.csv', encoding='latin1')

# clean up data
food_dataset.dropna(subset=['recipe_name', 'cuisine'], inplace=True)

counts = food_dataset['cuisine'].value_counts()
valid_classes = counts[counts >= 2].index
food_dataset = food_dataset[food_dataset['cuisine'].isin(valid_classes)]

# features & labels
dish = food_dataset['recipe_name']
origin = food_dataset['cuisine']

# split dataset (train + validation + test)
dish_train, dish_temp, origin_train, origin_temp = train_test_split(dish, origin, test_size=0.3, random_state=25,
                                                                    stratify=origin)
dish_val, dish_test, origin_val, origin_test = train_test_split(dish_temp, origin_temp, test_size=0.5, random_state=25,
                                                                stratify=None)

# vectorize
vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
dish_train_vec = vectorizer.fit_transform(dish_train)

# transform validation and test sets
dish_val_vec = vectorizer.transform(dish_val)
dish_test_vec = vectorizer.transform(dish_test)

# train model
clf = LogisticRegression(max_iter=1000)
clf.fit(dish_train_vec, origin_train)

# evaluate validation set
origin_val_pred = clf.predict(dish_val_vec)
print("Validation set results:")
print(classification_report(origin_val, origin_val_pred))

# evaluate test set
origin_test_pred = clf.predict(dish_test_vec)
print("Test set results:")
print(classification_report(origin_test, origin_test_pred))

# save model and vectorizer
joblib.dump(clf, 'cuisine_model.joblib')
joblib.dump(vectorizer, 'vectorizer.joblib')

# load your trained model and vectorizer
clf = joblib.load('cuisine_model.joblib')
vectorizer = joblib.load('vectorizer.joblib')

# === Ask user for food preference ===
print("What cuisine are you in the mood for? (e.g. American, Korean, Mexican, etc.)")
user_cuisine = input("Your choice: ").strip().lower()

# === Setup dining courts and headers ===
dining_courts = ["Earhart", "Ford", "Hillenbrand", "Wiley", "Windsor"]
today = datetime.today()
year, month, day = today.year, today.month, today.day

headers = {

  "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.5999.115 Safari/537.36",
  "host": "dining.purdue.edu",
  "connection": "keep-alive",
  "accept": "application/json, text/javascript, */*; q=0.01",
  "accept-encoding": "gzip, deflate, br, zstd",
  "accept-language": "en-US,en;q=0.9",
  "origin": "https://dining.purdue.edu",
  "referer": "https://dining.purdue.edu/menus/",
  "sec-ch-ua": "\"Google Chrome\";v=\"140\", \"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\"",
  "sec-ch-ua-mobile": "?0",
  "sec-ch-ua-platform": "\"Windows\"",
  "sec-fetch-dest": "empty",
  "sec-fetch-mode": "cors",
  "sec-fetch-site": "same-origin",
  "x-requested-with": "XMLHttpRequest",
  "content-type": "application/json;charset=UTF-8"
}

dishes_list = [[], [], [], [], []]

# === Scrape dishes ===

today = datetime.today()
year, month, day = today.year, today.month, today.day

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    index = 0

    for court in dining_courts:
        url = f"https://dining.purdue.edu/menus/{court}/{year}/{month}/{day}"
        print(f"\nLoading {url} ...")
        page.goto(url)
        page.wait_for_selector(".station-item")  # wait for React content

        # Extract dish names
        dishes = page.locator(".station-item").all_inner_texts()
        print(f"{court} has {len(dishes)} dishes:")
        for d in dishes:
            # print("  •", d.strip())
            dishes_list[index].append(d)
        index += 1

    browser.close()

# === Predict genre of each dish ===

classified_predictions = []

for court_dishes in dishes_list:
    court_predictions = []
    for dish in court_dishes:
        dish_vec = vectorizer.transform([dish])
        predicted_cuisine = clf.predict(dish_vec)[0].lower()
        court_predictions.append(predicted_cuisine)
    classified_predictions.append(court_predictions)

    
# === Score each dining court ===

scores = {
    'EARHART': 0,
    'FORD': 0,
    'HILLENBRAND': 0,
    'WILEY': 0,
    'WINDSOR': 0
}

diner = 0

for court in classified_predictions:
    for genre in court:
        if (genre.lower() == user_cuisine.lower()):
            match diner:
                case 0:
                    scores['EARHART'] += 1
                case 1:
                    scores['FORD'] += 1
                case 2:
                    scores['HILLENBRAND'] += 1
                case 3:
                    scores['WILEY'] += 1
                case 4:
                    scores['WINDSOR'] += 1
    diner += 1

greatest_score_name = max(scores, key=scores.get)
print(f"The best dining court is {greatest_score_name}")
        

  
    
