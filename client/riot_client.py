import requests
import os

elu_puuid = "XmEmjOPvqoEUkkgks49W3gYvvumXWcibTYtuSYHgDGSL_w85_ZzwsOPZKtLABf-YiRK2bNNai-2IrA"

dev_key = os.environ["riot_api_key"]

#Get player id by summoner name
def get_player_id(summoner_name):
	api_name = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/"
	response = requests.get(api_name + summoner_name + "?api_key=" + dev_key)
	print(response.json())

#Get match history by puuid, returns a list of match IDs
def get_matches(puuid, start = 0, count = 20):
	api_name = "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/"
	response = requests.get(api_name + puuid + "/ids?start=" + str(start) + "&count=" + str(count) + "&api_key=" + dev_key)
	print(response.json()) 

get_player_id("Elucidaze")

get_matches(elu_puuid, 0, 100)
