import os
import argparse
import time
from io import BytesIO
from urllib.parse import urlparse

import requests
from PIL import Image
from lxml import html
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def get_article_data(article: str) -> tuple[str, str]:
    url = urlparse(article)
    assert all([url.scheme, url.netloc]), 'Article is not a valid URL :('

    resp = requests.get(article)
    assert 199 < resp.status_code < 300, f'Received a status code of {resp.status_code} :('

    tree = html.fromstring(resp.text)

    url = tree.xpath('//head/meta[@property="og:image"]/@content')
    if not url: raise Exception('No og:image found :(')

    title = tree.xpath('//head/title/text()')
    if not title: raise Exception('No title tag found :(')

    return url[0], title[0]


def choose_font_color(image_url: str) -> str:
    resp = requests.get(image_url)
    assert 199 < resp.status_code < 300, f'Received a status code of {resp.status_code} :('

    img = Image.open(BytesIO(resp.content))
    img_gray = img.convert('L')
    
    pixels = list(img_gray.getdata())
    num_pixels = len(pixels)
    avg_brightness = sum(pixels) / num_pixels
    
    if avg_brightness < 127:
        return "snow"
    else:
        return "black"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('article')
    args = parser.parse_args()

    og_image, title = get_article_data(args.article)
    print(f'{og_image = }\n{title = }\nGenerating image...')

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(2500, 3500)

    driver.get(f"file://{os.path.join(os.getcwd(), 'index.html')}")

    # Instantiate stuff
    driver.execute_script(f'setImages("{og_image}")')
    driver.execute_script(f'setFigCaption("{title.strip()}")')
    driver.execute_script(f'setFontColor("{choose_font_color(og_image)}")')

    time.sleep(2)

    # Take screenshot
    container = driver.find_element(By.ID, 'story-container')
    container.screenshot(f"images/article_story-[{'-'.join(title.lower().split())}].png")

    driver.quit()


if __name__ == '__main__':
    main()
