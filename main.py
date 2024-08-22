import requests
import os
import random
import time
from datetime import datetime, timedelta, timezone
from log import logging
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv

load_dotenv()

GAME_DATA = {
    "hk4e_global": {
        "game_name": "Genshin Impact",
        "main": "Traveler",
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

class GameAccount:
    def __init__(self, game_biz, region_name, game_uid, level, nickname, region, **kwargs):
        self._game_biz = game_biz
        self._region_name = region_name.split(" ")[0]
        self._game_uid = game_uid
        self._level = level
        self._nickname = nickname
        self._region = region
        self.claimed_reward = None

    def get_game_biz(self):
        return self._game_biz

    def get_region_name(self):
        return self._region_name

    def get_game_uid(self):
        return self._game_uid

    def get_level(self):
        return self._level

    def get_nickname(self):
        return self._nickname

    def get_region(self):
        return self._region

    def get_claimed_reward(self):
        return self.claimed_reward

class CheckInInfo:
    def __init__(self, is_sign, total_sign_day, **kwargs):
        self._is_sign = is_sign
        self._total_sign_day = total_sign_day

    def is_signed_in(self):
        return self._is_sign

    def get_total_sign_day(self):
        return self._total_sign_day

class Reward:
    def __init__(self, name, cnt, icon, **kwargs):
        self._name = name
        self._cnt = cnt
        self._icon = icon
        self.game_name = None

    def get_name(self):
        return self._name

    def get_cnt(self):
        return self._cnt

    def get_icon(self):
        return self._icon
    
    def get_game_name(self):
        return self.game_name

class ApiClient:
    def __init__(self, headers):
        self.session = requests.Session()
        self.headers = headers

    def _request(self, url):
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

    def _check_json_format(self, data, url, required_fields):
        for field in required_fields:
            if isinstance(field, str):
                if field not in data:
                    logging.error(f"Unexpected JSON format from {url}: Missing field '{field}'")
                    return False
            elif isinstance(field, list):
                if not self._check_json_format(data.get(field[0]), url, field[1:]):
                    return False

        return True

class HoyolabClient(ApiClient):
    def __init__(self, cookie):
        headers = {
            "Cookie": cookie,
            "User-Agent": os.environ.get("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47"),
            "Referer": "https://act.hoyolab.com/",
            "Origin": "https://act.hoyolab.com/",
            "Accept-Encoding": "gzip, deflate, br"
        }
        super().__init__(headers)
        self.cookie = cookie

    def verify_cookie(self):
        url = "https://api-account-os.hoyolab.com/auth/api/getUserAccountInfoByLToken"
        res = self._request(url)
        if not res or res["retcode"] != 0:
            raise Exception("Invalid cookie")

    def get_game_accounts(self):
        logging.info("Scanning for Hoyoverse game account")
        url = "https://api-os-takumi.hoyolab.com/binding/api/getUserGameRolesByCookie"
        res = self._request(url)
        if not self._check_json_format(res, url, ["data", ["list"]]):
            return []

        accounts = [GameAccount(**account) for account in res["data"]["list"]]
        return accounts

    def check_in(self, account):
        if account.get_game_biz() not in GAME_DATA:
            raise Exception(f"Unsupported game")

        data = GAME_DATA[account.get_game_biz()]
        act_id = data["act_id"]

        logging.info("Fetch account detail from Hoyoverse ...")
        info_res = self._request(f"{data['info_url']}?act_id={act_id}")
        if not self._check_json_format(info_res, data["info_url"], ["data"]):
            return

        logging.info("Fetch daily login reward from Hoyoverse ..")
        rewards_res = self._request(f"{data['reward_url']}?act_id={act_id}")
        if not self._check_json_format(rewards_res, data["reward_url"], ["data", ["awards"]]):
            return

        info = CheckInInfo(**info_res["data"])
        rewards = [Reward(**reward) for reward in rewards_res["data"]["awards"]]

        if not info.is_signed_in():
            try:
                logging.info("Sign-in to server and claim reward.")
                sign_res = self.session.post(f"{data['sign_url']}?act_id={act_id}", headers=self.headers)
                sign_res.raise_for_status()
                sign_res_json = sign_res.json()
                if "retcode" not in sign_res_json or sign_res_json["retcode"] != 0:
                    raise Exception(f"Failed to check in: {sign_res_json.get('message', 'Unknown error')}")

                reward = rewards[info.get_total_sign_day()]
                reward.game_name = data["game_name"]
                account.claimed_reward = reward
                logging.info(f"Check-in result for {account.get_nickname()}: {reward.get_name()} x {reward.get_cnt()}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Check-in request failed for {account.get_nickname()}: {e}")
                return
        else:
            logging.info(f"You've already checked in today, {data['main']}~")

def send_discord_notification(webhook_url, account, reward):
    if not webhook_url:
        return

    webhook = DiscordWebhook(url=webhook_url)
    embed = DiscordEmbed(title=f"{reward.get_game_name()} Daily Check In", color="03b2f8")
    embed.set_author(
        name="Doctor Who Need",
        icon_url="https://media.discordapp.net/attachments/998960103766118503/1275905124102836306/idk-if-this-detail-about-dr-ratios-pose-is-true-but-here-v0-ynulkoybl7cc1.png?ex=66c796be&is=66c6453e&hm=cfff14c15e52d63a4dd089ec20fbc6f314d89f96842665e9bae78484c7ebd8e9&"
    )
    embed.set_thumbnail(url=reward.get_icon())
    embed.add_embed_field(name="UID", value=account.get_game_uid())
    embed.add_embed_field(name="Level", value=account.get_level())
    embed.add_embed_field(name="Name", value=account.get_nickname())
    embed.add_embed_field(name="Server", value=account.get_region_name())
    embed.add_embed_field(name="Reward", value=f"{reward.get_name()} x {reward.get_cnt()}")
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
            if webhook_url and account.get_claimed_reward():
                send_discord_notification(webhook_url, account, account.get_claimed_reward())
        except Exception as e:
            logging.error(f"Check-in failed for {account.get_nickname()}: {e}")

def wait():
    now_local = datetime.now()

    start_time_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time_local = now_local.replace(hour=5, minute=0, second=0, microsecond=0)

    if start_time_local <= now_local <= end_time_local:
        next_check_in_time = now_local + timedelta(hours=23)
        wait_time = (next_check_in_time - now_local).total_seconds()
    elif now_local < start_time_local:
        wait_time = (start_time_local - now_local).total_seconds()
    else:
        next_check_in_time = (now_local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_time = (next_check_in_time - now_local).total_seconds()

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
            
            try:
                accounts = client.get_game_accounts()
                check_in(client, accounts, webhook_url)
            except Exception as e:
                logging.error(f"Check-in failed: {e}")
                continue
        
        wait()

run()