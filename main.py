import requests
import os
import random
import time
from datetime import datetime, timedelta, timezone
from log import logging
from discord_webhook import DiscordWebhook, DiscordEmbed

class GameAccount:
    def __init__(self, game_biz, region_name, game_uid, level, nickname, region, **kwargs):
        self.game_biz = game_biz
        self.region_name = region_name.split(" ")[0]
        self.game_uid = game_uid
        self.level = level
        self.nickname = nickname
        self.region = region

class CheckInInfo:
    def __init__(self, is_sign, total_sign_day, **kwargs):
        self.is_sign = is_sign
        self.total_sign_day = total_sign_day

class Reward:
    def __init__(self, name, cnt, icon, **kwargs):
        self.name = name
        self.cnt = cnt
        self.icon = icon

class HoyolabClient:
    def __init__(self, cookie):
        self.cookie = cookie
        self.session = requests.Session()
        self.headers = {
            "Cookie": self.cookie,
            "User-Agent": os.environ.get("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47"),
            "Referer": "https://act.hoyolab.com/",
            "Origin": "https://act.hoyolab.com/",
            "Accept-Encoding": "gzip, deflate, br"
        }

    def request(self, url):
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status() 
            data = response.json()
            
            if "retcode" not in data or "data" not in data:
                raise Exception(f"Unexpected JSON format from {url}")
            
            return data
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
            return None 

    def verify_cookie(self):
        url = "https://api-account-os.hoyolab.com/auth/api/getUserAccountInfoByLToken"
        res = self.request(url)
        if not res or res["retcode"] != 0:
            raise Exception("Invalid cookie")

    def get_game_accounts(self):
        logging.info("Scanning for Hoyoverse game account")
        url = "https://api-os-takumi.hoyolab.com/binding/api/getUserGameRolesByCookie"
        res = self.request(url)
        if not res or "data" not in res or "list" not in res["data"]:
            logging.error(f"Unexpected JSON format from {url}")
            return []

        accounts = [GameAccount(**account) for account in res["data"]["list"]]
        return accounts

    def check_in(self, account):
        game_data = {
            "hk4e_global": {
                "game_name": "Genshin Impact",
                "main": "Traveller",
                "act_id": "e202102251931481",
                "info_url": "https://sg-hk4e-api.hoyolab.com/event/sol/info",
                "reward_url": "https://sg-hk4e-api.hoyolab.com/event/sol/home",
                "sign_url": "https://sg-hk4e-api.hoyolab.com/event/sol/sign"
            },
            "hkrpg_global": {
                "game_name": "Honkai: Star Rail",
                "main": "Trailblazer",
                "act_id": "e202303301540311",
                "info_url": "https://sg-public-api.hoyolab.com/event/luna/hkrpg/os/info",
                "reward_url": "https://sg-public-api.hoyolab.com/event/luna/hkrpg/os/home",
                "sign_url": "https://sg-public-api.hoyolab.com/event/luna/hkrpg/os/sign"
            },
            "nap_global": {
                "game_name": "Zenless Zone Zero",
                "main": "Phaethon",
                "act_id": "e202406031448091",
                "info_url": "https://sg-act-nap-api.hoyolab.com/event/luna/zzz/os/info",
                "reward_url": "https://sg-act-nap-api.hoyolab.com/event/luna/zzz/os/home",
                "sign_url": "https://sg-act-nap-api.hoyolab.com/event/luna/zzz/os/sign"
            },
        }

        if account.game_biz not in game_data:
            raise Exception(f"Unsupported game")

        data = game_data[account.game_biz]
        act_id = data["act_id"]

        logging.info("Fetch account detail from Hoyoverse ...")
        info_res = self.request(f"{data['info_url']}?act_id={act_id}")
        if not info_res or "data" not in info_res:
            logging.error(f"Unexpected JSON format from {data['info_url']}")
            return

        logging.info("Fetch daily login reward from Hoyoverse ..")
        rewards_res = self.request(f"{data['reward_url']}?act_id={act_id}")
        if not rewards_res or "data" not in rewards_res or "awards" not in rewards_res["data"]:
            logging.error(f"Unexpected JSON format from {data['reward_url']}")
            return

        info = CheckInInfo(**info_res["data"])
        rewards = [Reward(**reward) for reward in rewards_res["data"]["awards"]]

        if not info.is_sign:
            try:
                logging.info("Sign-in to server and claim reward.")
                sign_res = self.session.post(f"{data['sign_url']}?act_id={act_id}", headers=self.headers)
                sign_res.raise_for_status() 
                sign_res_json = sign_res.json()
                if "retcode" not in sign_res_json or sign_res_json["retcode"] != 0:
                    raise Exception(f"Failed to check in: {sign_res_json.get('message', 'Unknown error')}")
                
                reward = rewards[info.total_sign_day]
                account.claimed_reward = reward
                account.game_name = data["game_name"]
                logging.info(f"Check-in result for {account.nickname}: {reward.name} x {reward.cnt}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Check-in request failed for {account.nickname}: {e}")
                return
        else:
            logging.info(f"{data['main']}, You've already checked in today.")


