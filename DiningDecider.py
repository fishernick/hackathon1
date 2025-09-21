# develop and train dish-recognizing model
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib

# for web scraping
import requests
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
dish_train, dish_temp, origin_train, origin_temp = train_test_split(dish, origin, test_size=0.3, random_state=25, stratify=origin)
dish_val, dish_test, origin_val, origin_test = train_test_split(dish_temp, origin_temp, test_size=0.5, random_state=25, stratify=None)

# vectorize
vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words='english')
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

# === Step 2: Ask user for food preference ===
print("What cuisine are you in the mood for? (e.g. American, Korean, Mexican, etc.)")
user_cuisine = input("Your choice: ").strip().lower()

# === Step 3: Setup dining courts and headers ===
dining_courts = ["Earhart", "Ford", "Hillenbrand", "Wiley", "Windsor"]
today = datetime.today()
year, month, day = today.year, today.month, today.day
meal = "Dinner"

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/5",
    "host":	"dining.purdue.edu",
    "connection":	"keep-alive",
    "sec-ch-ua-platform":	"\"Windows\"",
    "k":	"application/json; charset=UTF-8",
    "sec-ch-ua":	"\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
    "content-type":	"text/plain;charset=UTF-8",
    "sec-ch-ua-mobile":	"?0",
    "accept":	"*/*",
    "origin":"https://dining.purdue.edu",
    "sec-fetch-site":"same-origin",
    "sec-fetch-mode":"cors",
    "sec-fetch-dest":"empty",
    "referer":"https://dining.purdue.edu/menus/",
    "accept-encoding":	"gzip",
    "accept-language":	"en-US,en;q=0.9"
    }

# === Step 4: Functions to scrape dishes ===
def get_dish_links(dining_court):
    url = f"https://dining.purdue.edu/menus/{dining_court}/{year}/{month}/{day}/{meal}"
    try:
        res = requests.get(url, headers=headers, verify=certifi.where())
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        item_links = soup.select('a[href^="/menus/item/"]')
        return ["https://dining.purdue.edu" + a['href'] for a in item_links]
    except Exception as e:
        print(f"Error loading menu for {dining_court}: {e}")
        return []

def get_dish_name_from_item_page(item_url):
    try:
        res = requests.get(item_url, headers=headers, verify=certifi.where())
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        name_tag = soup.find("span", class_="item-widget-name__name")
        return name_tag.get_text(strip=True) if name_tag else None
    except:
        return None

# === Step 5: Scrape all menus and classify ===
court_dishes = defaultdict(list)

for court in dining_courts:
    print(f"\n Scraping menu: {court} ({meal})")
    
    item_links = get_dish_links(court)
    print(f"   Found {len(item_links)} dish item links.")

    if not item_links:
        print(f"   No item links found for {court}. Skipping.")
        continue

    for idx, link in enumerate(item_links):
        print(f"     ({idx+1}/{len(item_links)}) Fetching item page: {link}")
        
        dish_name = get_dish_name_from_item_page(link)
        
        if dish_name:
            print(f"        Got dish name: {dish_name}")
            # Predict cuisine
            vec = vectorizer.transform([dish_name])
            predicted_cuisine = model.predict(vec)[0].lower()
            print(f"        Predicted cuisine: {predicted_cuisine}")
            court_dishes[court].append((dish_name, predicted_cuisine))
        else:
            print(f"        Failed to extract dish name from: {link}")


# === Step 6: Score each dining court ===
court_scores = {
    court: sum(1 for _, cuisine in dishes if cuisine == user_cuisine)
    for court, dishes in court_dishes.items()
}

# === Step 7: Recommend dining court ===
if any(score > 0 for score in court_scores.values()):
    best_court = max(court_scores, key=court_scores.get)
    print(f"\nBest match: {best_court} Dining Court")
    print(f"Matching {user_cuisine.title()} dishes there:")
    for dish_name, cuisine in court_dishes[best_court]:
        if cuisine == user_cuisine:
            print(f"  • {dish_name}")
else:
    print("\n⚠️ Sorry, none of the dining courts are serving your preferred cuisine right now.")
