import os, re, json, random, tasksio, ctypes, math, threading, requests, time
from discord_webhook import DiscordWebhook, DiscordEmbed
from collections import Counter
from datetime import datetime
from itertools import cycle

cookies = cycle(open('txts/cookies.txt').read().splitlines())
proxies = open('txts/proxies.txt').read().splitlines()
limiteds = open('txts/limiteds.txt').read().splitlines()
proxies = cycle([{'https': 'http://%s' % proxy} for proxy in proxies])

def sort_list(inp):
    return int(inp.split('(**')[1].split('**)')[0])

class Bot:
    def __init__(self):
        self.bannedPlayers = open('txts/banned.txt').read().splitlines()
        with open('uaidLog.json') as uaidLog:
            self.uaidLog = json.load(uaidLog)
        with open('playerValues.json') as playerValue:
            self.playerValue = json.load(playerValue)
        self.main()

    def title(self):
        while 1:
            ctypes.windll.kernel32.SetConsoleTitleW(f'{self.completed}/{self.total} - {self.checked}/{len(limiteds)}')
            time.sleep(1)
            if self.completed == self.total:
                return 1

    def updateRoli(self):
        while 1:
            try:
                self.itemDetails = requests.get(
                    'https://www.rolimons.com/itemapi/itemdetails'
                ).json()['items']
            except: pass
            time.sleep(60)

    def checkCookie(self, cookie):
        try:
            response = requests.get('https://accountsettings.roblox.com/v1/email', timeout=4, cookies={'.ROBLOSECURITY': cookie})
            if response.status_code == 200:
                return 1
            else:
                return 0
        except:
            return 0
            pass

    def uaidUpdater(self, _limiteds, newLog):
        while 1:
            if len(_limiteds):
                limited = _limiteds.pop()
                cursor = ''
                while cursor != None:
                    cookie = next(cookies)
                    try:
                        response = requests.get(
                            'https://inventory.roblox.com/v2/assets/%s/owners?sortOrder=Asc&limit=100&cursor=%s' % (limited, cursor),
                            proxies = next(proxies), timeout = 5, cookies = {'.ROBLOSECURITY': cookie}
                        )
                        if response.status_code == 200:
                            data = response.json()['data']
                            if not any(i['owner'] != None for i in data):
                                valid = self.checkCookie(cookie)
                                if not valid: continue

                            for item in data:
                                if item['owner']:
                                    newLog[str(item['id'])] = {'owner': item['owner']['id'], 'assetId': limited, 'updated': item['updated']}
                                else:
                                    newLog[str(item['id'])] = {'owner': None, 'assetId': limited, 'updated': item['updated']}
                            cursor = response.json()['nextPageCursor']
                    except:
                        pass
                self.checked += 1
            else:
                self.completed += 1
                return 1


    def analyseLog(self, newLog):
        playerValue, potentialBanned, potentialLost = {}, [], []
        for uaid in newLog:
            if uaid in self.uaidLog:
                owner = newLog[uaid]['owner']
                assetId = str(newLog[uaid]['assetId'])
                updated = newLog[uaid]['updated']
                if owner:
                    if not playerValue.get(str(owner)): playerValue[str(owner)] = {'value': 0, 'items': []}
                    playerValue[str(owner)]['value'] += self.itemDetails[assetId][4]
                    playerValue[str(owner)]['items'].append(assetId)
                else:
                    if updated == self.uaidLog[uaid]['updated']:
                        owner = self.uaidLog[uaid]['owner']
                        if not playerValue.get(str(owner)): playerValue[str(owner)] = {'value': 0, 'items': []}
                        playerValue[str(owner)]['value'] += self.itemDetails[assetId][4]
                        playerValue[str(owner)]['items'].append(assetId)
                        newLog[uaid]['owner'] = owner
                        if self.uaidLog[uaid]['owner']: # user in old log, not in new log -> went private or unbanned
                            potentialBanned.append(owner)
        for player in self.playerValue:
            if player in playerValue:
                if playerValue[player]['value'] <= self.playerValue[player]['value']*0.25:
                    potentialLost.append(player)
            else:
                potentialLost.append(player)
        return playerValue, potentialBanned, potentialLost

    def checkBanned(self, users, bannedUsers):
        for i in range(math.ceil(len(users) / 50)):
            currentUsers = users[i*50 : (i+1)*50]
            responseUsers = None
            while responseUsers == None:
                try:
                    response = requests.post(
                        'https://users.roblox.com/v1/users',
                        timeout = 5, proxies = next(proxies),
                        json = {
                            'userIds': currentUsers,
                            'excludeBannedUsers': True
                        }
                    )
                    if response.status_code == 200:
                        responseUsers = [i['id'] for i in response.json()['data']]
                except:
                    pass
            for user in currentUsers:
                if user not in responseUsers:
                    if str(user) not in self.bannedPlayers:
                        bannedUsers.append(str(user))
                        self.bannedPlayers.append(str(user))

    def checkUnbanned(self, users, unbannedUsers):
        for i in range(math.ceil(len(users) / 50)):
            currentUsers = users[i*50 : (i+1)*50]
            responseUsers = None
            while responseUsers == None:
                try:
                    response = requests.post(
                        'https://users.roblox.com/v1/users',
                        timeout = 5, proxies = next(proxies),
                        json = {
                            'userIds': currentUsers,
                            'excludeBannedUsers': True
                        }
                    )
                    if response.status_code == 200:
                        responseUsers = [i['id'] for i in response.json()['data']]
                except:
                    pass
            for user in responseUsers:
                unbannedUsers.append(str(user))
                self.bannedPlayers.remove(str(user))

    def lastOnline(self, user):
        while 1:
            proxy = next(proxies)
            try:
                response = requests.post(
                    'https://presence.roblox.com/v1/presence/last-online',
                    proxies = proxy,
                    json = {
                        'userIds': [user]
                    }, timeout = 5
                )
                if response.status_code == 200:
                    return response.json()['lastOnlineTimestamps'][0]['lastOnline'].split('T')[0]
            except:
                pass

    def username(self, user):
        while 1:
            proxy = next(proxies)
            try:
                response = requests.get(
                    'https://users.roblox.com/v1/users/%s' % user,
                    proxies = proxy, timeout = 5
                )
                if response.status_code == 200:
                    return response.json()['name']
            except:
                pass

    def userImage(self, user):
        while 1:
            proxy = next(proxies)
            try:
                response = requests.get(
                    'https://thumbnails.roblox.com/v1/users/avatar?userIds=%s&size=250x250&format=Png&isCircular=false' % user,
                    proxies = proxy, timeout = 3
                )
                if response.status_code == 200:
                    return response.json()['data'][0]['imageUrl']
            except:
                pass

    def getLimiteds(self, items):
        counts = Counter(items)
        to_sort = []
        for item in counts:
            if counts[item] > 1:
                to_sort.append(f'(**{self.itemDetails[item][4]}**) **{counts[item]}x** {self.itemDetails[item][0]}')
            else:
                to_sort.append(f'(**{self.itemDetails[item][4]}**) {self.itemDetails[item][0]}')
        to_sort.sort(key=sort_list, reverse=True)
        return '\n'.join(to_sort[0:9])

    def bannedEmbed(self, user, imageURL, lastValue, lastOnline, username, limiteds):
        converted_today = datetime.strptime(self.date, '%Y-%m-%d')
        converted_last = datetime.strptime(lastOnline, '%Y-%m-%d')
        days_ago = (converted_today-converted_last).days
        if days_ago == 0: line = 'today'
        elif days_ago == 1: line = '1 day ago'
        else: line = f'{days_ago} days ago'

        webhook = DiscordWebhook(url='https://discord.com/api/webhooks/1099789478043856896/zBUVmR1IkDrGtNsZmJAiqyVWAJXKmef8NOYtwFvspcZdqQUWuVNwmqLD7Tub42IW2Qln')
        embed = DiscordEmbed(title=f'{username} :grimacing:', url=f'https://www.rolimons.com/player/{user}', color='2360B8')
        embed.set_thumbnail(url=imageURL)
        val = lastValue
        if val: val = "{:,}".format(lastValue)
        embed.set_footer(text='last value is according to rolimons')
        embed.add_embed_field(name='last value', value=f'{val}', inline=True)
        embed.add_embed_field(name='\u200b', value='\u200b', inline=True)
        embed.add_embed_field(name='last online', value=f'{line}', inline=True)
        embed.add_embed_field(name='limiteds (max 10)', value=f'{limiteds}', inline=True)
        webhook.add_embed(embed)
        response = webhook.execute()

    def unbannedEmbed(self, user, imageURL, lastValue, lastOnline, username):
        converted_today = datetime.strptime(self.date, '%Y-%m-%d')
        converted_last = datetime.strptime(lastOnline, '%Y-%m-%d')
        days_ago = (converted_today-converted_last).days
        if days_ago == 0: line = 'today'
        elif days_ago == 1: line = '1 day ago'
        else: line = f'{days_ago} days ago'

        if lastValue: lastValue = "{:,}".format(lastValue)
        else: lastValue = 'unknown'
        webhook = DiscordWebhook(url='https://discord.com/api/webhooks/1140354509516853398/9MUxcvPlQq_5ACY6PbvixnvvDzsqbLuFeCrJb-dp4hU9xhcUiE7mUYppAPYwOLxWWWZm')
        embed = DiscordEmbed(title=f'{username} :smiley:', url=f'https://www.rolimons.com/player/{user}', color='FFA500')
        embed.set_thumbnail(url=imageURL)
        embed.set_footer(text=f"if current value = unknown, private OR not scanned since unban")
        embed.add_embed_field(name='current value', value=f'{lastValue}', inline=True)
        embed.add_embed_field(name='last online', value=f'{line}', inline=True)
        webhook.add_embed(embed)
        response = webhook.execute()

    def uaidThreads(self):
        self.completed = self.total = self.checked = 0
        threads, newLog, copied = [threading.Thread(target=self.title)], {}, limiteds.copy()
        for i in range(50):
            threads.append(threading.Thread(target=self.uaidUpdater, args=[copied, newLog]))
            self.total += 1
        for t in threads: t.start()
        for t in threads: t.join()
        playerValue, potentialBanned, potentialLost = self.analyseLog(newLog)
        self.playerValue, self.uaidLog = playerValue, newLog
        with open('playerValues.json', 'w') as file:
            json.dump(self.playerValue, file, indent=4)
        with open('uaidLog.json', 'w') as file:
            json.dump(self.uaidLog, file, indent=4)
        return potentialBanned, potentialLost

    def checkUserThreads(self, potentialBanned, potentialLost):
        threads, bannedUsers, unbannedUsers = [], [], []
        for i in range(25):
            threads.append(threading.Thread(target=self.checkBanned, args=[potentialBanned[i::25], bannedUsers]))
        for t in threads: t.start()
        for t in threads: t.join()
        self.evalUsers(bannedUsers, 'banned')
        threads = []
        for i in range(25):
            threads.append(threading.Thread(target=self.checkUnbanned, args=[self.bannedPlayers[i::25], unbannedUsers]))
        for t in threads: t.start()
        for t in threads: t.join()
        self.evalUsers(unbannedUsers, 'unbanned')
        print(len(bannedUsers), len(unbannedUsers))
        with open('txts/banned.txt', 'w') as file:
            file.writelines('\n'.join(self.bannedPlayers))

    def evalUsers(self, users, type):
        for user in users:
            self.date = str(datetime.now()).split(' ')[0]
            lastValue = self.playerValue[user]['value'] if user in self.playerValue else None
            lastOnline = self.lastOnline(user)
            imageURL = self.userImage(user)
            username = self.username(user)
            limiteds = self.getLimiteds(self.playerValue[user]['items'])
            if type == 'banned':
                self.bannedEmbed(user, imageURL, lastValue, lastOnline, username, limiteds)
            else:
                self.unbannedEmbed(user, imageURL, lastValue, lastOnline, username)

    def main(self):
        threading.Thread(target=self.updateRoli).start()
        while 1:
            pb, pl = self.uaidThreads()
            print(len(pb), len(pl))
            self.checkUserThreads(pb, pl)

Bot()
