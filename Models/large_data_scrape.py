import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import time
from threading import Thread, Event
import pandas as pd
from typing import List
import datetime


def get_date_range_for_season(year):
    switcher = {
        2020: ["october-2019", "november", "december", "january", "february", "march", "july", "august", "september", "october-2020"],
        2019: pd.date_range('2018-11-08', '2019-3-31'),
        2018: pd.date_range('2017-11-08', '2018-3-31'),
        2017: pd.date_range('2016-11-08', '2017-3-31'),
        2016: pd.date_range('2015-11-08', '2016-3-31'),
        2015: pd.date_range('2014-11-08', '2015-3-31'),
        2014: pd.date_range('2013-11-01', '2014-3-31'), # bad year no data on jan-31-2013 for some reason
        2013: pd.date_range('2012-11-08', '2013-3-31'),
        2012: pd.date_range('2012-1-01', '2012-3-31'), # bad year no data in november/december :(
        2011: pd.date_range('2010-11-08', '2011-3-31'), # bad year
        2010: pd.date_range('2009-11-08', '2010-3-31') # bad year 
    }
    return switcher.get(year, "out of range... range is 2010-2020")


class DataHolder():
    def __init__(self, stat_url_endpoints):
        self.stat_dict = {}
        self.endpoints = stat_url_endpoints
        self.keys = []

    def updateKeys(self):
        self.keys = [key for key in self.stat_dict.keys()]


def scrape_column(response, col: int):
    # changed to '3' to get the 'last 3 games data' on the website
    teams = [team.text for team in BeautifulSoup(response.text, 'html.parser').find_all('td', class_='text-left nowrap')]
    data = [row.find_all('td')[col].text for row in BeautifulSoup(response.text, 'html.parser').find_all('tr')[1:]]
    zip_list = list(zip(*[teams, data]))
    zip_list.sort()
    teams_list, data_list = zip(*zip_list)
    if '%' in data_list[0]: # handles the percent symbol in certain data points
        data_list = [float(x[0:-1]) for x in data_list]
    else:
        data_list = [float(x) for x in data_list]
    # data_array.append([[date for i in range(30)], list(zip(*[teams, pts]))])
    return teams_list, data_list

def scrape_stat_data(url, daterange, column:int):
    print(f"going to {url}, for col: {column}, starting at: {daterange[0].date()}")
    data_array = []
    for date in daterange:
        if date == pd.Timestamp('2013-12-31'): # skip this date there is no data on the website...
            continue
        print(date.date())
        response = requests.get(url + date.strftime("%Y-%m-%d"))
        # col = 2 means season stat, col = 3 means last 3 stats, cols = 4 means last 1 stats, col = 5 means home stats, col = 6 means away stats
        try:
            teams_list, data_list = scrape_column(response, column)
        except ValueError as e:
            print(f'Value Error for {date.date()} {url}')
            continue
        data_array.append([[date for i in range(30)], teams_list, data_list])
    
    return data_array


def send_scrape_threads(DHolder: DataHolder, years, columns: List[int]):
    dateRanges = [get_date_range_for_season(year) for year in years if year not in [2010, 2011, 2012, 2014]] # 2012 and 2014 are werid data years
    numDateRanges = len(dateRanges)
    for r in dateRanges:
        print(r)
    print(numDateRanges)
    # numEndpoints = len(endpoints)
    # with concurrent.futures.ThreadPoolExecutor(max_workers=numEndpoints) as executor:
    #     executor.map(send_threads_for_columms, DHolder.endpoints, [columns]*numEndpoints, [dateRanges]*numEndpoints, [DHolder]*numEndpoints)
    for endpoint in DHolder.endpoints:
        t0 = time.time()
        for col in columns:
            url = f"https://www.teamrankings.com/nba/stat/{endpoint}?date="
            data_list = []
            # ppg threads
            with concurrent.futures.ThreadPoolExecutor(max_workers=numDateRanges) as executor:
                results = executor.map(scrape_stat_data, [url]*numDateRanges, dateRanges, [col]*numDateRanges)
            for val in results:
                print(f"val: {val[0]} \n")  
                data_list += val
                # print(val[0])
            key = get_column_name(endpoint, col)
            DHolder.stat_dict[key] = data_list
            # DHolder.print()
            # print(f"this took {round(t1-t0,2)} seconds USING {numDateRanges} WORKERS!!!.")
        t1 = time.time()
        print(f"It took {round(t1-t0,2)} seconds to parse cols {columns} for {endpoint}.")

