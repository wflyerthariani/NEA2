#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 10:13:09 2020

@author: arman
"""


from bs4 import BeautifulSoup
import requests
import json
def get_imagelink(isbn):
    URL = "https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn
    r = requests.get(URL)
    soup = BeautifulSoup(r.content, 'html5lib')
    json_data = soup.html.text.strip()
    parser = json.loads(json_data)
    return str(parser['items'][0]['volumeInfo']['imageLinks']['thumbnail'])
    
print(get_imagelink('0590426850'))
