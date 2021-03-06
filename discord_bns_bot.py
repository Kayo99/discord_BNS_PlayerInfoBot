################################################################################
#   FileName: discord_bns_bot.py
#   Author: Jack (https://github.com/wei0831)
#   Date: 04/10/2016
################################################################################
from aiohttp import get
from lxml.html import fromstring
import discord
import getpass

################################################################################
#   USER SETTING
################################################################################
# 'na' or 'eu'
BNS_REGION = 'na'

# Your Discord Email
DISCORD_USER_EMAIL = None #'user@example.com'

# Your Discord Password
DISCORD_USER_PSW = None   #'userpassword'

# Only check message from certain server
WATCH_FOR_SERVER = False
SERVER_LIST = []

# Only check message from certain channel
WATCH_FOR_CHANNEL = False
CHANNEL_LIST = []

# Check direct message or not
WATCH_FOR_PRIVATE_MSG = True

# Commision percentage
SMART_BID_TAX = 0.95

################################################################################
#   PROGRAM SETTING
################################################################################
BNS_WEB_PROFILE = 'http://{region}-bns.ncsoft.com/ingame/bs/character/profile?c={name}'
BNS_WEB_SEARCH = 'http://{region}-bns.ncsoft.com/ingame/bs/character/search/info?c={name}'

# Stats
HP = 44
DEFENSE = 48
ATK_POWER = 0
CRIT_RATE = 24
CRIT_DMG = 28
# Equipment
WEAPON = 0
RING = 6
EARING = 2
NECKLACE = 1
BRACELET = 4
BELT = 8

################################################################################
#   Data Class
################################################################################
class Character:
    """ This represent player's character data scraping from accessing BNS web API.
    """
    def __init__(self, name):
        """ Initializing properties of a character
        Feel free to add more properties as you needed.

        Args:
            name (str): Character name to search
        """
        self.name = name
        self.id = None
        self.class_name = None
        self.server = None
        self.level = None
        self.hmlevel = None
        self.faction = None
        self.factionLevel = None
        self.guild = None
        self.weapon_durability = None
        self.stats = None
        self.equips = None
        self.error = False
        self.otherChars = None

    async def parse(self):
        """ Parsing character data from accessing BNS web API
        """
        # Need to convert space to URL encoding character
        page = await get(BNS_WEB_PROFILE.format(name=self.name.replace(' ', '%20'), region=BNS_REGION))
        content = await page.read()
        content = fromstring(str(content))

        # Player ID
        playerID = content.xpath('//dl[@class="signature"]/dt/a/text()')
        if len(playerID) != 0:
            self.id = playerID[0]
        else:
            # Not found, Skip the rest
            self.error = True
            return

        # Player HM Level
        playerHMLv = content.xpath('//span[@class="masteryLv"]/text()')
        if len(playerHMLv) != 0:
            self.hmlevel = playerHMLv[0]

        # Player Info
        playerInfo = content.xpath('//dd[@class="desc"]/ul/li/text()')

        if self.hmlevel == None:
            if len(playerInfo) == 3:
                # [CLASS NAME] [LEVEL] [SERVER]
                self.class_name, self.level, self.server = [x.replace('[', '').replace(']', '') for x in playerInfo]
            elif len(playerInfo) == 4:
                # [CLASS NAME] [LEVEL] [SERVER] [FACTION]
                self.class_name, self.level, self.server, self.faction = [x.replace('[', '').replace(']', '') for x in playerInfo]
            elif len(playerInfo) == 5:
                # [CLASS NAME] [LEVEL] [SERVER] [FACTION] [GUILD]
                self.class_name, self.level, self.server, self.faction, self.guild = [x.replace('[', '').replace(']', '') for x in playerInfo]
        else:
            if len(playerInfo) == 4:
                # [CLASS NAME] [LEVEL] [] [SERVER]
                self.class_name, self.level, _, self.server = [x.replace('[', '').replace(']', '') for x in playerInfo]
            elif len(playerInfo) == 5:
                # [CLASS NAME] [LEVEL] [] [SERVER] [FACTION]
                self.class_name, self.level, _, self.server, self.faction = [x.replace('[', '').replace(']', '') for x in playerInfo]
            elif len(playerInfo) == 6:
                # [CLASS NAME] [LEVEL] [] [SERVER] [FACTION] [GUILD]
                self.class_name, self.level, _, self.server, self.faction, self.guild = [x.replace('[', '').replace(']', '') for x in playerInfo]

        # Faction and Faction Level
        if self.faction != None:
            faction_texts = self.faction.split('\xa0')
            self.faction = faction_texts[0]
            self.factionLevel = faction_texts[1]

        # Player Stats
        self.stats = content.xpath('//span[@class="stat-point"]/text()')

        # Player Equipments
        self.equips = content.xpath('//div[@class="name"]/span/text()')

        # Player Weapon Durability
        playerWeaponDurability = content.xpath('//div[@class="wrapWeapon"]/div/div[@class="quality"]/span[@class="text"]/text()')
        if len(playerWeaponDurability) != 0:
            self.weapon_durability = playerWeaponDurability[0]

        # Find other characters
        page = await get(BNS_WEB_SEARCH.format(name=self.name.replace(' ', '%20'), region=BNS_REGION))
        content = await page.read()
        content = fromstring(str(content))

        firstResult = content.xpath('//dd[@class="desc2"]')[0]
        self.otherChars = firstResult.xpath('.//ul/li/a/text()')

    def format(self):
        """ Output character data as string
        """
        if self.error:
            result = '```\n' \
                   '==== Character Profile ====\n' \
                   'Character Not Found !!\n' \
                   '============================\n' \
                   '```\n'
            return result

        result =  '```\n' \
               '================= Character Profile ===================\n' \
               'Name:  {name} [{ID}]\n' \
               'Guild: {guild} [{server}]\n' \
               'Faction: {faction} | {factionLevel}\n' \
               'Class: {class_name}\n' \
               'Level: {level} | {hmlevel}\n' \
               '--------------------------------------------------------\n' \
               'Attack Power: {attack_power}\n' \
               'Crit Rate:    {crit_rate}\n' \
               'Crit Damage:  {crit_dmg}\n' \
               'HP:           {hp}\n' \
               'Defense:      {defense}\n' \
               '--------------------------------------------------------\n' \
               'Weapon:   {weapon} [{weapon_durability}]\n' \
               'Ring:     {ring}\n' \
               'Earing:   {earing}\n' \
               'Necklace: {necklace}\n' \
               'Bracelet: {bracelet}\n' \
               'Belt:     {belt}\n'

        if self.otherChars != None:
            result += '--------------------------------------------------------\n' \
                      'Other Characters: '
            if len(self.otherChars) == 0:
                result += 'None\n'
            else:
                result += '\n'
                for c in self.otherChars:
                    result += '\t' + c + '\n'

        result += '========================================================\n' \
                  '```\n'

        return result.format(name=self.name,
            ID=self.id,
            server=self.server,
            class_name=self.class_name,
            level=self.level,
            hmlevel = self.hmlevel,
            faction=self.faction,
            factionLevel=self.factionLevel,
            guild=self.guild,
            weapon=self.equips[WEAPON],
            weapon_durability=self.weapon_durability,
            ring=self.equips[RING],
            earing=self.equips[EARING],
            necklace=self.equips[NECKLACE],
            bracelet=self.equips[BRACELET],
            belt=self.equips[BELT],
            attack_power=self.stats[ATK_POWER],
            crit_rate=self.stats[CRIT_RATE],
            crit_dmg=self.stats[CRIT_DMG],
            hp=self.stats[HP],
            defense=self.stats[DEFENSE])


