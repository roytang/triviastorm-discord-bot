# https://github.com/Rapptz/discord.py/blob/async/examples/reply.py
import discord
import os
import requests, json
import urllib.request, json, urllib.parse
import binascii
from apiclient import ApiClient

# high five for security
# apparently discord knows if i put my token up on github
TOKEN = os.environ['triviastorm.token']

# time for qs to be answered
TIME_LIMIT = 30

client = discord.Client()

def dump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))

class TriviaBot():

    def __init__(self, channel):
        self.channel = channel
        self.current_q = None
        self.qcount = 0
        self.tag = None
        self.api = ApiClient(channel.id)

    async def endq(self, q=None):
        # print("endq")
        if q is None:
            q = self.current_q
        self.current_q = None
        answers = ";".join(self.api.getanswer(q))
        print(answers)
        await client.send_message(self.channel, "Time's up! Nobody got the answer! Acceptable answers: **%s**" % (answers))
        await self.afterendq()

    async def sendq(self, tag=None):
        # print("sendq")
        try:
            q = self.api.askq(tag)
        except:
            print("Failed getting a q with tag %s" % (tag))
            await client.send_message(self.channel, "Couldn't retrieve a question. Your parameters might be invalid. If there was a trivia run, it will be terminated.")
            self.qcount = 0
            return

        msg = "**Q#%s: %s**" % (q['id'], q['text'])
        self.current_q = q['id']
        self.hint = q['hint']
        em = None
        if len(q['attachment']) > 0:
            em = discord.Embed()
            em.set_image(url=q['attachment'])
            
        await client.send_message(self.channel, msg, embed=em)
        # schedule a task to end this q after some time
        client.loop.create_task(status_task(self, q['id']))

    async def afterendq(self):
        # print("afterendq")
        self.qcount = self.qcount - 1
        if self.qcount > 0:
            await client.send_message(self.channel, "%d question(s) remaining in this run. Next question!" % (self.qcount))
            await self.sendq(self.tag)
        else:
            self.api.endq()

    def format_scores(self, raw_scores):
        scores = []
        for key in raw_scores:
            score = raw_scores[key]
            scores.append("%s : %s" % (key, score))
        return ", ".join(scores)

    async def checkanswer(self, message):
        text = message.content
        sender = message.author.name
        if self.current_q is not None:
            resp = self.api.submitanswer(self.current_q, text, sender)
            if resp['correct']:
                # correct submission ends the currernt_q
                self.current_q = None
                msg = '{0.author.mention} is correct!'.format(message)
                answers = ";".join(resp['answers'])
                msg = msg + " Acceptable answers: **" + answers + "**"
                await client.send_message(self.channel, msg)
                msg = "Current scores: %s" % (self.format_scores(resp['scores']))
                await client.send_message(self.channel, msg)
                await self.afterendq()
            # else do nothing on incorrect answer
    
    async def scores(self):
        resp = self.api.scores()
        msg = "Current scores: %s" % (self.format_scores(resp))
        await client.send_message(self.channel, msg)


bots = {}

def get_bot(channel_id):
    if channel_id in bots:
        return bots[channel_id]
    else:
        bot = TriviaBot(channel_id)
        bots[channel_id] = bot
        return bot
import asyncio

async def status_task(bot, q):
    # print("status_task")
    await asyncio.sleep(TIME_LIMIT)
    if bot.current_q == q:
        await bot.endq(q)

@client.event
async def on_message(message):
    #dump(message)

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    bot = get_bot(message.channel)

    if message.content.startswith('!pass'):
        await bot.endq()

    if message.content.startswith('!scores'):
        await bot.scores()

    if message.content.startswith('!stop'):
        qcount = bot.qcount
        bot.qcount = 0
        await bot.endq()
        if qcount > 1:
            await client.send_message(message.channel, "Trivia run ended prematurely")

    if message.content.startswith('!channel'):
        msg = 'Current channel settings: Tag=%s QCount=%d' % (bot.tag, bot.qcount)
        await client.send_message(message.channel, msg)

    if message.content.startswith('!hint'):
        if bot.current_q is None:
            await client.send_message(message.channel, "Hint for what?")
        else:
            await client.send_message(message.channel, "Hint: `%s`" % (bot.hint))

    if message.content.startswith('!q'):

        if bot.current_q is not None:
            await client.send_message(message.channel, "There's already a q in this channel, !pass to immediately end a q")
            return

        # parameter parsing
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
            if bot.qcount > 1:
                await client.send_message(message.channel, "There is already an existing trivia run with %d question(s) remaining, !stop to stop" % (bot.qcount))    
            await client.send_message(message.channel, "Starting trivia run with %d questions, !stop to stop" % (qcount))

        bot.tag = tag
        bot.qcount = qcount
        await bot.sendq(tag)

    # all other messages to be treated as potential answers
    else:
        await bot.checkanswer(message)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

if __name__ == '__main__':
    print("Starting client")
    client.run(TOKEN)

