import requests
from urllib.parse import urlencode
from requests.exceptions import RequestException
import json
from bs4 import BeautifulSoup
import re
from config import *
import pymongo
from json.decoder import JSONDecodeError
import os
from hashlib import md5
from multiprocessing import Pool



client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

def get_page_index(offset,keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': '1',
        'from': 'search_tab'
    }
    url = 'https://www.toutiao.com/search_content/?'+urlencode(data)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('Request Failed')
        return None

def parse_page_index(html):
    try:
        data = json.loads(html)
        if data and 'data' in data.keys():
            for item in data.get('data'):
                yield item.get('article_url')
    except JSONDecodeError:
        pass

def download_image(url):
    print('Downloading', url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except ConnectionError:
        return None

def save_image(content):
    file_path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    print(file_path)
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()


def get_page_detail(url):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    }
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException as e:
        # print('Request Details Failed')
        return None

def parse_page_detail(html,url):
    soup = BeautifulSoup(html,'lxml')
    title_html = soup.select('title')
    result_lst = []
    if len(title_html) > 0:
        title = title_html[0].get_text()
        images_pattern = re.compile('&quot;http://(.*?)&quot;',re.S)
        result = re.findall(images_pattern,html)

        if len(result) == 0:
            images_pattern =  re.compile('gallery: JSON.parse\("(.*?)"\),',re.S)
            search_result = re.search(images_pattern, html)
            if search_result:
                data = json.loads(search_result.group(1).replace('\\',''))
                if data and 'sub_images' in data.keys():
                    sub_images = data.get('sub_images')
                    result_lst = [item.get('url') for item in sub_images]
        else:
            result_lst = ['http://' + item for item in result]

        for image in result_lst: download_image(image)
        return {
            'title': title,
            'url': url,
            'images': result_lst
        }

def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('Save to Mongo DB successfully!', result)
        return True
    return False


def main(offset):
    html = get_page_index(offset,'美女')
    for url in parse_page_index(html):
        if url:
            html = get_page_detail(url)
            if html:
                result = parse_page_detail(html,url)
                if len(result['images']) != 0:
                    save_to_mongo(result)


if __name__ == '__main__':
    pool = Pool()
    groups = ([x * 20 for x in range(GROUP_START, GROUP_END + 1)])
    pool.map(main, groups)
    pool.close()
    pool.join()