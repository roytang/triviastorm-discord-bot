# https://github.com/Rapptz/discord.py/blob/async/examples/reply.py
import discord
import os
import requests, json
import urllib.request, json, urllib.parse
import binascii
from apiclient import ApiClient
import traceback
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
API_TOKEN = os.getenv('API_TOKEN')
API_ROOT = os.getenv('API_ROOT')

# print("DISCORD_TOKEN", TOKEN)
# print(os.getenv("DISCORD_TOKEN"))
# print(os.getenv("API_TOKEN"))
# print(os.getenv("API_ROOT"))
# print(os.getenv("TIME_LIMIT"))
# print(os.getenv("RUN_LIMIT"))



# time for qs to be answered
TIME_LIMIT = int(os.getenv('TIME_LIMIT', 60))
RUN_LIMIT = int(os.getenv('RUN_LIMIT', 100))

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def dump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))


def is_number(s):
    """ Returns True if string is a number. """
    return s.replace(',','').replace('.','',1).isdigit()    

class TriviaBot():

    def __init__(self, channel):
        self.channel = channel
        self.current_q = None
        self.last_q = None
        self.qcount = 0
        self.tag = None
        self.api = ApiClient(channel.id, api_root=API_ROOT, token=API_TOKEN)

    async def endq(self, q=None):
        # print("endq")
        if q is None:
            q = self.current_q
        self.last_q = self.current_q
        self.current_q = None
        answers = ";".join(self.api.getanswer(q))
        print(answers)
        await self.channel.send("Time's up! Nobody got the answer! Acceptable answers: **%s**" % (answers))
        await self.afterendq()

    async def sendq(self, tag=None):
        # print("sendq")
        try:
            q = self.api.askq(tag)
        except Exception as e:
            print("Failed getting a q with tag %s" % (tag))
            track = traceback.format_exc()
            print(track)            
            await self.channel.send("Couldn't retrieve a question. Your parameters might be invalid. If there was a trivia run, it will be terminated.")
            self.qcount = 0
            return

        print(q)
        msg = "**Q#%s: %s**" % (q['id'], q['text'])
        self.current_q = q['id']
        self.hint = q['hint']
        em = None
        if len(q['attachment']) > 0:
            em = discord.Embed()
            em.set_image(url=q['attachment'])
            
        await self.channel.send(msg, embed=em)
        # schedule a task to end this q after some time
        client.loop.create_task(status_task(self, q['id']))

    async def afterendq(self):
        # print("afterendq")
        self.qcount = self.qcount - 1
        if self.qcount > 0:
            await self.channel.send("%d question(s) remaining in this run. Next question!" % (self.qcount))
            await self.sendq(self.tag)
        else:
            self.api.endq()

    def format_scores(self, raw_scores):
        scores = []
        for score in raw_scores:
            scores.append("%s : %s" % (score['name'], score['score']))
        return ", ".join(scores)

    async def checkanswer(self, message):
        text = message.content
        sender = message.author.name
        if self.current_q is not None:
            resp = self.api.submitanswer(self.current_q, text, sender)
            if resp['correct']:
                # correct submission ends the currernt_q
                self.last_q = self.current_q
                self.current_q = None
                msg = '{0.author.mention} is correct!'.format(message)
                answers = ";".join(resp['answers'])
                msg = msg + " Acceptable answers: **" + answers + "**"
                await self.channel.send(msg)
                msg = "Current scores: %s" % (self.format_scores(resp['scores']))
                await self.channel.send(msg)
                await self.afterendq()
            # else do nothing on incorrect answer

    async def report(self, message):
        text = message.content
        sender = message.author.name
        qq = None
        tokens = text.split(" ")
        # check if 2nd token is a question id
        if len(tokens) > 1:
            t1 = tokens[1].replace("#", "")
            if is_number(t1):
                qq = t1        
        
        if qq is None:
            # if no id specified, use last_q
            qq = self.last_q 

        if qq is not None:
            try:
                resp = self.api.report(qq, text, sender)
                msg = "Report submitted for #{0}, thanks for the feedback!".format(qq)
                await self.channel.send(msg)
            except:
                msg = "Error reporting feedback. You may have provided an invalid id.`"
                await self.channel.send(msg)
        else:
            msg = "You can specify a question to report by passing the question id: `!report 1234 this question is great!`"
            await self.channel.send(msg)
    
    async def scores(self):
        resp = self.api.scores()
        msg = "Current scores: %s" % (self.format_scores(resp))
        await self.channel.send(msg)


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
    print(message.content)

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
            await message.channel.send("Trivia run ended prematurely")

    if message.content.startswith('!channel'):
        msg = 'Current channel settings: Tag=%s QCount=%d' % (bot.tag, bot.qcount)
        await message.channel.send(msg)

    if message.content.startswith('!hint'):
        if bot.current_q is None:
            await message.channel.send("Hint for what?")
        else:
            await message.channel.send("Hint: `%s`" % (bot.hint))

    if message.content.startswith('!q'):

        if bot.current_q is not None:
            await message.channel.send("There's already a q in this channel, !pass to immediately end a q")
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
                await message.channel.send("There is already an existing trivia run with %d question(s) remaining, !stop to stop" % (bot.qcount))    

            if qcount > RUN_LIMIT:
                await message.channel.send("%d questions!! Are you insane? That's way too many!" % (qcount))
                return

            await message.channel.send("Starting trivia run with %d questions, !stop to stop" % (qcount))

        bot.tag = tag
        bot.qcount = qcount
        await bot.sendq(tag)

    if message.content.startswith('!report '):
        await bot.report(message)

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