def get_column_name(endpoint, column):
    if column == 2:
        return f'{endpoint}-SeasonSoFar'
    elif column == 3:
        return f'{endpoint}-Last3'
    elif column == 5:
        return f'{endpoint}-Home'
    elif column == 6:
        return f'{endpoint}-Away'

def get_team_data(startYear: int, endYear: int, endpoints: List[str], columns:List[int]):
    DHolder = DataHolder(endpoints)
    years = [x + startYear for x in range(endYear-startYear)]
    print(years)
    # print(years) # loops over different stats
    send_scrape_threads(DHolder, years, columns)
    
    DHolder.updateKeys()
    keys = DHolder.keys
    first_key = next(iter(DHolder.stat_dict)) # first key in dict
    number_of_days = len(DHolder.stat_dict[first_key])
    print(f'keys {keys}')
    date_index, team_index =  [], []
    for i in range(number_of_days):
        date_index += DHolder.stat_dict[keys[0]][i][0]
        team_index += DHolder.stat_dict[keys[0]][i][1]
    # get DHolder.stat_dict ready to be made into a data frame
    # turn the original list into a long list that holds JUST the data for that endpoint. It will be in the proper order since the teams were sorted (see zipping) in scrape_stat_data. By doing this we will bea able to make a dataframa out of Dholder.stat_dict.
    for key in keys:
        data_list = []
        for j in range (number_of_days):
            data_list += DHolder.stat_dict[key][j][2] # this j is important 
        DHolder.stat_dict[key] = data_list # replace list containing team and date info with only the stat list(datalist)

    DF =  pd.DataFrame(data=DHolder.stat_dict, index=[date_index, team_index])
    return DF

if __name__=='__main__':
    endpoints = [
                #  'effective-field-goal-pct', 'true-shooting-percentage', 'shooting-pct',
                #  'opponent-effective-field-goal-pct', 'opponent-true-shooting-percentage', 'opponent-shooting-pct',

                #  'free-throw-pct', 'free-throws-made-per-game', 'fta-per-fga', 'free-throw-rate',
                #  'opponent-free-throw-pct', 'opponent-free-throws-made-per-game', 'opponent-fta-per-fga', 'opponent-free-throw-rate',

                #  'assists-per-game', 'assists-per-possession', 'assists-per-fgm', 'assist--per--turnover-ratio',
                #  'opponent-assists-per-game', 'opponent-assists-per-possession', 'opponent-assists-per-fgm', 'opponent-assist--per--turnover-ratio',

                #  'turnovers-per-possession', 'turnover-pct',
                #  'opponent-turnovers-per-possession', 'opponent-turnover-pct',

                 'offensive-efficiency',
                 'defensive-efficiency',

                 'points-per-game', '3rd-quarter-points-per-game', '4th-quarter-points-per-game', 'average-scoring-margin',
                 'opponent-points-per-game', 'opponent-3rd-quarter-points-per-game', 'opponent-4th-quarter-points-per-game', 'opponent-average-scoring-margin',

                 'total-rebounds-per-game', 'offensive-rebounding-pct', 'defensive-rebounding-pct', 'total-rebounding-percentage',
                 'opponent-total-rebounds-per-game', 'opponent-offensive-rebounding-pct', 'opponent-defensive-rebounding-pct', 'opponent-steals-per-game', 
                 
                 'win-pct-all-games', 'average-biggest-lead', 'fastbreak-efficiency',
                 'opponent-win-pct-all-games', 'opponent-average-biggest-lead', 'opponent-fastbreak-efficiency'
                ]
    print(f'len endpoints: {len(endpoints)}')
    t0 = time.time()
    # col = 2 means season stat, col = 3 means last 3 stats, cols = 4 means last 1 stats, col = 5 means home stats, col = 6 means away stats 2, 3, 5, 6
    DF = get_team_data(2015, 2020, endpoints, columns=[2, 3, 5, 6]) # 2015
    t1 = time.time()
    secs = t1-t0
    time_taken = str(datetime.timedelta(seconds=secs))
    print(f"The time for {len(endpoints)} endpoints was {time_taken}")
    DF.to_pickle('data_df_2015-2020-second-24-endpoints-4-cols.pickle')