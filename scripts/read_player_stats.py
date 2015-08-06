import pandas as pd
import numpy as np
from lxml.html import parse
from urllib2 import urlopen
import re

#function for parsing
def rb_stats(season, page=0):
    #read in RB stats for given season from fftoday.com
    rb_column_names = ['Name', 'Team', 'Games', 'RunAtt', 'RunYards', 'RunTD', 'Targets', 'Rec', 'RecYards', 'RecTD', 'FFP', 'FFPPG']
    url_str = 'http://fftoday.com/stats/playerstats.php?Season=%d&GameWeek=&PosID=20&LeagueID=1&order_by=FFPts&sort_order=DESC&cur_page=%d' % (season, page)
    
    #parse html and find the main data table
    parsed = parse(urlopen(url_str))
    page = parsed.getroot()
    tables = page.findall('.//table')
    #get the rows of the player table
    main_table = tables[10]
    rows = main_table.findall('.//tr')
    
    #dataframe we will return
    rb_df = pd.DataFrame(columns=rb_column_names)
    for i,row in enumerate(rows[2:]): #rows[2] is first player entry
        elements = row.findall('.//td') #find all elements in the row
        values = [val.text_content() for val in elements] #make a list of all the values from the row
        rb_df.loc[i] = values
        
    #clean up entries
    rb_df['Name'] = rb_df['Name'].str.replace('[^a-z]', '',flags=re.IGNORECASE) #remove extra stuff from name cell
    rb_df['RunYards'] = rb_df['RunYards'].str.replace(',', '') #remove thousands commas
    rb_df['RecYards'] = rb_df['RecYards'].str.replace(',', '')
    #add season column
    rb_df['Season'] = season
    rb_df[['Games', 'RunAtt', 'RunYards', 'RunTD', 'Targets', 'Rec', 'RecYards', 'RecTD', 'FFP', 'FFPPG']] = rb_df[[ 'Games', 'RunAtt', 'RunYards', 'RunTD', 'Targets', 'Rec', 'RecYards', 'RecTD', 'FFP', 'FFPPG']].astype(float)

    return rb_df