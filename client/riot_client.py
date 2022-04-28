import requests
import os
import pandas as pd
import numpy as np
import json

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
	response = requests.get(api_name + puuid + "/ids?start=" + str(start) + "&count=" + str(count) + "&api_key=" + dev_key)
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