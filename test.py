# https://github.com/Rapptz/discord.py/blob/async/examples/reply.py
# import requests, json

# def checkanswer(q, text):
#     payload = { "ans" : text}
#     target = "http://triviastorm.net/api/checkanswer/%s/" % (q)
#     r = requests.get(target, params=payload)
#     data = r.json()
#     return data['correct']

# print(checkanswer('17444', 'lich king'))

from apiclient import ApiClient

c = ApiClient()

print(c.getq())
print(c.getq("flags"))

print(c.checkanswer(16546, "parkour"))
print(c.checkanswer(16546, "notparkour"))

print(c.getanswer(16546))