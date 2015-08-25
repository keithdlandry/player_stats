#training_data.py

import pandas as pd
import numpy as np
import read_player_stats
from sklearn import linear_model
from sklearn import grid_search

def make_total_data(seasons=range(2004,2015),pages=[0,1], pos='rb'):
	total_df = None
	for season in seasons:
		for page in pages:
			df = read_player_stats.read_stats(season, week=0,page=page,pos=pos)
			if total_df is None:
				total_df = df
			else:
				total_df = total_df.append(df, ignore_index = True)
			
	total_df.sort_index(by=['Name','Season'], inplace=True)
	return total_df

def make_total_game_data(seasons=range(2004,2015), weeks=range(1,18),pages=[0,1], pos='rb'):
	total_df = None
	for season in seasons:
		for week in weeks:
			for page in pages:
				df = read_player_stats.read_stats(season, week=week,page=page,pos=pos)
				if total_df is None:
					total_df = df
				else:
					total_df = total_df.append(df, ignore_index = True)

	total_df.sort_index(by=['Name','Season', 'Week'], inplace=True)
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

def data_for_projection(total_df, season=2015):
	most_rec_df = merge_seasons(total_df[total_df.Season == season-2], total_df[total_df.Season == season-1])
	most_rec_df.dropna(inplace=True)
	return most_rec_df

def ff_projection(most_rec_df, model):
	#project based on most recent data
	X_proj = np.array(most_rec_df.drop('Name', axis=1))
	y_proj = model.predict(X_proj)

	#player names and newest projections sorted descending
	most_rec_df['2015 Projection'] = y_proj
	most_rec_df = most_rec_df[['Name', '2015 Projection']].sort(columns='2015 Projection', ascending=False)
	most_rec_df.index = range(1, len(most_rec_df)+1)
	return most_rec_df

def train_player_model(training_df):
	X_train = np.array(training_df.drop(['Name','FFPPG'], axis=1))
	y_train = np.array(training_df['FFPPG'])

	parameters = {'alpha': np.logspace(-5,5,num=30)}
	lin_model = grid_search.GridSearchCV(linear_model.Ridge(normalize=True), parameters, cv=10)
	lin_model.fit(X_train, y_train)

	return lin_model.best_estimator_