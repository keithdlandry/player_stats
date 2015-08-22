import pandas as pd
import numpy as np
from lxml.html import parse
from urllib2 import urlopen
import re

#function for parsing
def season_stats(season, page=0, pos='rb'):
    posid_dict = {'rb': 20, 'wr': 30}
    posid = posid_dict[pos]
    #read in RB stats for given season from fftoday.com
    rb_column_names = ['Name', 'Team', 'Games', 'RunAtt', 'RunYards', 'RunTD', 'Targets', 'Rec', 'RecYards', 'RecTD', 'FFP', 'FFPPG']
    wr_column_names = ['Name', 'Team', 'Games', 'Targets', 'Rec', 'RecYards', 'RecTD', 'RunAtt', 'RunYards', 'RunTD', 'FFP', 'FFPPG']
    column_dict = {'rb': rb_column_names, 'wr': wr_column_names}
    column_names = column_dict[pos]
    url_str = 'http://fftoday.com/stats/playerstats.php?Season=%d&GameWeek=&PosID=%d&LeagueID=1&order_by=FFPts&sort_order=DESC&cur_page=%d' % (season, posid, page)
    
    #parse html and find the main data table
    parsed = parse(urlopen(url_str))
    page = parsed.getroot()
    tables = page.findall('.//table')
    #get the rows of the player table
    main_table = tables[10]
    rows = main_table.findall('.//tr')
    
    #dataframe we will return
    seasons_data_df = pd.DataFrame(columns=column_names)
    for i,row in enumerate(rows[2:]): #rows[2] is first player entry
        elements = row.findall('.//td') #find all elements in the row
        values = [val.text_content() for val in elements] #make a list of all the values from the row
        seasons_data_df.loc[i] = values
        
    #clean up entries
    seasons_data_df['Name'] = seasons_data_df['Name'].str.replace('[^a-z]', '',flags=re.IGNORECASE) #remove extra stuff from name cell
    seasons_data_df['RunYards'] = seasons_data_df['RunYards'].str.replace(',', '') #remove thousands commas
    seasons_data_df['RecYards'] = seasons_data_df['RecYards'].str.replace(',', '')
    #add season column
    seasons_data_df['Season'] = season
    seasons_data_df[seasons_data_df.drop(['Name', 'Team'], axis=1).columns] = seasons_data_df[seasons_data_df.drop(['Name', 'Team'], axis=1).columns].astype(float)

    return seasons_data_df