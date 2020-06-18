import os
import time
import random

import requests
import re
import json

from bs4 import BeautifulSoup
import argparse

headers = {
    'Accept': '*/*',
    'Authorization': 'www.dek-d.com',
    'Accept-encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'cache-control': 'no-cache',
    'referer':'https://www.dek-d.com/home/writer/'
}
    
class DekDScraper():
    def __init__(self, path, delay):
        self.path = path
        self.delay = delay
        
        self.params = {
            "_by":"filter",
            "offset":"0",
            "abstract":"",
            "advance-search":"0",
            "category":"0",
            "is_end":"0",
            "keyword":"",
            "not_abstract":"",
            "not_story_name":"",
            "not_writer_name":"",
            "story_name":"",
            "story_type":"0",
            "writer_name":"",
            "sort_by":"1",
            "nexttime":"i_warn_u"
        }
        
        self.scraped_id_list = list()
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        else:
            self.scraped_id_list = [p[:-5] for p in os.listdir(self.path) if p.endswith('.json')]
            
        resp = requests.get('https://www.dek-d.com/homepage/ajax/writer_query?', params=self.params, headers=headers)
        json_data = json.loads(str(resp.text)[9:])
        self.total_noval = json_data['total']
        
        
    def get_data(self):
        i=0
        while(i<self.total_noval):
            resp = requests.get('https://www.dek-d.com/homepage/ajax/writer_query?', params=self.params, headers=headers)
            json_data = json.loads(str(resp.text)[9:])
            noval_list = json_data['o']['list']

            status_code = resp.status_code
            if status_code != 200:
                print("Error get data from api : " + resp.url)
                continue
            
            for noval in noval_list:
                self.data = {
                    'novel_id':'',
                    'title':'',
                    'writer':'',
                    'text':'',
                }
                
                try :
                    noval_id = noval['id']
                    writer = noval['writer']
                    title = noval['title']
                    n_chapter = noval['chapter']
                    username = noval['username']
                    
                    if str(noval_id) in self.scraped_id_list:
                        continue
                    
                    print("scrape novel name : "+title+", novel id : "+str(noval_id))
                    text = self.get_novel(noval_id, username, int(n_chapter))
                    
                    if len(text) > 0:
                        w_file = open(os.path.join(self.path, str(noval_id)+'.json'), 'w+')
                        
                        self.data['novel_id'] = noval_id
                        self.data['writer'] = writer
                        self.data['text'] = text
                        self.data['title'] = title
                        
                        json.dump(self.data, w_file, ensure_ascii=False)
                        w_file.close()
                
                except Exception as e :
                    continue
                
                    
                i+=1
                
            self.params['offset'] = str(int(self.params['offset'])+30)
    
    def get_novel(self, novel_id, username, n_chapter):
        all_text = ''
        
        for c in range(1,n_chapter+1):
            chapter_resp = requests.get('https://writer.dek-d.com/'+username+'/story/viewlongc.php?id='+str(novel_id)+'&chapter='+str(c), headers=headers)
            status_code = chapter_resp.status_code
            if status_code != 200:
                print("Error get page : " + chapter_resp.url)
                continue
            soup = BeautifulSoup(chapter_resp.content, 'html.parser')
            content_div = soup.find('div',{'id':'story-content'})
            if content_div == None:
                continue
            for t in content_div.findAll('p'):
                _text = t.text.strip()
                _text = re.sub('<[^>]*>', '', _text)
                _text = re.sub('\\xa0|"', '', _text)
                _text = re.sub("-|”|\*|#|:|\)|\(|!|'|\]|\[", '', _text)
                _text = re.sub("\!", '', _text)
                _text = re.sub("’", '', _text)
                _text = re.sub("“", '', _text)

                all_text=all_text+'\n'+_text.strip()
                time.sleep(self.delay)
                
        return all_text
                
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Scrape text from www.dek-d.com")
    parser.add_argument("--path", type=str, default="data")
    parser.add_argument("--sleep", type=int, default=1)
    args = parser.parse_args()
    
    scraper = DekDScraper(args.path, args.sleep)
    print("start scrape")
    scraper.get_data()
    
    