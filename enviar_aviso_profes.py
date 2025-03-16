import json
from pathlib import Path
import requests
from dotenv import load_dotenv
import os
import sys

MAX_MENTIONS = 15

teachers_id_path = Path(__file__).parent / "teachers.json"
teachers_to_mention_path = Path(__file__).parent / "teachers_to_mention.txt"
guardar_profes_path = Path(__file__).parent / "guardar_profes.py"

extDataDir = os.getcwd()
if getattr(sys, 'frozen', False):
    extDataDir = sys._MEIPASS
    load_dotenv(dotenv_path = os.path.join(extDataDir, '.env'))
else:
    load_dotenv()

def read_teachers_from_file():
    try:
        with open(teachers_id_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # print("Se va a crear el fichero teachers.json, por favor, vuelve a ejecutar este programa.")           
        with open(guardar_profes_path, "r") as f:                 
            exec(f.read())              
        # print("No se ha encontrado el fichero guardar_profes.py.")            
        exit()        

def check_teachers_id(teachers_id, teachers_to_mention):
    isOk = True
    teachers_bad_names = ""
    for teacher in teachers_to_mention.split('\n'):    
        try:          
            if teacher.replace('\n','').strip() != "":
                result = teachers_id[teacher.replace('\n','').strip()]
        except KeyError as e:               
            teachers_bad_names += f"{teacher}\n"    
            isOk = False
    return isOk, teachers_bad_names


def teacher_id(teacherName, teachers_id):
    result = teachers_id[teacherName.replace('\n','').strip()]
    return f"<@{result}>\n"
            


def set_payloads(teachers:str):
    teachers_id = read_teachers_from_file()
    payloads = []
    i = -1
    iter = 0
    for teacher in teachers.split('\n'):        
        try:
            if iter >= MAX_MENTIONS:
                payloads.append(teacher_id(teacher,teachers_id))
                i += 1
                iter = 0
            else:
                payloads[i] += teacher_id(teacher,teachers_id) 
                iter += 1       
        except IndexError:    
            payloads.append(teacher_id(teacher,teachers_id)) 
            iter += 1
            i += 1
    return payloads  

def send_payloads(data, hora):
    # Datos para la request
    url = f"https://discord.com/api/v9/channels/{os.getenv("CHANNEL_CODING_GIANTS")}/messages"

    headers = {
        "Authorization" : "Bot " + os.getenv("BOT_TOKEN"),
        'Content-Type': 'application/json'
    }    
    payload_content = data

    check, bad_names = check_teachers_id(read_teachers_from_file(), payload_content)
    if not check:
        raise KeyError(f"Error en la lista de profesores a mencionar:\n{bad_names}")

    payloads = set_payloads(payload_content) 
    for p in range(len(payloads)):
        payload = {
            "content": f"Buena clase a las {hora} ({p + 1}/{len(payloads)}):\n{payloads[p]}"
        }
        # print(payload["content"]) 
        try:
            res = requests.post(url, json = payload, headers= headers)
            res.raise_for_status()            
            pass
        except requests.HTTPError as ex:
            raise ex            
        except TimeoutError:            
            exit()  
    