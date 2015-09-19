import pandas as pd
import numpy as np

def single_player(single_player_df):
    single_player_df = single_player_df.sort(columns='WeekID', ascending=False)
    single_player_df.reset_index(drop=True, inplace=True)
    arr = np.array(single_player_df.drop(['Name', 'Team', 'Games', 'Season', 'Week', 'FFPPG'], axis=1))
    tot_games,nfeat = arr.shape    
    windowlen = 20*nfeat
    flat = arr.flatten()
    
    label = np.array([-1])
    data_feat = np.concatenate([label, flat[:windowlen]], axis=1) 
        
    for i in range(tot_games - windowlen/nfeat + 1):
        if i==0: 
            continue
        index = i*nfeat
        if (index - 2) >= 0 :
            label = flat[index - 2]
        else:
            label = np.array([-1])
        row = np.hstack([label, flat[index:index+windowlen]])
        data_feat = np.vstack([data_feat, row])
        
    return data_feat

def gbg_train_stats(data_frame):
    #define all weeks relative to this value
	orig = {'Season': 2004, 'Week': 1}

    #remove players with fewer than 20 games recorded
	data_frame = data_frame.groupby('Name').filter(lambda x: len(x) > 20)
	data_frame['WeekID'] = 17*(data_frame['Season'] - orig['Season']) + (data_frame['Week'] - orig['Week'])

    #create column names for new dataframe
	stats_cols = data_frame.drop(['Name', 'Team', 'Games', 'Season', 'Week','FFPPG'], axis=1).columns
	game_stats_cols = []
	for i in range(20):
		game_stats_cols = game_stats_cols + [(col + '_' + str(i)) for col in stats_cols]

    #make examples for each player
	names = data_frame['Name'].unique()
	data_list = []
	for name in names:
		feat_arr = single_player(data_frame[data_frame.Name == name])
		feat_df = pd.DataFrame(feat_arr, columns=(['Label'] + game_stats_cols))
		feat_df['Name'] = name
		data_list.append(feat_df)

	stacked_data = pd.concat(data_list)
	return stacked_data