def send_discord_notification(webhook_url, account, reward):
    if not webhook_url:
        return

    webhook = DiscordWebhook(url=webhook_url)
    embed = DiscordEmbed(title=f"{account.game_name} Daily Check In", color="03b2f8")
    embed.set_author(
        name="Doctor Who Need",
        icon_url="https://media.discordapp.net/attachments/998960103766118503/1275905124102836306/idk-if-this-detail-about-dr-ratios-pose-is-true-but-here-v0-ynulkoybl7cc1.png?ex=66c796be&is=66c6453e&hm=cfff14c15e52d63a4dd089ec20fbc6f314d89f96842665e9bae78484c7ebd8e9&"
    )
    embed.set_thumbnail(url=reward.icon)
    embed.add_embed_field(name="UID", value=account.game_uid)
    embed.add_embed_field(name="Level", value=account.level)
    embed.add_embed_field(name="Name", value=account.nickname)
    embed.add_embed_field(name="Server", value=account.region_name)
    embed.add_embed_field(name="Reward", value=f"{reward.name} x {reward.cnt}")
    embed.set_footer(text="Hoyolab Auto Check-in")
    embed.set_timestamp()
    webhook.add_embed(embed)

    try:
        response = webhook.execute()
        if response.status_code != 200:
            logging.error(f"Failed to send Discord notification: {response.status_code} {response.content}")
    except Exception as e:
        logging.error(f"Failed to send Discord notification: {e}")

def check_in(client, accounts, webhook_url):
    for account in accounts:
        try:
            client.check_in(account)
            if webhook_url and hasattr(account, 'claimed_reward'):
                send_discord_notification(webhook_url, account, account.claimed_reward)
        except Exception as e:
            logging.error(f"Check-in failed for {account.nickname}: {e}")

def wait():
    now_utc = datetime.now(timezone(timedelta(0)).utc)

    start_time_utc = now_utc.replace(hour=5, minute=0, second=0, microsecond=0)
    end_time_utc = now_utc.replace(hour=22, minute=0, second=0, microsecond=0)

    if start_time_utc <= now_utc <= end_time_utc:
        next_check_in_time = now_utc + timedelta(hours=23)
        wait_time = (next_check_in_time - now_utc).total_seconds()
    elif now_utc < start_time_utc:
        wait_time = (start_time_utc - now_utc).total_seconds()
    else:
        next_check_in_time = (now_utc + timedelta(days=1)).replace(hour=5, minute=0, second=0, microsecond=0)
        wait_time = (next_check_in_time - now_utc).total_seconds()

    random_minutes = random.randint(0, 59)
    random_seconds = random.randint(0, 59)
    wait_time += random_minutes * 60 + random_seconds

    logging.info(f"Waiting for {wait_time} seconds before next check-in...")
    time.sleep(wait_time)

def run():
    logging.info("Hoyolab Auto Daily Check-in Starting ...")

    cookie = os.environ.get("COOKIE")
    if not cookie:
        raise Exception("COOKIE environment variable not set")

    webhook_url = os.environ.get("DISCORD_WEBHOOK")

    cookies = cookie.split('#')

    while True:
        for i, cookie in enumerate(cookies):
            logging.info(f"Processing account {i + 1} of {len(cookies)}")

            client = HoyolabClient(cookie)

            try:
                client.verify_cookie()
            except Exception as e:
                logging.error(f"Invalid cookie for account {i + 1}: {e}")
                continue

            accounts = client.get_game_accounts()
            check_in(client, accounts, webhook_url)
        
        wait()

run()