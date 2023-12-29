import aiohttp, json, asyncio, requests, threading, random, tasksio, ctypes, time, traceback
from aiohttp_socks import ProxyConnector
from httpstuff import ProxyPool
from discord_webhook import DiscordWebhook, DiscordEmbed

proxies = open('txts/proxies.txt').read().splitlines()[0:500]
ignore = ['1', '15189', '80254', '986']
itemData = None

def roliValue():
    global itemData
    while 1:
        try:
            itemData = requests.get(
                'https://www.rolimons.com/itemapi/itemdetails'
            ).json()['items']
        except: pass
        time.sleep(60)
threading.Thread(target=roliValue).start()
time.sleep(3)

class Bot:
    def __init__(self):
        self.ProxyPool = ProxyPool(proxies.copy())
        self.checkedUsers = 0
        self.userLen = 0
        self.uaidLog = json.load(open('uaidLog.json'))
        threading.Thread(target=self.title).start()
        asyncio.run(self.threads())

    async def threads(self):
        global users
        await self.sessions()
        while 1:
            with open('uaidLog.json', 'w') as file:
                json.dump(self.uaidLog, file, indent=4)
            currentLog = {}

            users = [
                i for i in json.load(
                    open('playerValues.json')
                )
            ] + open('txts/seperateUsers.txt').read().splitlines()
            users = list(set(users))
            _users = [i for i in users if i not in ignore]
            self.userLen = len(_users)

            self.checkedUsers = 0
            async with tasksio.TaskPool(100) as pool:
                for i in range(100):
                    await pool.put(self.checkInventories(_users[i::100], currentLog))

            ignorePair = []
            for uaid in currentLog:
                if uaid in self.uaidLog:
                    if currentLog[uaid] != self.uaidLog[uaid]:
                        pair = [int(currentLog[uaid]), int(self.uaidLog[uaid])]
                        pair.sort()
                        if pair not in ignorePair:
                            await self.findTrade(currentLog[uaid], self.uaidLog[uaid], self.uaidLog)
                            ignorePair.append(pair)
            self.uaidLog = currentLog

    async def getInventory(self, player):
        inventory = []
        async with aiohttp.ClientSession() as session:
            cursor = ''
            while cursor != None:
                proxy = self.ProxyPool.get()
                self.ProxyPool.put(proxy)
                try:
                    response = await self.sessionStorage[proxy].get(
                        f'https://inventory.roblox.com/v1/users/{player}/assets/collectibles?sortOrder=Asc&limit=100&cursor={cursor}', timeout = 4
                    )
                    if response.status == 200:
                        data = await response.json()
                        for item in data['data']:
                            inventory.append({'assetId': str(item['assetId']), 'UAID': str(item['userAssetId'])})
                        cursor = data['nextPageCursor']
                    else:
                        data = await response.json()
                        if data['errors'][0]['code'] in [1, 11]:
                            break
                except:
                    pass
        return inventory

    def sortKey(self, n):
        return int(n.split('**')[1].split('**')[0])

    async def getInfo(self, player, offer):
        itemLog, value, highestid, total = [], 0, '', 0
        for item in offer:
            assetId, uaid = item['assetId'], item['UAID']
            if itemData[assetId][4] > total:
                highestid = assetId
                total = itemData[assetId][4]
            itemLog.append(f"(**{itemData[assetId][4]}**) {itemData[assetId][0]}")
            value += itemData[assetId][4]
        itemLog.sort(key=self.sortKey, reverse=True)
        return value, itemLog, highestid

    async def getImage(self, highest):
        async with aiohttp.ClientSession() as session:
            while 1:
                try:
                    async with session.get(f'https://thumbnails.roblox.com/v1/assets?assetIds={highest}&size=250x250&format=Png', timeout=4, proxy='http://%s' % random.choice(proxies)) as response:
                        data = await response.json()
                        return data['data'][0]['imageUrl']
                except:
                    pass

    async def getUser(self, player):
        async with aiohttp.ClientSession() as session:
            while 1:
                try:
                    async with session.get(f'https://users.roblox.com/v1/users/{player}', timeout=4, proxy='http://%s' % random.choice(proxies)) as response:
                        data = await response.json()
                        return data['name']
                except:
                    pass

    async def sendTrade(self, player1, player2, p1_offer, p2_offer):
        p1_value, p1_embed, p1_highest = await self.getInfo(player1, p1_offer)
        p2_value, p2_embed, p2_highest = await self.getInfo(player2, p2_offer)
        if p1_value >= 5000 and p2_value >= 5000:
            p1_user = await self.getUser(player1)
            p2_user = await self.getUser(player2)
            if itemData[p1_highest][4] > itemData[p2_highest][4]: highest = p1_highest
            else: highest = p2_highest

            if itemData[highest][4] >= 1000000:
                webhook = DiscordWebhook(url='https://discord.com/api/webhooks/1184223297949405324/_jNXD7HunTB3H42yBLsVLOIxKvoAxjHySiq7UBDjCp38e2hhDIDhEMOAhvL5M_wzcp57')
            elif itemData[highest][4] >= 100000:
                webhook = DiscordWebhook(url='https://discord.com/api/webhooks/1180858959058436126/2HWxLm4xPWhIxf5hXWtzn0fWpyh2IBj9a9haOs1CBgaUFhp77xd6h_cIUYZzMXVevMLi')
            else:
                webhook = DiscordWebhook(url='https://discord.com/api/webhooks/1180673246794883143/nak4gnpo-P3x5mUI6z5cacWWVd-Dc1CCD5uRUsqAfec_xYS4mcxMOmrTxbeA8_RegiCQ')

            p1_embed = '\n'.join(p1_embed)
            p2_embed = '\n'.join(p2_embed)
            imgUrl = await self.getImage(highest)
            embed = DiscordEmbed(description=f'**[{p2_user}](https://www.rolimons.com/player/{player2})** traded with **[{p1_user}](https://www.rolimons.com/player/{player1})**\n\u200b', color='cc99ff')
            embed.set_thumbnail(url=imgUrl)
            embed.add_embed_field(name=f'{p2_user} - {p1_value}', value=f'{p1_embed}', inline=False)
            embed.add_embed_field(name=f'{p1_user} - {p2_value}', value=f'{p2_embed}', inline=False)
            embed.set_footer(text="trade COULD have included usd/robux")
            webhook.add_embed(embed)
            response = webhook.execute()
        else:
            print('lower than 5k')


    async def findTrade(self, player1, player2, oldLog):
        print(player1, player2)
        try:
            p1_inv = await self.getInventory(player1)
            p2_inv = await self.getInventory(player2)
            p1_offer = [i for i in p1_inv if i['UAID'] in oldLog and oldLog[i['UAID']] == player2]
            p2_offer = [i for i in p2_inv if i['UAID'] in oldLog and oldLog[i['UAID']] == player1]
            if p1_offer and p2_offer:
                if len(p1_offer) <= 4 and len(p2_offer) <= 4:
                    await self.sendTrade(player1, player2, p1_offer, p2_offer)
                else:
                    print('double trade')
            else:
                print(p1_offer, p2_offer)
        except Exception as err:
            print(err)
            pass

    def title(self):
        while 1:
            ctypes.windll.kernel32.SetConsoleTitleW(f'checked: {self.userLen}/{self.checkedUsers}')
            time.sleep(1)

    async def sessions(self):
        self.sessionStorage = {}
        for proxy in self.ProxyPool.raw_proxies:
            self.sessionStorage[proxy] = aiohttp.ClientSession(
                connector = ProxyConnector.from_url(f"http://{proxy}")
            )

    async def checkInventories(self, players, currentLog):
        global ignore
        for player in players:
            cursor, totalItems = '', 0
            while ((cursor != None) and (totalItems <= 1000)):
                proxy = self.ProxyPool.get()
                self.ProxyPool.put(proxy)
                try:
                    response = await self.sessionStorage[proxy].get(
                        f'https://inventory.roblox.com/v1/users/{player}/assets/collectibles?sortOrder=Asc&limit=100&cursor={cursor}', timeout = 4
                    )
                    data = await response.json()

                    if response.status == 200:

                        for item in data['data']:
                            currentLog[str(item['userAssetId'])] = player

                        cursor = data['nextPageCursor']
                        if cursor: totalItems += 100

                    else:
                        if data['errors'][0]['code'] in [1, 11]:
                            #ignore.append(player)
                            break

                except:
                    pass
            self.checkedUsers += 1

Bot()
