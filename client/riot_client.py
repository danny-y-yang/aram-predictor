import requests
import os
import pandas as pd
import numpy as np
import random
import json
import os.path
import time
import argparse

#checks if riot_api_key exists in environment variables
# if ("riot_api_key" not in os.environ):
# 	raise Exception("Riot API key does not exist. Please set a key as riot_api_key = your_key in environment variables")
# else:
# 	dev_key = os.environ["riot_api_key"]
parser = argparse.ArgumentParser()
parser.add_argument('--dev_key', type=str, help='Riot API key')
args = parser.parse_args()
dev_key = args.dev_key

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