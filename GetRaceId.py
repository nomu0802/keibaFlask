import pandas as pd
import numpy as np
import datetime
from tqdm.notebook import tqdm

import requests
from bs4 import BeautifulSoup
import time
import re
import json
from bs4 import BeautifulSoup
from urllib import request






class GetRaceId:
   def scrape(days):
    race_id_list = []
    url = 'https://db.netkeiba.com/race/list/' + days
    response = request.urlopen(url)
    soup = BeautifulSoup(response, features="html.parser")
    response.close()
    found = soup.find_all('dl', class_='race_top_hold_list')
    
    foundlist = found[1].find_all('dl', class_='race_top_data_info fc')
    for  index in foundlist:
        link = index.find('a').get('href')
        race_id_list.append(link[6:18])
    return race_id_list
    

   
