# read the @main.py file and add a text input box for the user to input the context as a paragraph, then it goes to the deepseek AI model to configure that context paragraph given by   │
# │   the user into the safe_topics list as saved in the json file. the actual text paragraph is saved in the @userData.json file as well to load it back when the settings page is opened,  │
# │   also use caching into a json file to reduce costs from the API


from operator import is_
import os
import time
import string
from datetime import datetime
import json

os.system("pip install pywin32 pyautogui pywinauto keyboard yt-dlp requests beautifulsoup4")

import pyautogui
from pywinauto import Desktop
import keyboard
import sys
import argparse
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
from tkinter import messagebox

parser = argparse.ArgumentParser(description="Backend distraction detection.")
parser.add_argument("--model", type=str, default="Deepseek", help="The AI model to use for classification (e.g., 'Deepseek', 'Llama 3.1').")
args = parser.parse_args()
selected_model = args.model

print(f"Using AI model: {selected_model}")


# os.environ["CUDA_VISIBLE_DEVICES"] = "1"
# classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
CACHE_FILENAME = "classification_cache.json"

def load_hashmap_from_disk():
    """Loads the classification cache from a JSON file."""
    try:
        if os.path.exists(CACHE_FILENAME):
            with open(CACHE_FILENAME, 'r') as f:
                return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Could not load cache file '{CACHE_FILENAME}'. Starting fresh. Error: {e}")
    return {}

def save_hashmap_to_disk():
    """Saves the classification cache to a JSON file."""
    try:
        with open(CACHE_FILENAME, 'w') as f:
            json.dump(hashmap, f, indent=4)
    except IOError as e:
        print(f"Could not write to cache file '{CACHE_FILENAME}'. Error: {e}")

hashmap = load_hashmap_from_disk()
print(f"Loaded {len(hashmap)} items from cache.")


def get_current_datetime():
    return datetime.now().strftime("%d/%m/%y %H:%M:%S")

