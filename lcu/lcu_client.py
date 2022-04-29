import requests
from requests.auth import HTTPBasicAuth

from base64 import b64encode
import platform
import os
import json

_PORT = 'port'
_PASSWORD = 'password'

def parse_lockfile():
	"""
	lockfile is a special file that is created when LCU (League Client) starts. It contains the port, pid of the application, and a unique
	password for this instance of the client. A new password is created each time the client starts, so we must dynamically query for it.

	Format is: "LeagueClient:<PID>:<PORT>:<PASSWORD>:https"
	Example content: "LeagueClient:51815:65203:ZRP5aFUJ_l4sbtMfxfcyYQ:https"
	"""

	op_system = platform.system()

	# path to lockfile is different depending on operating system.
	if op_system == 'Darwin':

		# Default path of League client. If its different, you're gay.
		path = '/Applications/League of Legends.app/Contents/LoL'
	else:

		## TODO: Windows
		raise Exception(f"{op_system} not supported yet.")

	lockfile_path = f"{path}/lockfile"
	if not os.path.exists(lockfile_path):
		raise Exception(f"lockfile was not found in path[{lockfile_path}]. Is LCU running?")

	with open(lockfile_path, 'r') as lockfile_in:
		data = lockfile_in.read().split(':')
		return {
			_PORT: data[2],
			_PASSWORD: data[3]
		}

class LCUClient:
	def __init__(self):
		lcu_metadata = parse_lockfile()

		self.base_url = 'https://127.0.0.1'
		self.port = lcu_metadata[_PORT]

		base_64_auth_key = b64encode(str.encode(f"riot:{lcu_metadata[_PASSWORD]}")).decode()
		self.basic_auth = f"Basic {base_64_auth_key}"


	def get(self, endpoint):
		"""
		Wrapper method for GET queries against LCU client.
		"""
		headers = {
			'Accept': 'application/json', 
			'Authorization': self.basic_auth
		}
		return requests.get(f"{self.base_url}:{self.port}/{endpoint}", 
			headers=headers, 
			verify=False # ignore self signed certificate
		).json()
		

	def whoami(self):
		"""
		Sample response: 
		{
		    "accountId": 35699771,
		    "displayName": "Feyeing",
		    "internalName": "Feyeing",
		    "nameChangeFlag": false,
		    "percentCompleteForNextLevel": 11,
		    "privacy": "PUBLIC",
		    "profileIconId": 512,
		    "puuid": "66e161c9-fe2f-5344-aa1a-df91fd6b333f",
		    "rerollPoints": {
		        "currentPoints": 302,
		        "maxRolls": 2,
		        "numberOfRolls": 1,
		        "pointsCostToRoll": 250,
		        "pointsToReroll": 198
		    },
		    "summonerId": 22066834,
		    "summonerLevel": 244,
		    "unnamed": false,
		    "xpSinceLastLevel": 406,
		    "xpUntilNextLevel": 3456
		}
		"""
		return self.get('lol-summoner/v1/current-summoner')