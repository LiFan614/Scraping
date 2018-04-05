import requests
from requests.exceptions import RequestException
from multiprocessing import Pool
import re
import json

def get_one_page(url,headers):
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None

def parse_page(html):
    pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?img data-src="(.*?)".*?title.*?>(.*?)</a>.*?"star">(.*?)</p>.*?'
                         +'"releasetime">(.*?)</p>.*?"integer">(.*?)</i>.*?"fraction">(.*?)</i>.*?</dd>',re.S)
    items = re.findall(pattern,html)
    for item in items:
        yield {
            'rank':   item[0],
            'name':   item[2],
            'image':  item[1],
            'actors': item[3].strip()[3:],
            'time':   item[4].strip()[5:],
            'rating': item[5]+item[6]
        }

def write_to_file(content):
    with open('result.txt','a',encoding = 'utf-8') as f:
        f.write(json.dumps(content,ensure_ascii=False) + '\n')
        f.close()

def main(offset):
    headers = {'user-agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}
    url = 'https://maoyan.com/board/4?offset='+str(offset)
    html = get_one_page(url,headers)
    for item in parse_page(html):
        print(item)
        write_to_file(item)


if __name__ == '__main__':
    pool = Pool()
    pool.map(main,[i*10 for i in range(10)])
