#!/usr/bin/env python
# coding: utf-8
# In[3]:

import pandas as pdF
import numpy as np
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import time
from threading import Thread, Event
import pandas as pd
from typing import List

# In[]:
def get_date_range_for_season(year):
    switcher = {
        2020: ["october-2019", "november", "december", "january", "february", "march", "july", "august", "september", "october-2020"],
        2019: pd.date_range('2018-11-01', '2019-3-31'),
        2018: pd.date_range('2017-11-01', '2018-3-31'),
        2017: pd.date_range('2016-11-01', '2017-3-31'),
        2016: pd.date_range('2015-11-01', '2016-3-31'),
        2015: pd.date_range('2014-11-01', '2015-3-31'),
        2014: pd.date_range('2013-11-01', '2014-3-31'),
        2013: pd.date_range('2012-11-01', '2013-3-31'),
        2012: pd.date_range('2012-1-01', '2012-3-31'),
        2011: pd.date_range('2010-11-01', '2011-3-31'),
        2010: pd.date_range('2009-11-01', '2010-3-31'),
    }
    return switcher.get(year, "out of range... range is 2010-2020")

# In[43]:
class DataHolder():
    def __init__(self, stat_url_endpoints):
        self.stat_dict = {}
        self.keys = stat_url_endpoints
        for key in self.keys:
            self.stat_dict[key] = []

    def print(self):
        print(self.stat_dict)
    
    def getDataDict(self):
        return self.stat_dict
# In[]
#dates needed 
def scrape_stat_data(url, daterange):
    print(f"going to {url} starting at: {daterange[0].date()}")
    data_array = []
    for date in daterange:
        if date == pd.Timestamp('2013-12-31'): # skip this date there is no data on the website...
            continue
        response = requests.get(url + date.strftime("%Y-%m-%d"))
        pts = [row.find_all('td')[2].text for row in BeautifulSoup(response.text, 'html.parser').find_all('tr')[1:]]
        teams = [team.text for team in BeautifulSoup(response.text, 'html.parser').find_all('td', class_='text-left nowrap')]
        zip_list = list(zip(*[teams, pts]))
        zip_list.sort()
        print(date.date())
        try:
            teams_list, pts_list = zip(*zip_list)
            pts_list = list(np.float_(pts_list))
        except ValueError as e:
            print(date)
            print(f"Pts: {pts}")
            print(f"teams: {teams}")
        
        # data_array.append([[date for i in range(30)], list(zip(*[teams, pts]))])
        data_array.append([[date for i in range(30)], teams_list, pts_list])
    return data_array

# In[]
def send_scrape_threads(DHolder: DataHolder, years):
    dateRanges = [get_date_range_for_season(year) for year in years]
    print(dateRanges)
    numDateRanges = len(dateRanges)
    print(numDateRanges)
    for endpoint in DHolder.keys: 
        url = f"https://www.teamrankings.com/nba/stat/{endpoint}?date="
        data_list = []
        # ppg threads
        t0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=numDateRanges) as executor:
            results = executor.map(scrape_stat_data, [url]*numDateRanges, dateRanges)
        for val in results:    
            data_list += val
            # print(val[0])
        t1 = time.time()
        DHolder.stat_dict[endpoint] = data_list
        # DHolder.print()
        print(f"this took {round(t1-t0,2)} seconds USING {numDateRanges} WORKERS!!!.")
# In[52]:
# t0 = time.time()
# ppg_array = []
# ppg = scrape_stat_data(ppg_url, daterange, ppg_array)
# t1 = time.time()
# print(f"this took {round(t1-t0,2)} seconds.")
# ppg_array
# oppg = scrape_stat_data(oppg_url, daterange)

# # In[53]:
# count = 0
# for R in dateRanges:
#     count += len(R)
# print(count)
# In[59]:

# In[61]:
def get_team_data(startYear: int, endYear: int, endpoints: List[str]):
    DHolder = DataHolder(endpoints)
    years = [x + startYear for x in range(endYear-startYear)]
    # print(years) # loops over different stats
    send_scrape_threads(DHolder, years)
    
    keys = DHolder.keys
    number_of_days = len(DHolder.stat_dict[keys[0]])
    date_index, team_index =  [], []
    for i in range(number_of_days):
        date_index += DHolder.stat_dict[keys[0]][i][0]
        team_index += DHolder.stat_dict[keys[0]][i][1]
    # get DHolder.stat_dict ready to be made into a data frame
    for key in keys:
        data_list = []
        for j in range (number_of_days):
            data_list += DHolder.stat_dict[key][i][2]

        DHolder.stat_dict[key] = data_list # replace list containing team and date info with only the stat list(datalist)

    DF =  pd.DataFrame(data=DHolder.stat_dict, index=[date_index, team_index])
    return DF

# %%
endpoints = ['opponent-points-per-game', 'points-per-game']
DF = get_team_data(2015, 2020, endpoints) # 2015
DF
# In[]
DF['opponent-points-per-game'][0]
# %%
# yay = pd.date_range('2013-11-30', '2013-12-31')
# comparison = pd.Timestamp('2013-12-31')
# if comparison == yay[-1]:
#     print("we dont like this date")

# %%

# %%
