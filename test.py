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

c = ApiClient("test", token="59d6e8551296d27034a65a05c44c82a2ddb0fc05")

# print(c.getq())
# print(c.getq("movies"))

# print(c.checkanswer(5344, "groundhog day"))
# print(c.checkanswer(5344, "ghostbusters"))

# print(c.getanswer(5344))

q = c.askq("test4")
print(q)
print(c.submitanswer(q["id"], "simon pegg", "myusername22"))
print(c.endq())
