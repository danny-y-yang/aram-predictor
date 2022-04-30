import requests
import os
import pandas as pd
import numpy as np
import random
import json
import os.path
import time
from riot_client import *
from df_utils import *
import argparse


class MatchCrawler:

	def __init__(self, riot_client, region):
		self.riot_client = riot_client
		self.region = region
		print("Initialized match crawler!")

	def generate_match_data(self, summoner_name, match_count):
		"""
		Creates a csv of match data by summoner name. Future plan is to generate a bunch of match ids, then use that set of match ids as argument only
		"""
		matches_generated = []
		my_puuid = self.riot_client.get_puuid(region=self.region, summoner_name=summoner_name)
		match_ids = self.riot_client.get_match_ids(region=self.region, puuid=my_puuid, start=0, count=match_count)
		df_all = pd.DataFrame()


		for match_id in match_ids:
			#Checks if the match has already been generated. We do not want to concatenate duplicate matches
			if match_id not in matches_generated:
				df_all = concatenate(df_all, self.riot_client.get_match(region=self.region, match_id=match_id))
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


	def generate_match_line(self, match_id):
		"""
		returns a single line dataframe for a match by match id; returns empty if not ARAM game
		"""
		df = self.riot_client.get_match(region=self.region, match_id=match_id)
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
			"win",
			"perk1",
			"perk2",
			"perk3",
			"perk4",
			"perk5",
			"perk6"
		]

		df = df[cols_to_keep]
		data_headers = []
		for i in range(10):
			for j in range(len(cols_to_keep)):
				data_headers.append("p" + str(i+1) + "_" + cols_to_keep[j])
		df = pd.DataFrame(df.values.reshape(-1, 200), columns = data_headers)

		df["matchId"] = match_id
		df["gameMode"] = gameMode
		return df


	def crawl(self, input_csv, summoner_seed='TyreeThePettiest'):	
		"""
		If the CSV does not exist, one will be created for you.
			If you provide a summoner id, the first line of data will be based on the provided summoner id
			If you do not provide a summoner id, the first line of data will be based on TyreeThePettiest's id. This guy ONLY plays aram
		Otherwise, appends to a particular CSV
		"""

		if os.path.isfile(input_csv) == False:
			starting_puuid = self.riot_client.get_puuid(region=self.region, summoner_name=summoner_seed)
			r = random.randint(5, 10) #grab a random match
			matchId = self.riot_client.get_match_ids(region=self.region, puuid=starting_puuid, start=r, count=r)[0]
			print(matchId)
			df_temp = self.generate_match_line(matchId)
			# print(df_temp)
			df_temp.to_csv(input_csv, index = False)
		else:
			try:
				set_matchIds = set()
				df = pd.read_csv(input_csv)
				for i in df["matchId"]:
					set_matchIds.add(i)

				r = random.randint(1, 10)
				chosen_col = df["p" + str(r) + "_puuid"].tolist()
				puuid = random.choice(chosen_col) #choose a random puuid from the entire existing dataset

				r = random.randint(5, 10) #grab a random match
				matchId = self.riot_client.get_match_ids(region=self.region, puuid=puuid, start=r, count=r)[0] #get the matchId for that random match]
				print(matchId)
				df_temp = self.generate_match_line(matchId)
				if matchId not in set_matchIds and df_temp["gameMode"][0] == "ARAM":
					df = concatenate(df, df_temp) 
				set_matchIds.add(matchId)
				df.to_csv(input_csv, index = False)
			except: 
				pass	

	def match_appender(self, input_csv, starting_puuid, n):
		"""
		crawls n matches assuming you already have 1 line of data, deprecated, please see crawl()
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
				matchId = self.riot_client.get_match_ids(region=region, puuid=puuid, start=r, count=r)[0] #get the matchId for that random match]
				print(matchId)
				df_temp = self.generate_match_line(matchId)
				if matchId not in set_matchIds and df_temp["gameMode"][0] == "ARAM":
					df = concatenate(df, df_temp) 
				set_matchIds.add(matchId)
				df.to_csv(input_csv, index = False)

				#Grab new puuid
				r = random.randint(1, 10)
				chosen_col = df["p" + str(r) + "_puuid"].tolist()
				puuid = random.choice(chosen_col)

			except Exception as e: #if getting match fails, grab an entirely new puuid
				r = random.randint(1, 10)
				chosen_col = df["p" + str(r) + "_puuid"].tolist()
				# df.to_csv(input_csv, index = False)
				puuid = random.choice(chosen_col)
				continue


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--dev_key', type=str, help='Riot API key')
	args = parser.parse_args()
	dev_key = args.dev_key

	riot_client = RiotClient(dev_key)
	match_crawler = MatchCrawler(riot_client, 'na1')

	while True:
		for i in range(20):
			match_crawler.crawl(f"../data/out_{dev_key}-test.csv", 'Shiera')
		print("pull success")
		time.sleep(2)