def search_youtube_video(title, max_results=10):
    try:
        encoded_title = urllib.parse.quote_plus(title)
        
        search_url = f"https://www.youtube.com/results?search_query={encoded_title}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        video_urls = []
        video_titles = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and '/watch?v=' in href:
                video_id = href.split('/watch?v=')[1].split('&')[0]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                video_title = link.get('title') or link.get_text(strip=True)
                
                if video_url not in video_urls and video_title:
                    video_urls.append(video_url)
                    video_titles.append(video_title)
                    
                    if len(video_urls) >= max_results:
                        break
        
        if not video_urls:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    video_id_matches = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', script.string)
                    title_matches = re.findall(r'"title":{"runs":\[{"text":"([^"]+)"}\]}', script.string)
                    
                    for i, video_id in enumerate(video_id_matches[:max_results]):
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        video_title = title_matches[i] if i < len(title_matches) else "Unknown Title"
                        
                        if video_url not in video_urls:
                            video_urls.append(video_url)
                            video_titles.append(video_title)
        
        if not video_urls:
            return None
        
        try:
            for i in range(0, max_results):
                if video_titles[i] == title:
                    return video_urls[i], video_titles[i]
        except Exception as _:
            pass

        return video_urls[0], video_titles[0]
        
    except requests.exceptions.RequestException as e:
        print(f"A network error occurred: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
LLAMA_API_KEY = os.environ.get("LLAMA_API_KEY", "YOUR_LLAMA_API_KEY")
LLAMA_API_URL = "https://api.groq.com/openai/v1/chat/completions" # Example for Groq

def is_distracting(title: str, user_context: list, model: str) -> bool:
    labels = ["Distracting", "Not Distracting"]
    
    if title in hashmap:
        cached_result = hashmap.get(title)
        if cached_result and 'labels' in cached_result and 'Distracting' in cached_result['labels']:
             return cached_result

    prompt = f'''
The user is a student and is interested in videos about {user_context}.
Based on the user's interests, classify the following video title: "{title}"
The categories are: {labels}.
Your response must be a valid JSON object with two keys: "labels" and "scores".
- "labels" must be a list of the categories provided, sorted by their score in descending order.
- "scores" must be a corresponding list of confidence scores (between 0 and 1).
The scores should sum to 1.
Only return the JSON object, with no other text or explanations.
'''

    if model == "Deepseek":
        api_url = DEEPSEEK_API_URL
        api_key = DEEPSEEK_API_KEY
        model_name = "deepseek-chat"
    elif model == "Llama 3.1":
        print("Using Llama 3.1 model via Groq API.")
        api_url = LLAMA_API_URL
        api_key = LLAMA_API_KEY
        model_name = "llama3-8b-8192" # Groq model name for Llama3 8b
        
        if api_key == "YOUR_LLAMA_API_KEY":
            print("WARNING: LLAMA_API_KEY is not set. Using placeholder value.")
        else:
            print(f"Using LLAMA_API_KEY starting with: {api_key[:4]}...")
        
        print(f"API URL: {api_url}")
        print(f"Model Name: {model_name}")
    else:
        print(f"Model '{model}' is not supported by this backend.")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are an expert text classifier. Your response is only a valid JSON object."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=20)
        print(f"API Response Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"API Error Response: {response.text}")
        response.raise_for_status()
        
        api_response = response.json()
        json_response_str = api_response.get('choices', [{}])[0].get('message', {}).get('content')
        
        if not json_response_str:
            print(f"{model} API returned an empty response.")
            return None

        result = json.loads(json_response_str)
        
        if 'labels' in result and 'scores' in result and isinstance(result['labels'], list) and isinstance(result['scores'], list):
            hashmap[title] = result
            save_hashmap_to_disk()
            return result
        else:
            print(f"{model} API response is not in the expected format.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred with the {model} API request: {e}")
        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Failed to parse {model} API response: {e}")
        if 'response' in locals():
            print(f"Raw response: {response.text}")
        return None

def wins():
    windows = Desktop(backend="uia").windows()
    return [w.window_text() for w in windows]

# def search_youtube(query):
#     ydl_opts = {"quiet": True, "noplaylist": True}
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(f"ytsearch1:{query}", download=False)
#         if "entries" in info and len(info["entries"]) > 0:
#             video = info["entries"][0]
#             return video["webpage_url"]
#     return None

def get_video_description(video_url):
    """
    Extract the description of a YouTube video from its URL using web scraping.
    
    Args:
        video_url (str): The YouTube video URL
        
    Returns:
        str: The video description, or None if not found
    """
    try:
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Make the request to the video page
        response = requests.get(video_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Method 1: Look for description in meta tags
        # print(1)
        # description_meta = soup.find('meta', {'name': 'description'})
        # if description_meta and description_meta.get('content'):
        #     return description_meta.get('content').strip()
        
        # Method 2: Look for description in script tags (YouTube stores data here)
        # print(2)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for description in various JSON patterns
                description_patterns = [
                    r'"description":"([^"]+)"',
                    r'"shortDescription":"([^"]+)"',
                    r'"description":{"simpleText":"([^"]+)"}',
                    r'"description":{"runs":\[{"text":"([^"]+)"}\]}',
                ]
                
                for pattern in description_patterns:
                    matches = re.findall(pattern, script.string)
                    if matches:
                        # Clean up the description
                        description = matches[0]
                        # Decode HTML entities
                        description = description.replace('\\"', '"').replace('\\n', '\n').replace('\\/', '/')
                        # Remove excessive whitespace
                        description = re.sub(r'\s+', ' ', description).strip()
                        if len(description) > 50:  # Ensure it's a meaningful description
                            return description
        
        # Method 3: Look for description in specific div elements
        # print(3)
        # description_divs = soup.find_all('div', {'id': 'description'})
        # for div in description_divs:
        #     text_content = div.get_text(strip=True)
        #     if text_content and len(text_content) > 50:
        #         return text_content
        
        # # Method 4: Look for description in expandable content
        # print(4)
        # expandable_content = soup.find_all('div', class_=re.compile(r'.*expandable.*'))
        # for content in expandable_content:
        #     text_content = content.get_text(strip=True)
        #     if text_content and len(text_content) > 50:
        #         return text_content
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"A network error occurred while fetching description: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while extracting description: {e}")
        return None

# while True:
#     windows = wins()
#     for title in windows:
#         if not title.strip():
#             continue
#         if 'youtube' in title.lower():
#             title = ' '.join(title.split(' ')[1:-4])
#             try:
#                 syv = search_youtube_video(title)
#                 if syv != None:
#                     url, title_searched = syv
#                 print(url, title_searched, title)
#                 if title_searched == title:
#                     try:
#                         description = get_video_description(url)
#                         res = is_distracting(f"{title}\n{description}")
#                     except Exception as e2:
#                         print("Couldn't fetch the description!")
#                         res = is_distracting(title)
#                 else:
#                     res = is_distracting(title)
#             except Exception as e:
#                 print("Couldn't fetch the URL!")
#                 res = is_distracting(title)

#             try:
#                 print(f"\n{res}\n")
#                 distracting = res["labels"][0]
#                 if not (res["scores"][res["labels"].index("Education")] > 0.2 or res["scores"][res["labels"].index("Programming")] > 0.2):
#                     print(f"\nDistracting window detected: {title}")
#                     try:
#                         pass
#                         # w = pyautogui.getWindowsWithTitle(title)[0]
#                         # w.activate()
#                     except Exception as e:
#                         print(f"\nError while focusing on {title}: {e}")
#                     print(f"\nClosing: {title}")
#                     # keyboard.press_and_release('ctrl+w')
#                 else:
#                     print(f"\nSafe window: {title}")
#                     pass
#             except Exception as e:
#                 print(f"\nError while the process {title}: {e}")

#     time.sleep(5)

def remove_links(text):
    updated_text = []
    for i in text.split(' '):
        if not 'http' in i:
            updated_text.append(i)
    return ' '.join(updated_text)


distracting_titles = [
    # Video Streaming
    "Netflix",
    "Prime Video",
    "JioHotstar",
    "Hulu",
    "Crunchyroll",
    "Twitch",

    # Social Media
    "Instagram",
    "Snapchat",
    "Facebook",
    "X. It’s what’s happening / X",
    "Threads",
    "Reddit",
    "Pinterest",
    "TikTok",
    "BeReal.",

    # Gaming Platforms
    "Welcome to Steam",
    "Epic Games Store | Download & Play PC Games, Mods, DLCs",
    "Roblox",
    "Riot Games",
    "Discord | Your Place to Talk and Hang Out",
    "Battle.net",
    "Xbox Official Site",
    "PlayStation® Official Site",

    # Chat & Meme Sites
    "9GAG: Go Fun The World",
    "Quora - A place to share knowledge and better understand the world",
    "Tumblr",
    "Imgur: The magic of the Internet",
    "Telegram Messenger",
    "WhatsApp Web",

    # Shopping
    "Online Shopping site in India: Shop Online for Mobiles, Books, Watches, Shoes and More - Amazon.in",
    "Online Shopping Site for Mobiles, Electronics, Furniture, Grocery, Lifestyle, Books & More. Best Offers!",
    "Online Shopping for Women, Men, Kids Fashion & Lifestyle - Myntra",
    "Meesho: Online Shopping Site for Fashion, Electronics, Home & More",
    "Online Shopping for Men, Women & Kids Fashion - AJIO",
    "AliExpress - Online Shopping for Popular Electronics, Fashion, Home & Garden",

    # Clickbait / News
    "BuzzFeed",
    "Home | Daily Mail Online",
    "TMZ"
]

hash_links = {}

hash_desc = {}

try:
    with open("userData.json", "r") as f:
        data = json.load(f)
    backendActive = data["backendActive"]
except PermissionError as e:
    time.sleep(5)
except OSError as e1:
    time.sleep(5)
except Exception as e2:
    print(f'Error: {e2}')


while backendActive == True:
# while True:
    try:
        with open("userData.json", "r") as f:
            data = json.load(f)
        backendActive = data["backendActive"]
        safe_topics = data.get("safe_topics", ["Education", "Technology", "Programming"])
    except PermissionError as e:
        time.sleep(5)
    except OSError as e1:
        time.sleep(5)
    except Exception as e2:
        print(f'Error: {e2}')

    for t in wins():
        for i in distracting_titles:
            if i.lower() in t.lower():
                print(f'Title: {t}\n\n\n')
                print(f'Distracting window detected: {t}')
                try:
                    with open('distractionHistory.json', 'r') as f:
                        data = json.load(f)
                        data["Distractions"].append([t, get_current_datetime()])
                    with open('distractionHistory.json', 'w') as f:
                        json.dump(data, f, indent=4)
                except Exception as e:
                    print("Fatal Error: JSON file loading or dumping couldn't work. Rewriting the JSON file to its default.")
                    with open('distractionHistory.json', 'w') as f:
                        json.dump({"Distractions":[[t, get_current_datetime()]]}, f, indent=4)
                print(f'Focusing: {t}')
                with open("userData.json", 'r') as f:
                    intervention = json.load(f)["Intervention Style"]
                if intervention == 'auto-close':
                    try:
                        pyautogui.getWindowsWithTitle(t)[0].activate()
                        print(f'Successfully focused on: {t}')
                    except Exception as e:
                        print(f'Couldn\'t focus on: {t}')
                    print(f'Closing: {t}')
                    try:
                        keyboard.press_and_release('ctrl+w')
                        print(f'Successfully closed: {t}\n\n\n')
                    except Exception as e:
                        print(f"Couldn't close: {t}\n\n\n")
                else:
                    messagebox.showinfo("Information", "Distracting Window detected!!!")
        description = ''
        # browser based youtube tab closing
        title = t
        if 'Google Chrome' == title.split(' - ')[-1] or 'Opera' == title.split(' - ')[-1]:
            if 'YouTube' == title.split(' - ')[-2]:
                # handle the case where the title is like this: (1) Title - Youtube - Google Chrome
                t1 = time.time()
                title_tf = False;
                try:
                    if title.split(' ')[0][0] == '(' and title.split(' ')[0][-1] == ')':
                        title = ' '.join(' - '.join(title.split(' - ')[0:-2]).split(' ')[1::])
                    else:
                        title = ' - '.join(title.split(' - ')[0:-2])
                    print(f'Title: {title}')
                    title_tf = True;
                except Exception as e:
                    print(f'Error: {e}')

                if not t in wins():
                    break

                if not title in hashmap:
                    url_tf = False;
                    try:
                        if not title in hash_links:
                            url, title_searched = search_youtube_video(title)
                            hash_links[title] = (url, title_searched)
                        else:
                            url, title_searched = hash_links[title]
                        if not url == None:
                            url_tf = True;
                            print(f'URL: {url}')
                    except Exception as e:
                        print(f'Error: {e}')

                    if not t in wins():
                        break

                    desc_tf = False;
                    try:
                        if not url in hash_desc:
                            description = get_video_description(url)
                            hash_desc[url] = description
                        else:
                            description = hash_desc[url]
                        if not description == None:
                            desc_tf = True
                            print(f'Description: {description}')
                    except Exception as e:
                        print(f'Error: {e}')
                else:
                    description = 'Hello World!'

                if not t in wins():
                    break

                letters = list(string.ascii_letters)
                digits = list(string.digits)
                special_characters = list(string.punctuation)
                all_characters = letters + digits + special_characters + [' ']
                

                is_dist_tf = False;
                try:
                    if title_tf and url_tf and desc_tf:
                        if not f"{title}" in hashmap:
                            d = ''
                            for char in description:
                                if (char in all_characters):
                                    d = d + char

                            d = remove_links(d)

                            if len(d) > 251:
                                description = d[0:250]
                            is_dist = is_distracting(f"{title}\n{description}", safe_topics, selected_model)
                            hashmap[f"{title}"] = is_dist
                        else:
                            is_dist = hashmap[f"{title}"]
                        is_dist_tf = True;
                    elif title_tf and url_tf:
                        if not title in hashmap:
                            is_dist = is_distracting(title, safe_topics, selected_model)
                            hashmap[title] = is_dist
                        else:
                            is_dist = hashmap[title]
                        is_dist_tf = True;
                    elif title_tf:
                        if not title in hashmap:
                            is_dist = is_distracting(title, safe_topics, selected_model)
                            hashmap[title] = is_dist
                        else:
                            is_dist = hashmap[title]
                        is_dist_tf = True;
                except Exception as e:
                    print(f'Error: {e}')

                try:
                    print(f'{is_dist}')
                except Exception as e:
                    print(e)

                print(time.time() - t1)

                print('\n\n\n')

                try:
                    distracting_score = is_dist['scores'][is_dist['labels'].index('Distracting')]
                    if distracting_score > 0.7:
                        if is_dist_tf and t in wins():
                            print(f'Distracting window detected: {t}')
                            try:
                                with open('distractionHistory.json', 'r') as f:
                                    data = json.load(f)
                                    data["Distractions"].append([t, get_current_datetime()])
                                with open('distractionHistory.json', 'w') as f:
                                    json.dump(data, f, indent=4)
                            except Exception as e:
                                print("Fatal Error: JSON file loading or dumping couldn't work. Rewriting the JSON file to its default.")
                                with open('distractionHistory.json', 'w') as f:
                                    json.dump({"Distractions":[[t, get_current_datetime()]]}, f, indent=4)
                            print(f'Focusing: {t}')
                            with open("userData.json", 'r') as f:
                                intervention = json.load(f)["Intervention Style"]
                            if intervention == 'auto-close':
                                try:
                                    pyautogui.getWindowsWithTitle(t)[0].activate()
                                    print(f'Successfully focused on: {t}')
                                except Exception as e:
                                    print(f'Couldn\'t focus on: {t}')
                                print(f'Closing: {t}')
                                try:
                                    keyboard.press_and_release('ctrl+w')
                                    print(f'Successfully closed: {t}\n\n\n')
                                except Exception as e:
                                    print(f"Couldn't close: {t}\n\n\n")
                            else:
                                messagebox.showinfo("Information", "Distracting Window detected!!!")
                    else:
                        print(f'Safe window: {title}\n\n\n')
                except Exception as e:
                    print(f'Error: {e}')

        if 'Microsoft​ Edge' == title.split(' - ')[-1].replace('\200b', ''):
            if 'YouTube' in title.split(' - ')[-3]:
                # handle the case where the title is like this: (1) Title - Youtube - Personal - Microsoft Edge
                t1 = time.time()
                title_tf = False;
                try:
                    if title.split(' ')[0][0] == '(' and title.split(' ')[0][-1] == ')':
                        title = ' '.join(' - '.join(title.split(' - ')[0:-3]).split(' ')[1::])
                    else:
                        title = ' - '.join(title.split(' - ')[0:-3])
                    print(f'Title: {title}')
                    title_tf = True;
                except Exception as e:
                    print(f'Error: {e}')

                if not t in wins():
                    break

                if not title in hashmap:
                    url_tf = False;
                    try:
                        if not title in hash_links:
                            url, title_searched = search_youtube_video(title)
                            hash_links[title] = (url, title_searched)
                        else:
                            url, title_searched = hash_links[title]
                        if not url == None:
                            url_tf = True;
                            print(f'URL: {url}')
                    except Exception as e:
                        print(f'Error: {e}')

                    if not t in wins():
                        break

                    desc_tf = False;
                    try:
                        if not url in hash_desc:
                            description = get_video_description(url)
                            hash_desc[url] = description
                        else:
                            description = hash_desc[url]
                        if not description == None:
                            desc_tf = True
                            print(f'Description: {description}')
                    except Exception as e:
                        print(f'Error: {e}')
                else:
                    description = 'Hello World!'

                if not t in wins():
                    break

                letters = list(string.ascii_letters)
                digits = list(string.digits)
                special_characters = list(string.punctuation)
                all_characters = letters + digits + special_characters + [' ']
                

                is_dist_tf = False;
                try:
                    if title_tf and url_tf and desc_tf:
                        if not f"{title}" in hashmap:
                            d = ''
                            for char in description:
                                if (char in all_characters):
                                    d = d + char

                            d = remove_links(d)

                            if len(d) > 251:
                                description = d[0:250]
                            is_dist = is_distracting(f"{title}\n{description}", safe_topics, selected_model)
                            hashmap[f"{title}"] = is_dist
                        else:
                            is_dist = hashmap[f"{title}"]
                        is_dist_tf = True;
                    elif title_tf and url_tf:
                        if not title in hashmap:
                            is_dist = is_distracting(title, safe_topics, selected_model)
                            hashmap[title] = is_dist
                        else:
                            is_dist = hashmap[title]
                        is_dist_tf = True;
                    elif title_tf:
                        if not title in hashmap:
                            is_dist = is_distracting(title, safe_topics, selected_model)
                            hashmap[title] = is_dist
                        else:
                            is_dist = hashmap[title]
                        is_dist_tf = True;
                except Exception as e:
                    print(f'Error: {e}')

                try:
                    print(f'{is_dist}')
                except Exception as e:
                    print(e)

                print(time.time() - t1)

                print('\n\n\n')

                try:
                    distracting_score = is_dist['scores'][is_dist['labels'].index('Distracting')]
                    if distracting_score > 0.7:
                        if is_dist_tf and t in wins():
                            print(f'Distracting window detected: {t}')
                            try:
                                with open('distractionHistory.json', 'r') as f:
                                    data = json.load(f)
                                    data["Distractions"].append([t, get_current_datetime()])
                                with open('distractionHistory.json', 'w') as f:
                                    json.dump(data, f, indent=4)
                            except Exception as e:
                                print("Fatal Error: JSON file loading or dumping couldn't work. Rewriting the JSON file to its default.")
                                with open('distractionHistory.json', 'w') as f:
                                    json.dump({"Distractions":[[t, get_current_datetime()]]}, f, indent=4)
                            print(f'Focusing: {t}')
                            with open("userData.json", 'r') as f:
                                intervention = json.load(f)["Intervention Style"]
                            if intervention == 'auto-close':
                                try:
                                    pyautogui.getWindowsWithTitle(t)[0].activate()
                                    print(f'Successfully focused on: {t}')
                                except Exception as e:
                                    print(f'Couldn\'t focus on: {t}')
                                print(f'Closing: {t}')
                                try:
                                    keyboard.press_and_release('ctrl+w')
                                    print(f'Successfully closed: {t}\n\n\n')
                                except Exception as e:
                                    print(f"Couldn't close: {t}\n\n\n")
                            else:
                                messagebox.showinfo("Information", "Distracting Window detected!!!")
                    else:
                        print(f'Safe window: {title}\n\n\n')
                except Exception as e:
                    print(f'Error: {e}')



                
    time.sleep(0.25)
