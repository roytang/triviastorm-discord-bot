import os
import requests
import binascii

class ApiClient():

    def __init__(self, channel_id, api_root, token):
        self.channel_id = channel_id
        self.api_root = api_root
        print("self.api_root", api_root)
        self.headers = { 'Authorization': 'Token %s' % token }

    def get(self, endpoint, payload={}):
        target = self.api_root + endpoint
        print("sending get", target, payload)
        r = requests.get(target, params=payload, headers=self.headers)
        data = r.json()
        return data

    def post(self, endpoint, payload={}):
        target = self.api_root + endpoint
        payload['channel_id'] = self.channel_id
        print("sending post", target, payload)
        r = requests.post(target, data=payload, headers=self.headers)
        data = r.json()
        return data

    def askq(self, tag=''):
        return self.post("questions/ask/", { "tag": tag })

    def endq(self):
        return self.post("questions/end/")

    def submitanswer(self, q, text, sender):
        text = binascii.hexlify(text.encode()).decode()
        payload = { "anshex" : text, "sender": sender }
        return self.post("questions/%s/submit/" % (q), payload)

    def report(self, q, text, sender):
        text = binascii.hexlify(text.encode()).decode()
        payload = { "feedbackhex" : text, "sender": sender }
        return self.post("questions/%s/report/" % (q), payload)

    def scores(self):
        return self.post("questions/scores/")

    def getq(self, tag=''):
        return self.get("questions/get/", { "tag": tag })

    def checkanswer(self, q, text):
        text = binascii.hexlify(text.encode()).decode()
        payload = { "anshex" : text}
        return self.get("questions/%s/check/" % (q), payload)['correct']

    def getanswer(self, q):
        return self.get("questions/%s/answer/" % (q))['answers']

