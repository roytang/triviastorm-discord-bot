# https://github.com/Rapptz/discord.py/blob/async/examples/reply.py
import requests, json

def checkanswer(q, text):
    payload = { "ans" : text}
    target = "http://triviastorm.net/api/checkanswer/%s/" % (q)
    r = requests.get(target, params=payload)
    data = r.json()
    return data['correct']

print(checkanswer('17444', 'lich king'))