################################################################################
#   Smart Bid Class
################################################################################
class Bid:
    def __init__(self, people, marketprice):
        self.people = None
        self.marketprice = None
        self.maxBid = None
        self.maxBidIfSell = None
        self.error = False

        try:
            self.people = int(people)
            self.marketprice = float(marketprice)
        except ValueError:
            self.error = True
            return

        self.maxBid = self.marketprice * ((self.people - 1) / self.people)
        self.maxBidIfSell = self.maxBid * SMART_BID_TAX

    def format(self):
        if self.error:
            return '```\nSomething went wrong...\n```\n'

        str = '```\n' \
              '========== Smart Bid ==========\n' \
              'People in Group: {people}\n' \
              'Market Price: {marketprice}\n' \
              'Max Bid: {maxBid:.2f}\n' \
              'Max Bid if selling: {maxBidIfSell:.2f}\n' \
              '================================\n' \
              '```\n'
        return str.format(people=self.people, marketprice=self.marketprice, maxBid=self.maxBid, maxBidIfSell=self.maxBidIfSell)


################################################################################
#   Discord
################################################################################
print("==== Discord BNS Character Info Search Bot ====")
print("[SYS] Initializing discord client...")
client = discord.Client(cache_auth=False)

@client.event
async def on_message(msg):
    ''' Detect message in discord
    '''

    # Ignore slef's message
    if msg.author.id == client.user.id:
        return

    if msg.channel.is_private:
        if not WATCH_FOR_PRIVATE_MSG:
            return
    else:
        # Only respond to messages form certian servers
        if WATCH_FOR_SERVER and msg.channel.server.name not in SERVER_LIST:
            return

        # Only respond to messages form certian channels
        if WATCH_FOR_CHANNEL and msg.channel.name not in CHANNEL_LIST:
            return

    if msg.content.startswith('!help'):
        result = '```\n' \
              '==== Command Lists ====\n' \
              '\t!p [Character Name] - Show Character Stats\n' \
              '\t!b [Number of People] [Market Price] - Smart Bid\n' \
              '========================\n' \
              '```\n'
        await client.send_message(msg.channel, result)

    elif msg.content.startswith('!p'):
        args = msg.content.split(' ')
        character = Character(' '.join(args[1:]))
        await character.parse()
        await client.send_message(msg.channel, character.format())

    elif msg.content.startswith('!b'):
        args = msg.content.split(' ')
        if len(args) < 3:
            await client.send_message(msg.channel, "```\nCommand Syntax:\n\t!b [Number of People] [Market Price]\n```\n")
        else:
            bid = Bid(args[1], args[2])
            await client.send_message(msg.channel, bid.format())

@client.event
async def on_ready():
    print("[SYS] Successfully login as the user: '{user}'".format(user=client.user.name))
    print("[SYS] Monitoring...")


################################################################################
#   Main
################################################################################
userID = DISCORD_USER_EMAIL
userPSW = DISCORD_USER_PSW
if userID == None:
    userID = input("Enter Discord Email: ")
else:
    print("Your Discord ID is {userID}".format(userID=userID))
if userPSW == None:
    userPSW = getpass.getpass("Enter Discord Password: ")

try:
    client.run(userID, userPSW)
except:
    print("[ERROR] Login Fail...")

client.close()
