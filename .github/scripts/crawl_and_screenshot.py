import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

website_url = os.environ.get("WEBSITE_URL")
if not website_url:
    print("Error: WEBSITE_URL environment variable not set.")
    exit(1)

visited_urls = set()
urls_to_visit = [website_url]
sitemap_entries = []
screenshots_dir = "screenshots"
os.makedirs(screenshots_dir, exist_ok=True)

chrome_options = ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=ChromeService('/usr/bin/chromedriver'), options=chrome_options)

# Try to install ChromeDriver if not found
try:
    webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
except Exception as e:
    print(f"ChromeDriver not automatically installed: {e}")
    print("Assuming ChromeDriver is in /usr/bin/chromedriver")

while urls_to_visit:
    current_url = urls_to_visit.pop(0)
    if current_url in visited_urls:
        continue
    visited_urls.add(current_url)
    sitemap_entries.append(current_url)
    print(f"Crawling: {current_url}")

    try:
        response = requests.get(current_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Take screenshot
        try:
            driver.get(current_url)
            time.sleep(2) # Give the page time to load
            filename = os.path.join(screenshots_dir, current_url.replace("https://", "").replace("http://", "").replace("/", "_") + ".png")
            driver.save_screenshot(filename)
            print(f"Screenshot saved: {filename}")
        except Exception as e:
            print(f"Error taking screenshot of {current_url}: {e}")

        # Find all links on the page
        for link in soup.find_all('a', href=True):
            absolute_url = link['href']
            if absolute_url.startswith(website_url) and absolute_url not in visited_urls and absolute_url not in urls_to_visit:
                urls_to_visit.append(absolute_url)

    except requests.exceptions.RequestException as e:
        print(f"Error accessing {current_url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while processing {current_url}: {e}")

driver.quit()

# Create sitemap.txt
with open("sitemap.txt", "w") as f:
    for url in sitemap_entries:
        f.write(url + "\n")
print("sitemap.txt created.")
