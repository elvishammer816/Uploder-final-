import random #NIKHIL SAINI BOTS
import time #NIKHIL SAINI BOTS
import math #NIKHIL SAINI BOTS
import os
import re
import time
import mmap
import datetime
import aiohttp
import aiofiles
import asyncio
import logging
import requests
import tgcrypto
import subprocess
import concurrent.futures
from math import ceil
from utils import progress_bar
from pyrogram import Client, filters
from pyrogram.types import Message
from io import BytesIO
from pathlib import Path  
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode
import globals

def duration(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)

def get_mps_and_keys(api_url):
    response = requests.get(api_url)
    response_json = response.json()
    mpd = response_json.get('MPD')
    keys = response_json.get('KEYS')
    return mpd, keys

def get_mps_and_keys2(api_url):
    response = requests.get(api_url) 
    response_json = response.json()
    mpd = response_json.get('mpd_url')
    keys = response_json.get('keys')
    return mpd, keys
    
def get_mps_and_keys3(api_url):
    response = requests.get(api_url)   
    response_json = response.json()
    mpd = response_json.get('url')
    return mpd

def fetch_classplus_token(email: str = None, password: str = None, login_url: str = None):
    """
    Attempt to auto-generate/fetch the Classplus token using email/password.
    Priority of credentials:
      1) Function arguments (email, password, login_url)
      2) Environment variables (CLASSPLUS_EMAIL, CLASSPLUS_PASSWORD, CLASSPLUS_LOGIN_URL)

    Expected response JSON shape: {"token": "<value>"} or {"access_token": "<value>"} or {"data": {"token": "<value>"}}.
    On success, updates globals.cptoken and returns the token string; otherwise returns None.
    """
    email = email or os.getenv("CLASSPLUS_EMAIL", "")
    password = password or os.getenv("CLASSPLUS_PASSWORD", "")
    login_url = login_url or os.getenv("CLASSPLUS_LOGIN_URL", "https://web.classplusapp.com/api/login")

    if not email or not password:
        return None

    try:
        payload = {"email": email, "password": password}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": "https://web.classplusapp.com/",
            "User-Agent": "Mozilla/5.0"
        }
        resp = requests.post(login_url, json=payload, headers=headers, timeout=20)
        if resp.status_code != 200:
            return None
        data = resp.json()
        token = data.get("token") or data.get("access_token") or data.get("data", {}).get("token")
        if token:
            globals.cptoken = token
            return token
        return None
    except Exception:
        return None
    except Exception:
        return None

