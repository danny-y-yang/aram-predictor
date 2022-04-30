import requests
import os
import pandas as pd
import numpy as np
import random
import json
import os.path
import time
import re
from df_utils import *


SUPPORTED_REGIONS = ['na1', 'euw1', 'kr1']
API_KEY_REGEX = r'RGAPI-[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}'
API_KEY_REGEX_COMPILED = re.compile(API_KEY_REGEX)


def validate(riot_request):
	"""
	Validates a request sent to riot servers. To use, annotate a function with @validate.
	"""
	def validate_params(*args, **kwargs):
		region = kwargs.get('region')
		if not region or region not in SUPPORTED_REGIONS:
			raise Exception(f"Invalid region {region} when calling {riot_request.__name__}")
		return riot_request(*args, **kwargs)
	return validate_params


@validate
def get_routing_value(region):
	if region in ['na1']:
		return 'americas'
	elif region in ['euw1']:
		return 'europe'
	elif region in ['kr1']:
		return 'asia'
	else:
		raise Exception(f"Routing value not found for region: {region}")


class RiotClient:
	def __init__(self, api_key):
		if not API_KEY_REGEX_COMPILED.match(api_key):
			raise Exception(f"API key provided: {api_key} does not match expected regex: {API_KEY_REGEX}")
		
		self.api_key = api_key

	def ping(self):
		print("hi")

	@validate
	def get_player_ids(self, region, summoner_name):
		"""
		Get player ids by summoner name
		"""
		return requests.get(f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={self.api_key}").json()


	@validate
	def get_puuid(self, region, summoner_name):
		"""
		Get puuid by summoner name
		"""
		print("fetching puuid")
		api_name = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={self.api_key}"
		print(api_name)
		puuid = requests.get(api_name).json().get("puuid")
		print(requests.get(api_name).json())
		if not puuid:
			raise Exception(f"Invalid puuid fetched using endpoint: {api_name}")
		return puuid

	@validate
	def get_summoner_name(self, region, puuid):
		"""
		Get a summoner name by puuid, like XmEmjOPvqoEUkkgks49W3gYvvumXWcibTYtuSYHgDGSL_w85_ZzwsOPZKtLABf-YiRK2bNNai-2IrA
		"""
		api_name = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={self.api_key}"

		return requests.get(api_name + puuid + "?api_key=" + api_key).json().get("name")


	@validate
	def get_match_ids(self, region, puuid, start = 0, count = 20):
		"""
		Get match history by puuid, returns a list of match IDs
		"""
		print("hi!")
		if not puuid:
			raise Exception("Empty puuid when fetching match Ids")
		api_name = f"https://{get_routing_value(region=region)}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=normal&start={start}&count={count}&api_key={self.api_key}"
		return requests.get(api_name).json()


	def get_rune_info(self):
		"""
		pull rune data
		"""
		api_name = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perks.json"
		response = requests.get(api_name)
		data = response.json()
		df = pd.DataFrame.from_dict(data)
		df.to_csv("./runes_info.csv", index = False)


	def get_summoner_spells(self):
		"""
		pull summoner spell data
		"""
		api_name = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/summoner-spells.json"
		response = requests.get(api_name)
		data = response.json()
		df = pd.DataFrame.from_dict(data)
		df.to_csv("./summoner_spells_info.csv", index = False)


	@validate
	def get_match(self, region, match_id):
		"""
		gets information for a match by match id
		"""
		data = requests.get(f"https://{get_routing_value(region=region)}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={self.api_key}").json()

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

	def get_all_champions_ids(self, patch_version):
		"""
		Fetches IDs for all champions within a given patch version.
		"""
		response = requests.get("http://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json".format(patch_version)).json()
		return [champ_data['key'] for champ_data in response['data'].values()]