import requests
import os
import pandas as pd
import numpy as np
import random
import json
import os.path
import time

#checks if riot_api_key exists in environment variables
if ("riot_api_key" not in os.environ):
	raise Exception("Riot API key does not exist. Please set a key as riot_api_key = your_key in environment variables")
else:
	dev_key = os.environ["riot_api_key"]

def get_player_ids(summoner_name):
	"""
	Get player ids by summoner name
	"""
	api_name = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/"
	response = requests.get(api_name + summoner_name + "?api_key=" + dev_key)
	return response.json()


def get_puuid(summoner_name):
	"""
	Get puuid by summoner name
	"""
	api_name = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/"
	response = requests.get(api_name + summoner_name + "?api_key=" + dev_key)
	return response.json().get("puuid")


def get_summoner_name(puuid):
	"""
	Get a summoner name by puuid, like XmEmjOPvqoEUkkgks49W3gYvvumXWcibTYtuSYHgDGSL_w85_ZzwsOPZKtLABf-YiRK2bNNai-2IrA
	"""
	api_name = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/"
	response = requests.get(api_name + puuid + "?api_key=" + dev_key)
	data = response.json()
	return data.get("name")


def get_match_ids(puuid, start = 0, count = 20):
	"""
	Get match history by puuid, returns a list of match IDs
	"""
	api_name = "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/"
	response = requests.get(api_name + puuid + "/ids?type=normal&start=" + str(start) + "&count=" + str(count) + "&api_key=" + dev_key)
	return response.json()


def get_rune_info():
	"""
	pull rune data
	"""
	api_name = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perks.json"
	response = requests.get(api_name)
	data = response.json()
	df = pd.DataFrame.from_dict(data)
	df.to_csv("./runes_info.csv", index = False)


def get_summoner_spells():
	"""
	pull summoner spell data
	"""
	api_name = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/summoner-spells.json"
	response = requests.get(api_name)
	data = response.json()
	df = pd.DataFrame.from_dict(data)
	df.to_csv("./summoner_spells_info.csv", index = False)


def concatenate(df, df_new):
	"""
	simplify concatenation syntax
	"""
	return pd.concat([df, df_new])


def get_match(match_id):
	"""
	gets information for a match by match id
	"""
	api_name = "https://americas.api.riotgames.com/lol/match/v5/matches/"
	response = requests.get(api_name + str(match_id) + "?api_key=" + dev_key)
	data = response.json()

	# df = pd.DataFrame.from_dict(data.get("info").get("participants"))
	df = pd.json_normalize(data, record_path = ['info', 'participants'], meta = [['metadata', 'gameMode']])

	# is_good_data = True
	#checks if game is ARAM
	if df["metadata.gameMode"][0] != "ARAM":
		return

	#checks if there is data for all 10 participants, maybe not necessary, only exception was one random non-aram game
	# expected_ids = [1,2,3,4,5,6,7,8,9,10]
	# for i in expected_ids:
	# 	if i not in df["participantId"]:
	# 		is_good_data = False

	#Perks (runes) are in a nested JSON format. I normalize the data using a defined path and then reshape for joining
	df_perks = pd.json_normalize(data, record_path = ['info', 'participants', 'perks', 'styles', 'selections'])
	df_perks = df_perks["perk"]
	df_perks = pd.DataFrame(df_perks.values.reshape(-1, 6), columns=['perk1','perk2','perk3','perk4','perk5', 'perk6'])

	df["matchId"] = match_id
	return df.join(df_perks)


def get_all_champions_ids(patch_version):
	"""
	Fetches IDs for all champions within a given patch version.
	"""
	response = requests.get("http://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json".format(patch_version)).json()
	return [champ_data['key'] for champ_data in response['data'].values()]


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

			#Grab new puuid
			r = random.randint(1, 10)
			chosen_col = df["p" + str(r) + "_puuid"].tolist()
			df.to_csv(input_csv, index = False)
			puuid = random.choice(chosen_col)

		except: #if getting match fails, grab an entirely new puuid
			r = random.randint(1, 10)
			chosen_col = df["p" + str(r) + "_puuid"].tolist()
			df.to_csv(input_csv, index = False)
			puuid = random.choice(chosen_col)
			continue		

	df.to_csv(input_csv, index = False)

# while True:
# 	df_open = pd.read_csv("test.csv")
# 	puuid_picker = random.choice(df_open["p" + str(random.randint(1, 10)) + "_puuid"].tolist())
# 	match_crawler("test.csv", puuid_picker, 20)
# 	print("Pull successful.")
# 	time.sleep(120)
# 	df_all.to_csv("./match_" + str(match_count) + ".csv", index = False)
#test pull recuset