def exec(cmd):
        process = subprocess.run(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output = process.stdout.decode()
        print(output)
        return output
        #err = process.stdout.decode()

def pull_run(work, cmds):
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        print("Waiting for tasks to complete")
        fut = executor.map(exec,cmds)
        
async def aio(url,name):
    k = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(k, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return k


async def download(url,name):
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(ka, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return ka

def parse_vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = []
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",2)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.append((i[0], i[2]))
            except:
                pass
    return new_info

def vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = dict()
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",3)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    
                    # temp.update(f'{i[2]}')
                    # new_info.append((i[2], i[0]))
                    #  mp4,mkv etc ==== f"({i[1]})" 
                    
                    new_info.update({f'{i[2]}':f'{i[0]}'})

            except:
                pass
    return new_info


async def decrypt_and_merge_video(mpd_url, keys_string, output_path, output_name, quality="720"):
    try:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        cmd1 = f'yt-dlp -f "bv[height<={quality}]+ba/b" -o "{output_path}/file.%(ext)s" --allow-unplayable-format --no-check-certificate --external-downloader aria2c "{mpd_url}"'
        print(f"Running command: {cmd1}")
        os.system(cmd1)
        
        avDir = list(output_path.iterdir())
        print(f"Downloaded files: {avDir}")
        print("Decrypting")

        video_decrypted = False
        audio_decrypted = False

        for data in avDir:
            if data.suffix == ".mp4" and not video_decrypted:
                cmd2 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/video.mp4"'
                print(f"Running command: {cmd2}")
                os.system(cmd2)
                if (output_path / "video.mp4").exists():
                    video_decrypted = True
                data.unlink()
            elif data.suffix == ".m4a" and not audio_decrypted:
                cmd3 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/audio.m4a"'
                print(f"Running command: {cmd3}")
                os.system(cmd3)
                if (output_path / "audio.m4a").exists():
                    audio_decrypted = True
                data.unlink()

        if not video_decrypted or not audio_decrypted:
            raise FileNotFoundError("Decryption failed: video or audio file not found.")

        cmd4 = f'ffmpeg -i "{output_path}/video.mp4" -i "{output_path}/audio.m4a" -c copy "{output_path}/{output_name}.mp4"'
        print(f"Running command: {cmd4}")
        os.system(cmd4)
        if (output_path / "video.mp4").exists():
            (output_path / "video.mp4").unlink()
        if (output_path / "audio.m4a").exists():
            (output_path / "audio.m4a").unlink()
        
        filename = output_path / f"{output_name}.mp4"

        if not filename.exists():
            raise FileNotFoundError("Merged video file not found.")

        cmd5 = f'ffmpeg -i "{filename}" 2>&1 | grep "Duration"'
        duration_info = os.popen(cmd5).read()
        print(f"Duration info: {duration_info}")

        return str(filename)

    except Exception as e:
        print(f"Error during decryption and merging: {str(e)}")
        raise

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if proc.returncode == 1:
        return False
    if stdout:
        return f'[stdout]\n{stdout.decode()}'
    if stderr:
        return f'[stderr]\n{stderr.decode()}'

    
def old_download(url, file_name, chunk_size = 1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name

def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"


async def download_video(url,cmd, name):
    download_cmd = f'{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32"'
    global failed_counter
    print(download_cmd)
    logging.info(download_cmd)
    k = subprocess.run(download_cmd, shell=True)
    if "visionias" in cmd and k.returncode != 0 and failed_counter <= 10:
        failed_counter += 1
        await asyncio.sleep(5)
        await download_video(url, cmd, name)
    failed_counter = 0
    try:
        if os.path.isfile(name):
            return name
        elif os.path.isfile(f"{name}.webm"):
            return f"{name}.webm"
        name = name.split(".")[0]
        if os.path.isfile(f"{name}.mkv"):
            return f"{name}.mkv"
        elif os.path.isfile(f"{name}.mp4"):
            return f"{name}.mp4"
        elif os.path.isfile(f"{name}.mp4.webm"):
            return f"{name}.mp4.webm"

        return name
    except FileNotFoundError as exc:
        return os.path.isfile.splitext[0] + "." + "mp4"


async def send_doc(bot: Client, m: Message, cc, ka, cc1, prog, count, name, channel_id):
    reply = await bot.send_message(channel_id, f"Downloading pdf:\n<pre><code>{name}</code></pre>")
    time.sleep(1)
    start_time = time.time()
    await bot.send_document(ka, caption=cc1)
    count+=1
    await reply.delete (True)
    time.sleep(1)
    os.remove(ka)
    time.sleep(3) 

def decrypt_file(file_path, key):  
    if not os.path.exists(file_path): 
        return False  

    with open(file_path, "r+b") as f:  
        num_bytes = min(28, os.path.getsize(file_path))  
        with mmap.mmap(f.fileno(), length=num_bytes, access=mmap.ACCESS_WRITE) as mmapped_file:  
            for i in range(num_bytes):  
                mmapped_file[i] ^= ord(key[i]) if i < len(key) else i 
    return True  

async def download_and_decrypt_video(url, cmd, name, key):  
    video_path = await download_video(url, cmd, name)  
    
    if video_path:  
        decrypted = decrypt_file(video_path, key)  
        if decrypted:  
            print(f"File {video_path} decrypted successfully.")  
            return video_path  
        else:  
            print(f"Failed to decrypt {video_path}.")  
            return None  

async def send_vid(bot: Client, m: Message, cc, filename, vidwatermark, thumb, name, prog, channel_id):
    subprocess.run(f'ffmpeg -i "{filename}" -ss 00:00:10 -vframes 1 "{filename}.jpg"', shell=True)
    await prog.delete (True)
    reply1 = await bot.send_message(channel_id, f"**📩 Uploading Video 📩:-**\n<blockquote>**{name}**</blockquote>")
    reply = await m.reply_text(f"**Generate Thumbnail:**\n<blockquote>**{name}**</blockquote>")
    try:
        if thumb == "/d":
            thumbnail = f"{filename}.jpg"
        else:
            thumbnail = thumb  
        
        if vidwatermark == "/d":
            w_filename = f"{filename}"
        else:
            w_filename = f"w_{filename}"
            font_path = "vidwater.ttf"
            subprocess.run(
                f'ffmpeg -i "{filename}" -vf "drawtext=fontfile={font_path}:text=\'{vidwatermark}\':fontcolor=white@0.3:fontsize=h/6:x=(w-text_w)/2:y=(h-text_h)/2" -codec:a copy "{w_filename}"',
                shell=True
            )
            
    except Exception as e:
        await m.reply_text(str(e))

    dur = int(duration(w_filename))
    start_time = time.time()

    try:
        await bot.send_video(channel_id, w_filename, caption=cc, supports_streaming=True, height=720, width=1280, thumb=thumbnail, duration=dur, progress=progress_bar, progress_args=(reply, start_time))
    except Exception:
        await bot.send_document(channel_id, w_filename, caption=cc, progress=progress_bar, progress_args=(reply, start_time))
    os.remove(w_filename)
    await reply.delete(True)
    await reply1.delete(True)
    os.remove(f"{filename}.jpg") #NIKHIL SAINI BOTS
from vars import CREDIT #NIKHIL SAINI BOTS
from pyrogram.errors import FloodWait #NIKHIL SAINI BOTS
from datetime import datetime,timedelta #NIKHIL SAINI BOTS

class Timer: #NIKHIL SAINI BOTS
    def __init__(self, time_between=5): #NIKHIL SAINI BOTS
        self.start_time = time.time() #NIKHIL SAINI BOTS
        self.time_between = time_between #NIKHIL SAINI BOTS

    def can_send(self): #NIKHIL SAINI BOTS
        if time.time() > (self.start_time + self.time_between): #NIKHIL SAINI BOTS
            self.start_time = time.time() #NIKHIL SAINI BOTS
            return True #NIKHIL SAINI BOTS
        return False #NIKHIL SAINI BOTS

#lets do calculations #NIKHIL SAINI BOTS
def hrb(value, digits= 2, delim= "", postfix=""): #NIKHIL SAINI BOTS
    """Return a human-readable file size. #NIKHIL SAINI BOTS
    """ #NIKHIL SAINI BOTS
    if value is None: #NIKHIL SAINI BOTS
        return None #NIKHIL SAINI BOTS
    chosen_unit = "B" #NIKHIL SAINI BOTS
    for unit in ("KB", "MB", "GB", "TB"): #NIKHIL SAINI BOTS
        if value > 1000: #NIKHIL SAINI BOTS
            value /= 1024 #NIKHIL SAINI BOTS
            chosen_unit = unit #NIKHIL SAINI BOTS
        else: #NIKHIL SAINI BOTS
            break #NIKHIL SAINI BOTS
    return f"{value:.{digits}f}" + delim + chosen_unit + postfix #NIKHIL SAINI BOTS

def hrt(seconds, precision = 0): #NIKHIL SAINI BOTS
    """Return a human-readable time delta as a string. #NIKHIL SAINI BOTS
    """ #NIKHIL SAINI BOTS
    pieces = [] #NIKHIL SAINI BOTS
    value = timedelta(seconds=seconds) #NIKHIL SAINI BOTS

    if value.days: #NIKHIL SAINI BOTS
        pieces.append(f"{value.days}day") #NIKHIL SAINI BOTS

    seconds = value.seconds #NIKHIL SAINI BOTS

    if seconds >= 3600: #NIKHIL SAINI BOTS
        hours = int(seconds / 3600) #NIKHIL SAINI BOTS
        pieces.append(f"{hours}hr") #NIKHIL SAINI BOTS
        seconds -= hours * 3600 #NIKHIL SAINI BOTS

    if seconds >= 60: #NIKHIL SAINI BOTS
        minutes = int(seconds / 60) #NIKHIL SAINI BOTS
        pieces.append(f"{minutes}min") #NIKHIL SAINI BOTS
        seconds -= minutes * 60 #NIKHIL SAINI BOTS

    if seconds > 0 or not pieces: #NIKHIL SAINI BOTS
        pieces.append(f"{seconds}sec") #NIKHIL SAINI BOTS

    if not precision: #NIKHIL SAINI BOTS
        return "".join(pieces) #NIKHIL SAINI BOTS

    return "".join(pieces[:precision]) #NIKHIL SAINI BOTS

timer = Timer() #NIKHIL SAINI BOTS

async def progress_bar(current, total, reply, start): #NIKHIL SAINI BOTS
    if timer.can_send(): #NIKHIL SAINI BOTS
        now = time.time() #NIKHIL SAINI BOTS
        diff = now - start #NIKHIL SAINI BOTS
        if diff < 1: #NIKHIL SAINI BOTS
            return #NIKHIL SAINI BOTS
        else: #NIKHIL SAINI BOTS
            perc = f"{current * 100 / total:.1f}%" #NIKHIL SAINI BOTS
            elapsed_time = round(diff) #NIKHIL SAINI BOTS
            speed = current / elapsed_time #NIKHIL SAINI BOTS
            remaining_bytes = total - current #NIKHIL SAINI BOTS
            if speed > 0: #NIKHIL SAINI BOTS
                eta_seconds = remaining_bytes / speed #NIKHIL SAINI BOTS
                eta = hrt(eta_seconds, precision=1) #NIKHIL SAINI BOTS
            else: #NIKHIL SAINI BOTS
                eta = "-" #NIKHIL SAINI BOTS
            sp = str(hrb(speed)) + "/s" #NIKHIL SAINI BOTS
            tot = hrb(total) #NIKHIL SAINI BOTS
            cur = hrb(current) #NIKHIL SAINI BOTS
            bar_length = 10 #NIKHIL SAINI BOTS
            completed_length = int(current * bar_length / total) #NIKHIL SAINI BOTS
            remaining_length = bar_length - completed_length #NIKHIL SAINI BOTS

            symbol_pairs = [ #NIKHIL SAINI BOTS
                #("🟢", "⚪"), #NIKHIL SAINI BOTS
                #("⚫", "⚪"), #NIKHIL SAINI BOTS
                #("🔵", "⚪"), #NIKHIL SAINI BOTS
                #("🔴", "⚪"), #NIKHIL SAINI BOTS
                #("🔘", "⚪"), #NIKHIL SAINI BOTS
                ("🟩", "⬜") #NIKHIL SAINI BOTS
            ] #NIKHIL SAINI BOTS
            chosen_pair = random.choice(symbol_pairs) #NIKHIL SAINI BOTS
            completed_symbol, remaining_symbol = chosen_pair #NIKHIL SAINI BOTS

            progress_bar = completed_symbol * completed_length + remaining_symbol * remaining_length #NIKHIL SAINI BOTS

            try: #NIKHIL SAINI BOTS
                #await reply.edit(f'`╭──⌯═════𝐔𝐩𝐥𝐨𝐚𝐝𝐢𝐧𝐠══════⌯──╮\n├⚡ {progress_bar}\n├⚙️ Progress ➤ | {perc} |\n├🚀 Speed ➤ | {sp} |\n├📟 Processed ➤ | {cur} |\n├🧲 Size ➤ | {tot} |\n├🕑 ETA ➤ | {eta} |\n╰─═══✨🦋𝙎𝘼𝙄𝙉𝙄 𝘽𝙊𝙏𝙎🦋✨═══─╯`') 
                await reply.edit(f'<blockquote>`╭──⌯═════𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐢𝐜𝐬══════⌯──╮\n├⚡ {progress_bar}\n├⚙️ Progress ➤ | {perc} |\n├🚀 Speed ➤ | {sp} |\n├📟 Processed ➤ | {cur} |\n├🧲 Size ➤ | {tot} |\n├🕑 ETA ➤ | {eta} |\n╰─═══✨🦋{CREDIT}🦋✨═══─╯`</blockquote>') 
            except FloodWait as e: #NIKHIL SAINI BOTS
                time.sleep(e.x) #NIKHIL SAINI BOTS 
