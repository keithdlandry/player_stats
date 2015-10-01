import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import re
import sys
import training_data
import game_by_game

def weekly_pred(season=2015, week=4):
	positions = ['qb', 'rb', 'wr', 'te']
	df_list = [pd.read_csv('../game_stats/'+ pos +'_game_stats.csv') for pos in positions]
	df_list = [df.drop(['Unnamed: 0'], axis = 1) for df in df_list]

	tdata_list = [game_by_game.gbg_train_stats(df) for df in df_list]
	orig = {'Season': 2004, 'Week': 1}
	curr_week = 17*(season - orig['Season']) + (week - orig['Week'])
	test_samples = [df[(df.Label == -1) & (df.WeekID_0 > curr_week-5)] for df in tdata_list]
	train_samples = [df[df.Label != -1] for df in tdata_list]

	week_labels = ['WeekID_%d' % i for i in range(20)]
	test_samples = [df.drop(week_labels, axis=1) for df in test_samples]
	train_samples = [df.drop(week_labels + ['Name'], axis=1) for df in train_samples]

	y_train = [df['Label'] for df in train_samples]
	X_train = [np.array(df.drop(['Label'], axis=1)) for df in train_samples]
	rfr = [RandomForestRegressor(n_estimators=200) for i in range(4)]
	for i in range(4):
		rfr[i].fit(X_train[i], y_train[i])
	preds = [rfr[i].predict(np.array(test_samples[i].drop(['Label', 'Name'], axis=1))) for i in range(4)]

	proj_list = []
	for i in range(4):
		test_samples[i]['Projection'] = preds[i]
		pro_df = test_samples[i][['Name', 'Projection']]
		proj_list.append(pro_df.sort(columns=['Projection'], ascending=False))

	#remove players by hand
	proj_list[2].drop(['JordyNelson', 'JoshGordon'], inplace=True)

	positions = ['QB', 'RB', 'WR', 'TE']
	pos_salaries = []
	for pos in positions:
		pos_salaries.append(pd.read_csv('../salaries/by_position/' + pos + '_W' + str(week) + '_2015.csv'))

	week_table = []
	for proj, sal in zip(proj_list, pos_salaries):
		week_table.append(pd.merge(proj, sal, on='Name'))

	for table in week_table:
		table['DPP'] = table['Salary']/table['Projection']

	week_table = [table.drop(['Unnamed: 0'], axis=1) for table in week_table]
	for pos, table in zip(positions,week_table):
		table.to_csv('../projections/weekly/2015_w' + str(week) + '/' + pos + '_proj_and_sal.csv')

	return week_table

def FD_salaries(week=1, filename):
	salaries = pd.read_csv(filename)
	salaries['Name'] = salaries['First Name'] + salaries['Last Name']
	salaries['Name'] = salaries['Name'].str.replace('[^a-z]', '',flags=re.IGNORECASE)
	salaries = FD_salaries[['Name', 'Salary', 'Position']]
	
	positions = ['QB', 'RB', 'WR', 'TE']
	position_salaries = [FD_salaries[FD_salaries.Position == pos] for pos in positions]
	position_salaries[0]

	for i,pos in enumerate(positions):
		position_salaries[i].to_csv('../salaries/by_position/' + pos + '_W' + str(week) + '_2015.csv')

	return

if __name__ == '__main__':
	weekly_pred()