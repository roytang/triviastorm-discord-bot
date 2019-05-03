import os
import requests
import binascii

API_TOKEN = '' # os.environ['triviastorm.api_token']
API_ROOT = "https://triviastorm.net/api/v2/"

class ApiClient():

    def get(self, endpoint, payload={}):
        target = API_ROOT + endpoint

        r = requests.get(target, params=payload)
        data = r.json()
        return data

    def getq(self, tag=''):
        return self.get("questions/get/", { "tag": tag })

    def checkanswer(self, q, text):
        text = binascii.hexlify(text.encode()).decode()
        payload = { "anshex" : text}
        return self.get("questions/%s/check/" % (q), payload)['correct']

    def getanswer(self, q):
        return self.get("questions/%s/answer/" % (q))['answers']

