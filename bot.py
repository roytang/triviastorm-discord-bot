# https://github.com/Rapptz/discord.py/blob/async/examples/reply.py
import discord

TOKEN = 'MzM5MzM2Nzc1NjI3NzAyMjcy.DZ1LzQ.--eznYFj61kPrW9JGoKMeRNwS7w'

client = discord.Client()

def dump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))

def getq():
    import urllib.request, json 
    with urllib.request.urlopen("http://triviastorm.net/api/getq/") as url:
        data = json.loads(url.read().decode())
        return data

def checkanswer(q, text):
    import urllib.request, json, urllib.parse
    target = "http://triviastorm.net/api/checkanswer/%s/?ans=%s" % (q, urllib.parse.quote(text))
    print(target)
    with urllib.request.urlopen(target) as url:
        data = json.loads(url.read().decode())
        return data['correct']

def getanswer(q):
    import urllib.request, json, urllib.parse
    target = "http://triviastorm.net/api/getanswer/%s/" % (q)
    print(target)
    with urllib.request.urlopen(target) as url:
        data = json.loads(url.read().decode())
        return data['answers']

current_qs = {}            

import asyncio

async def status_task(q, channel):
    await asyncio.sleep(30)
    if channel.id in current_qs and current_qs[channel.id] == q:
        del current_qs[channel.id]
        answers = ";".join(getanswer(q))
        #print(answers)
        await client.send_message(channel, "Time's up! Nobody got the answer! Acceptable answers: %s" % (answers))

@client.event
async def on_message(message):
    #dump(message)

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)

    if message.content.startswith('!q'):
        q = getq()
        msg = "Q: " + q['text']
        current_qs[message.channel.id] = q['id']
        em = None
        if len(q['attachment']) > 0:
            em = discord.Embed()
            em.set_image(url=q['attachment'])
            
        await client.send_message(message.channel, msg, embed=em)
        client.loop.create_task(status_task(q['id'], message.channel))

    else:
        if message.channel.id in current_qs:
            q = current_qs[message.channel.id]
            text = message.content
            if checkanswer(q, text):
                del current_qs[message.channel.id]
                msg = '{0.author.mention} is correct!'.format(message)
                await client.send_message(message.channel, msg)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

print("Starting client")
client.run(TOKEN)

