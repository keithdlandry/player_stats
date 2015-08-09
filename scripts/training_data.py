#training_data.py

import pandas as pd
import numpy as np
import read_player_stats

def make_total_data(seasons=range(2004,2015),pages=[0,1]):
	total_df = None
	for season in seasons:
		for page in pages:
			df = read_player_stats.rb_stats(season,page)
			if total_df is None:
				total_df = df
			else:
				total_df = total_df.append(df, ignore_index = True)
			
	total_df.sort_index(by=['Name','Season'], inplace=True)
	return total_df

def merge_seasons(df_season1, df_season2):
	df_dropped1 = df_season1.drop(['Season', 'Team'], axis=1)
	df_dropped2 = df_season2.drop(['Season', 'Team'], axis=1)
	
	merged = pd.merge(df_dropped1,df_dropped2, on='Name', how='outer', suffixes=('_1', '_2'))
	return merged

def make_training_df(total_df, seasons=range(2004,2014), ppg=False):
	training_data_df = None
	for season in seasons[:-1]:
		df1 = total_df[total_df.Season == season]
		df2 = total_df[total_df.Season == season+1]
		label_df = total_df[total_df.Season == season+2]
		if ppg:
			labeled = pd.merge(merge_seasons(df1, df2), label_df[['Name','FFPPG']], on='Name')
		else:
			labeled = pd.merge(merge_seasons(df1, df2), label_df[['Name','FFP']], on='Name')
		if training_data_df is None:
			training_data_df = labeled
		else:
			training_data_df = training_data_df.append(labeled, ignore_index=True)
		
	training_data_nadropped = training_data_df.dropna() #dont train on missing seasons
	return training_data_nadropped