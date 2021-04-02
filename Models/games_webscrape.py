#!/usr/bin/env python
# coding: utf-8

# In[74]:


import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import datetime
from datetime import datetime as DT
from typing import List, Dict
import torch
import time
import concurrent.futures

# In[76]:


# response = requests.get("https://www.basketball-reference.com/leagues/NBA_2020_games-october-2020.html")
# Soup = BeautifulSoup(response.text, 'html.parser')
# rows = Soup.find_all('tr')
# len(rows)
# for row in rows: 
#     print(row.th.text)
#     if row.th.text != "Date":
#         date_of_game = DT.strptime(row.th.text, '%a, %b %d, %Y')
#         print(date_of_game)


# In[77]:


def get_proper_name(teamName: str) -> str:
    issue_teams = ["Los Angeles Clippers", "Los Angeles Lakers", "Oklahoma City Thunder", "Portland Trail Blazers", "New Jersey Nets"]
    if teamName not in issue_teams:
        return teamName.rsplit(' ', 1)[0]
    else:
        if teamName == issue_teams[0]:
            return 'LA Clippers'
        elif teamName == issue_teams[1]:
            return 'LA Lakers'
        elif teamName == issue_teams[2]:
            return 'Okla City'
        elif teamName == issue_teams[3]:
            return 'Portland'
        elif teamName == issue_teams[4]:
            return 'Brooklyn'


# In[78]:


def get_months_in_season(year: int) -> List[str]:
    october_to_june = ["october", "november", "december", "january", "february", "march", "april", "may", "june"]
    november_to_june = ["november", "december", "january", "february", "march", "april", "may", "june"]
    switcher = {
        2020: ["october-2019", "november", "december", "january", "february", "march", "july", "august", "september", "october-2020"],
        2019: october_to_june,
        2018: october_to_june,
        2017: october_to_june,
        2016: october_to_june,
        2015: october_to_june,
        2014: october_to_june,
        2013: october_to_june,
        2012: ["december", "january", "february", "march", "april", "may", "june"],
        2011: october_to_june,
        2010: october_to_june,
        2009: october_to_june,
        2008: october_to_june,
        2007: october_to_june,
        2006: november_to_june,
        2005: november_to_june,
        2004: october_to_june,
        2003: october_to_june,
        2002: october_to_june,
        2001: october_to_june,
        2000: november_to_june,
        1999: ["february", "march", "april", "may", "june"],
        1998: october_to_june,
        1997: november_to_june,
        1996: november_to_june,
        1995: november_to_june,
        1994: november_to_june,
        1993: november_to_june,
        1992: november_to_june,
        1991: november_to_june,
        1990: november_to_june,
    }
    return switcher.get(year, "out of range... range is 1990-2020")


# In[79]:
class Game:
    def __init__(self, timestamp, homeTeam, awayTeam, didHomeWin):
        self.day = timestamp
        self.homeTeam = homeTeam
        self.awayTeam = awayTeam
        self.didHomeWin = didHomeWin
        
    def __repr__(self):
        return f"Time: {self.day}, Home Team: {self.homeTeam}, Away Team {self.awayTeam}, Home Team Won: {self.didHomeWin}"


# In[80]:
# Initialise lists to store scraped information
dates = []
awayTeams = []
homeTeams = []
homeWins = []
def _get_game_data(year):
    urls = [f"https://www.basketball-reference.com/leagues/NBA_{year}_games-{month}.html" for month in get_months_in_season(year)]
    # print(f"for {int_year} the urls are: \n {urls}")
    for url in urls[1:-3]: # slice off last three months and first month
        #print(url)
        response = requests.get(url)
        Soup = BeautifulSoup(response.text, 'html.parser')
        rows = Soup.find_all('tr')
        for row in rows:
            if row.th.text not in ["Date", "Playoffs"]: # these are sometiems the coloumn text values
                #print(url)
                rowElems = row.find_all('td')
                # rowElems[0] is the time of the game
                # added 'm' in f string because this is the format of rowElems[0] 7:00p. and date time needs pm or am not p or a
                # gameDay = DT.strptime(f"{row.th.text} {rowElems[0].text}m", '%a, %b %w, %Y %I:%M%p')
                
                # Get text vals and append them to their respective list
                # date
                try:
                    date_of_game = DT.strptime(row.th.text, '%a, %b %d, %Y')
                    dates.append(date_of_game)
                    # print(date_of_game)
                except ValueError as e:
                    print(row.th.text)
                    break
                if year <= 2000: # the format of the HTML is slightly differnt for years <= 2000
                    # away team
                    away = get_proper_name(rowElems[0].text)
                    awayTeams.append(away)
                    # home team
                    home = get_proper_name(rowElems[2].text)
                    homeTeams.append(home)
                    # Did Home team win?
                    awayPts = rowElems[1].text
                    homePts = rowElems[3].text

                    didHomeWin = int(homePts) > int(awayPts)
                    homeWins.append(didHomeWin)
                else:
                    # away team
                    away = get_proper_name(rowElems[1].text)
                    awayTeams.append(away)
                    # home team
                    home = get_proper_name(rowElems[3].text)
                    homeTeams.append(home)
                    # Did Home team win?
                    awayPts = rowElems[2].text
                    homePts = rowElems[4].text

                    didHomeWin = int(homePts) > int(awayPts)
                    homeWins.append(didHomeWin)
#In[]
MAX_THREADS = 30
# inclusize of startYear not inclusive on endYear

def scrape_game_data(startYear: int, endYear: int):
    # clear lists
    dates.clear()
    awayTeams.clear()
    homeTeams.clear()
    homeWins.clear()
    # turn start date and end date into a list of years 
    start_date = datetime.date(startYear, 1, 2)
    end_date = datetime.date(endYear, 1, 1)
    delta = datetime.timedelta(weeks=52, days=1)
    years = []
    while start_date <= end_date:
        years.append(start_date.year)
        # increment year            
        start_date += delta
    print(years)
    threads = min(MAX_THREADS, len(years))
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executer:
        result = executer.map(_get_game_data, years)
    # print(result[-1])
                     
    data = {
        'Date': dates,
        'Home': homeTeams,
        'Away': awayTeams,
        'DidHomeWin': homeWins,
    }
    DF = pd.DataFrame(data)
    # clear lists
    dates.clear()
    awayTeams.clear()
    homeTeams.clear()
    homeWins.clear()
    return DF
    
#In[81]:
t0 = time.time()
DF = scrape_game_data(2010, 2020)
t1 = time.time()
print(f"this took {round(t1-t0,2)} seconds.")

# %%
# %%