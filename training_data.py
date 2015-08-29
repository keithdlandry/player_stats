#training_data.py

import pandas as pd
import numpy as np
import read_player_stats
from sklearn import linear_model
from sklearn import svm
from sklearn import grid_search
from sklearn import preprocessing
from sklearn import cluster
from sklearn import cross_validation

def make_total_data(seasons=range(2004,2015),pages=[0,1], pos='rb'):
	total_df = None
	for season in seasons:
		for page in pages:
			df = read_player_stats.read_stats(season, week=0,page=page,pos=pos, scoring='PPR')
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
				df = read_player_stats.read_stats(season, week=week,page=page,pos=pos, scoring='PPR')
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

def ff_projection(most_rec_df, model, normalize=False):
	#project based on most recent data
	X_proj = np.array(most_rec_df.drop('Name', axis=1))
	if normalize:
		X_proj = preprocessing.scale(X_proj)
	y_proj = model.predict(X_proj)
	
	return y_proj

def sort_and_reindex(df, col):
	df = df.sort(columns=col, ascending=False)
	df.index = range(1, len(df)+1)
	return df

def cluster_players(df, n_clusters=3):
	X_Cluster = np.array(df.drop(['Name', 'FFPPG'], axis=1))
	X_Cluster = preprocessing.scale(X_Cluster)

	kmean_model = cluster.KMeans(n_clusters=n_clusters)
	y_clusters = kmean_model.fit_predict(X_Cluster)

	df['Cluster'] = y_clusters

	group_df = [df[df.Cluster == clust] for clust in range(n_clusters)]

	for i, group_element in enumerate(group_df):
		group_element['FFPPG'].hist(bins=50)
		print('Group ' + str(i))
		print('mean: ' + str(np.mean(group_element['FFPPG'])))
		print('std: ' + str(np.std(group_element['FFPPG'])))

	return group_df, kmean_model

def train_player_model(training_df):
	X_train = np.array(training_df.drop(['Name','FFPPG'], axis=1))
	y_train = np.array(training_df['FFPPG'])

	parameters = {'alpha': np.logspace(-5,5,num=30)}
	lin_model = grid_search.GridSearchCV(linear_model.Ridge(normalize=True), parameters, cv=10)
	lin_model.fit(X_train, y_train)

	return lin_model.best_estimator_

def train_svm_model(training_df, verbose=False):
	#train SVM
	X_train = np.array(training_df.drop(['Name','FFPPG'], axis=1))
	y_train = np.array(training_df['FFPPG'])

	X_scaled = preprocessing.scale(X_train)

	best_score = 9999
	best_params = {}

	#grid search to optimize parameters of SVM
	C_list = np.logspace(-5,2,num=11)
	gamma_list = np.logspace(-3,1,num=11)
	epsilon_list = [.1]
	for c_test in C_list:
		for gamma_test in gamma_list:
			for epsilon_test in epsilon_list:
				svm_model = svm.SVR(kernel='rbf', C=c_test, gamma=gamma_test, epsilon=epsilon_test)
				scores = cross_validation.cross_val_score(svm_model, X_scaled, y_train, cv=5, scoring='mean_absolute_error')
				mean_score = np.mean(scores)
				if verbose:
					print('params: ' + str(svm_model.get_params()))
					print(mean_score)
				if abs(mean_score) < abs(best_score):
					best_score = mean_score
					best_params = svm_model.get_params()

	print('***Best Params***')
	print(best_params)
	print('Score:' + str(best_score))

	#return a trained SVM with the best parameters we found
	ret_svm = svm.SVR()
	ret_svm.set_params(**best_params)
	ret_svm.fit(X_scaled, y_train)
	return ret_svm