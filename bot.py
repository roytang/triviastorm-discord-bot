# https://github.com/Rapptz/discord.py/blob/async/examples/reply.py
import discord
import os
import requests, json
import urllib.request, json, urllib.parse


# high five for security
# apparently discord knows if i put my token up on github
TOKEN = os.environ['triviastorm.token']

client = discord.Client()

def dump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))

def getq(tag):
    import urllib.request, json 
    target = "http://triviastorm.net/api/getq/"
    if len(tag) > 0:
        target = target + "?tag="+tag
    with urllib.request.urlopen(target) as url:
        data = json.loads(url.read().decode())
        return data

def checkanswer(q, text):
    payload = { "ans" : text}
    target = "http://triviastorm.net/api/checkanswer/%s/" % (q)
    r = requests.get(target, params=payload)
    data = r.json()
    return data['correct']

def getanswer(q):
    target = "http://triviastorm.net/api/getanswer/%s/" % (q)
    print(target)
    with urllib.request.urlopen(target) as url:
        data = json.loads(url.read().decode())
        return data['answers']

current_qs = {}            
channel_settings = {}

import asyncio

async def afterendq(channel):
    # print("afterendq")
    channel_settings[channel.id]['qcount'] = channel_settings[channel.id]['qcount'] - 1
    if channel_settings[channel.id]['qcount'] > 0:
        await client.send_message(channel, "%d question(s) remaining in this run. Next question!" % (channel_settings[channel.id]['qcount']))
        await sendq(channel, channel_settings[channel.id]['tag'])

async def endq(channel, q=None):
    # print("endq")
    if q is None:
        q = current_qs[channel.id]
    del current_qs[channel.id]
    answers = ";".join(getanswer(q))
    #print(answers)
    await client.send_message(channel, "Time's up! Nobody got the answer! Acceptable answers: %s" % (answers))
    await afterendq(channel)

async def sendq(channel, tag):
    # print("sendq")
    try:
        q = getq(tag)
    except:
        print("Failed getting a q with tag %s" % (tag))
        await client.send_message(channel, "Couldn't retrieve a question. Your parameters might be invalid. If there was a trivia run, it will be terminated.")
        channel_settings[channel.id]['qcount'] = 0
        return
    msg = "Q#%s: %s" % (q['id'], q['text'])
    current_qs[channel.id] = q['id']
    em = None
    if len(q['attachment']) > 0:
        em = discord.Embed()
        em.set_image(url=q['attachment'])
        
    await client.send_message(channel, msg, embed=em)
    client.loop.create_task(status_task(q['id'], channel))
        

async def status_task(q, channel):
    # print("status_task")
    await asyncio.sleep(30)
    if channel.id in current_qs and current_qs[channel.id] == q:
        await endq(channel, q)

@client.event
async def on_message(message):
    #dump(message)

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)

    if message.content.startswith('!pass'):
        if message.channel.id in current_qs:
            await endq(message.channel)

    if message.content.startswith('!stop'):
        if message.channel.id in current_qs and message.channel.id in channel_settings:
            qcount = channel_settings[message.channel.id]['qcount']
            await endq(message.channel)
            if qcount > 1:
                await client.send_message(message.channel, "Trivia run ended prematurely")
            channel_settings[message.channel.id]['qcount'] = 0

    if message.content.startswith('!channel'):
        if message.channel.id not in channel_settings:
            channel_settings[message.channel.id] = {}
            channel_settings[message.channel.id]['tag'] = ""
            channel_settings[message.channel.id]['qcount'] = 0
        msg = 'Current channel settings: Tag=%s QCount=%d' % (channel_settings[message.channel.id]['tag'], channel_settings[message.channel.id]['qcount'])
        await client.send_message(message.channel, msg)
        
    if message.content.startswith('!q'):

        if message.channel.id in current_qs:
            await client.send_message(message.channel, "There's already a q in this channel, !pass to immediately end a q")
            return

        params = message.content.split()
        tag = ""
        qcount = 1
        if len(params) == 2:
            try:
                qcount = int(params[1])
            except ValueError:
                tag = params[1]
        if len(params) == 3:
            tag = params[1]
            qcount = int(params[2])

        if qcount > 1:
            if message.channel.id in channel_settings and channel_settings[message.channel.id]['qcount'] > 1:
                await client.send_message(message.channel, "There is already an existing trivia run with %d question(s) remaining, !stop to stop" % (channel_settings[message.channel.id]['qcount']))    
            await client.send_message(message.channel, "Starting trivia run with %d questions, !stop to stop" % (qcount))

        if message.channel.id not in channel_settings:
            channel_settings[message.channel.id] = {}

        channel_settings[message.channel.id]['tag'] = tag
        channel_settings[message.channel.id]['qcount'] = qcount

        await sendq(message.channel, tag)

    else:
        if message.channel.id in current_qs:
            q = current_qs[message.channel.id]
            text = message.content
            if checkanswer(q, text):
                del current_qs[message.channel.id]
                msg = '{0.author.mention} is correct!'.format(message)
                await client.send_message(message.channel, msg)
                await afterendq(message.channel)
                


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

if __name__ == '__main__':
    print("Starting client")
    client.run(TOKEN)

