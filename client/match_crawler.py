import requests
import os
import pandas as pd
import numpy as np
import random
import json
import os.path
import time
from riot_client import *
# import sys

def generate_match_data(summoner_name, match_count):
	"""
	Creates a csv of match data by summoner name. Future plan is to generate a bunch of match ids, then use that set of match ids as argument only
	"""
	matches_generated = []
	my_puuid = get_puuid(summoner_name)
	match_ids = get_match_ids(my_puuid, 0, match_count)
	df_all = pd.DataFrame()


	for match_id in match_ids:
		#Checks if the match has already been generated. We do not want to concatenate duplicate matches
		if match_id not in matches_generated:
			df_all = concatenate(df_all, get_match(match_id))
			matches_generated.append(match_id)

	#These are all the features we will need. Moving relevant columns to the front
	cols_to_move = [
		"matchId",
		"championId",
		"championName",
		"metadata.gameMode",
		"participantId",
		"perk1",
		"perk2",
		"perk3",
		"perk4",
		"perk5",
		"perk6",
		"perks.statPerks.offense",
		"perks.statPerks.flex",
		"perks.statPerks.defense",
		"puuid",
		"summoner1Id",
		"summoner2Id",
		"summonerId",
		"summonerLevel",
		"summonerName",
		"teamId",
		"win"
	]

	df_all = df_all[cols_to_move + [col for col in df_all.columns if col not in cols_to_move]]
	df_all.to_csv("./match_" + str(match_count) + ".csv", index = False)




def generate_match_line(match_id):
	"""
	returns a single line dataframe for a match by match id; returns empty if not ARAM game
	"""
	api_name = "https://americas.api.riotgames.com/lol/match/v5/matches/"
	response = requests.get(api_name + str(match_id) + "?api_key=" + dev_key)
	data = response.json()
	
	df = pd.json_normalize(data, record_path = ['info', 'participants'], meta = [['metadata', 'gameMode']])
	if df["metadata.gameMode"][0] != "ARAM":
		raise Exception("Not an ARAM game!")
	gameMode = df["metadata.gameMode"][0]
	cols_to_keep = [
		"championId",
		"championName",
		"participantId",
		"perks.statPerks.offense",
		"perks.statPerks.flex",
		"perks.statPerks.defense",
		"puuid",
		"summoner1Id",
		"summoner2Id",
		"summonerId",
		"summonerLevel",
		"summonerName",
		"teamId",
		"win"
	]
	df = df[cols_to_keep]
	data_headers = []
	for i in range(10):
		for j in range(14):
			data_headers.append("p" + str(i+1) + "_" + cols_to_keep[j])
	df = pd.DataFrame(df.values.reshape(-1, 140), columns = data_headers)

	#Generate perk data. df_perks.shape = (1, 60)
	df_perks = pd.json_normalize(data, record_path = ['info', 'participants', 'perks', 'styles', 'selections'])
	df_perks = df_perks["perk"]
	perk_headers = []
	for i in range(10):
		for j in range(6):
			perk_headers.append("p" + str(i+1) + "_perk" + str(j+1))
	df_perks = pd.DataFrame(df_perks.values.reshape(-1, 60), columns = perk_headers)

	df = df.join(df_perks)
	df["matchId"] = match_id
	df["gameMode"] = gameMode
	return df


# def match_crawler_without_csv(summoner_id):
# 	#summoner_name as input
# 	#assume no CSV
# 	#generate puuid
# 	#from summoner name grab riot api to get 1 match


def match_crawler(input_csv, starting_puuid, n):
	"""
	crawls n matches
	"""

	#Generate a set of recorded matches
	set_matchIds = set()
	df = pd.read_csv(input_csv)
	for i in df["matchId"]:
		set_matchIds.add(i)

	puuid = starting_puuid
	for i in range(n):
		df_temp = pd.DataFrame()
		matchId = ""
		try:
			r = random.randint(5, 10) #grab a random match
			matchId = get_match_ids(puuid, r, r)[0] #get the matchId for that random match]
			print(matchId)
			df_temp = generate_match_line(matchId)
			if matchId not in set_matchIds and df_temp["gameMode"][0] == "ARAM":
				df = concatenate(df, df_temp) 
			set_matchIds.add(matchId)
			df.to_csv(input_csv, index = False)

			#Grab new puuid
			r = random.randint(1, 10)
			chosen_col = df["p" + str(r) + "_puuid"].tolist()
			puuid = random.choice(chosen_col)

		except: #if getting match fails, grab an entirely new puuid
			r = random.randint(1, 10)
			chosen_col = df["p" + str(r) + "_puuid"].tolist()
			# df.to_csv(input_csv, index = False)
			puuid = random.choice(chosen_col)
			continue		

while True:
	df_open = pd.read_csv("training_dataset.csv")
	puuid_picker = random.choice(df_open["p" + str(random.randint(1, 10)) + "_puuid"].tolist())
	match_crawler("training_dataset.csv", puuid_picker, 20)
	print("Pull successful.")
	time.sleep(120)
