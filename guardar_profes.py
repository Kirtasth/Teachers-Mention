import json
from pathlib import Path
import discord
from jsonmerge import merge
from dotenv import load_dotenv
import os
import sys

test_all_members = {}

extDataDir = os.getcwd()
if getattr(sys, 'frozen', False):
    extDataDir = sys._MEIPASS
    load_dotenv(dotenv_path=os.path.join(extDataDir, '.env'))
    teachers_id_path = os.path.join(extDataDir, "teachers.json")
else:
    load_dotenv()
    teachers_id_path = Path(__file__).parent / "teachers.json"


intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents = intents)

@client.event
async def on_ready():        
    for guild in client.guilds:
        if guild.id == int(os.getenv("GUILD_ID")):            
            async for member in guild.fetch_members():                
                if not member.bot:                    
                    test_all_members[str(member.display_name)] = member.id                                                                                                                                                                    
            save_teachers(test_all_members)            
    await client.close()    


def save_teachers(teachers):    
    try:        
        old_data_teachers = None
        with open(teachers_id_path, "r", encoding = "utf-8") as fr:
            old_data_teachers = json.load(fr)
            fr.close()
        
        if old_data_teachers is not None:
            with open(teachers_id_path, "w+", encoding = "utf-8") as fw:                 
                res = merge(teachers, old_data_teachers)                            
                json.dump(res, fw, ensure_ascii=False)                    
                fw.close()                           
    except FileNotFoundError:        
        with open(teachers_id_path, "w+", encoding = "utf-8") as fw:
            json.dump(teachers, fw, ensure_ascii=False)
            fw.close()

def run_discord_bot():
    client.run(os.getenv("BOT_TOKEN"))
