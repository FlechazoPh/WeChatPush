# coding=utf-8

import os
import sys
from datetime import datetime
from urllib import request, parse

def prt(mes):
    print(str(datetime.now().strftime('[%Y.%m.%d %H:%M:%S] ')) + str(mes))


if int(sys.version_info.major) < 3:
    prt('程序仅支持Python3.4及以上版本运行，程序强制停止运行')
    os._exit(0)

import signal
import requests
import importlib
import traceback
import platform
import time
import json
from requests.packages import urllib3
from multiprocessing import Process, Manager
import subprocess
import base64

local_dir = str((os.path.split(os.path.realpath(__file__))[0]).replace('\\', '/'))
errorlog_clean = open(local_dir + '/error.log', 'w').close()
ppid = os.getppid()
pid = os.getpid()


def error_log(local):
    with open(local + '/error.log', 'a', encoding='utf-8') as f:
        f.write(str(datetime.now().strftime('[%Y.%m.%d %H:%M:%S] ')) + str(traceback.format_exc()) + '\n')
    prt('程序运行出现错误,错误信息已保存至程序目录下的error.log文件中')


try:
    import config
except:
    prt("读取配置文件异常,程序终止运行,请检查配置文件是否存在或语法是否有问题")
    error_log(local_dir)
    os._exit(0)

if int(config.async_components):
    import asyncio
    run_as_async = 1
else:
    run_as_async = 0

import itchat.content


def error(pid, ppid, errorlog_dir):
    error_log(errorlog_dir)
    prt('程序终止运行')
    system = str(platform.system())
    if system == 'Linux':
        os.killpg(os.getpgid(int(pid)), signal.SIGTERM)
    elif system == 'Windows':
        os.system('taskkill /F /T /PID ' + str(pid))
    else:
        os.kill(int(ppid), signal.SIGTERM)


def config_update(value):
    try:
        config_path = value.get('local_dir') + '/config.py'
        stat = os.stat(config_path)
        old_st_mtime_ns = stat.st_mtime_ns
        while 1:
            stat = os.stat(config_path)
            if stat.st_mtime_ns != old_st_mtime_ns:
                old_st_mtime_ns = stat.st_mtime_ns
                try:
                    importlib.reload(config)
                    newcfg = {'chat_push': str(config.chat_push), 'VoIP_push': str(config.VoIP_push), 'tdtt_alias': str(config.tdtt_alias),
                                'FarPush_regID': str(config.FarPush_regID), 'WirePusher_ID': str(config.WirePusher_ID),
                                'FarPush_Phone_Type': str(config.FarPush_Phone_Type), 'shield_mode': str(config.shield_mode),
                                'blacklist': list(config.blacklist), 'whitelist': list(config.whitelist), 'tdtt_interface': str(config.tdtt_interface), 
                                'FarPush_interface': str(config.FarPush_interface), 'WirePusher_interface': str(config.WirePusher_interface),
                                'group': str(config.group), 'Bark_Url': str(config.Bark_Url), 'noti_detail': str(config.noti_detail), 'encode_message': str(config.encode_message), 'bark_encode_key': str(config.bark_encode_key),
                                'bark_encode_iv': str(config.bark_encode_iv)}
                except:
                    prt('读取配置文件异常,请检查配置文件的语法是否有误或所需变量是否存在，程序使用最后一次正确的的配置')
                    error_log(value.get('local_dir'))
                    continue
                for i in list(newcfg.keys()):
                    if str(value.get(i)) != str(newcfg.get(i)):
                        prt(str(i) + '更改,新' + str(i) + '值为' + str(newcfg.get(i)))
                value.update(newcfg)
            time.sleep(1)
    except KeyboardInterrupt:
        prt('由于触发了KeyboardInterrupt(同时按下了Ctrl+C等情况)，程序强制停止运行')
    except FileNotFoundError:
        prt('配置文件丢失，程序强制停止运行')
        error(value.get('pid'), value.get('ppid'), value.get('local_dir'))
    except:
        error(value.get('pid'), value.get('ppid'), value.get('local_dir'))


def run(func):
    if int(run_as_async):
        asyncio.get_event_loop().run_until_complete(asyncio.gather(func))
    else:
        eval(str(func))


def encode_data(json_payload):
    # bark key
    # deviceKey = 'deviceKey'
    # deviceKey = str(value.get('bark_devicekey'))
    # push payload
    # json = '{"body": "test", "sound": "birdsong"}'
    
    # must be 16 bit long
    key = str(value.get('bark_encode_key'))
    iv = str(value.get('bark_encode_iv'))

    
    key = subprocess.run(['printf', key], capture_output=True, text=True).stdout.strip()
    key = subprocess.run(['xxd', '-ps', '-c', '200'], input=key, capture_output=True, text=True).stdout.strip()
    iv = subprocess.run(['printf', iv], capture_output=True, text=True).stdout.strip()
    iv = subprocess.run(['xxd', '-ps', '-c', '200'], input=iv, capture_output=True, text=True).stdout.strip()
    
    # Encode the JSON payload
    ciphertext = subprocess.run(['echo', '-n', json_payload], capture_output=True, text=True)
    ciphertext = subprocess.run(['openssl', 'enc', '-aes-128-cbc', '-K', key, '-iv', iv], input=ciphertext.stdout.encode(), capture_output=True, text=True)
    ciphertext = subprocess.run(['base64'], input=ciphertext.stdout.encode(), capture_output=True, text=True).stdout.strip()
    
    # URL encode the ciphertext
    payload = {'ciphertext': ciphertext}
    # url = f'http://api.day.app/{deviceKey}'
    # response = requests.post(url, data=payload)
    
    return payload
    # subprocess.run(['curl', '-d', data.decode(), url])

def data_send(url, **kwargs):
    for i in range(1, 5):
        try:
            title1 = parse.quote(kwargs['title'])
            content1 = parse.quote(kwargs['content'])
            
            apiUrl = str(value.get('Bark_Url'))

            headers = {"Content-Type": "application/json; charset=utf-8"}
            
            data = {"body": kwargs['content'],
                      "title": kwargs['title'],
                      "sound": "healthnotification",
                      "icon": "https://i.328888.xyz/2023/05/12/iq597J.jpeg",
                      "group": "WeChat",
                      "url": "WeChat://"
            }
            
            jsonData = json.dumps(data)
            
            
            # prt('JSON 对象：' + jsonData)
            if str(value.get('noti_detail')) == '1':
                isEncode = str(value.get('encode_message')) == "1"
                hasKey = (not str(value.get('bark_encode_key')) == "") and (not str(value.get('bark_encode_iv')) == "")
                if (isEncode and hasKey):
                    prt('isEncode：' + isEncode)
                    encodeData = encode_data(jsonData)
                    response = requests.post(url = apiUrl, data = encodeData)
                else:
                    response = requests.post(url = apiUrl, data = jsonData, headers = headers)
            else:
                title2 = parse.quote("微信")
                content2 = parse.quote("你收到一条微信消息")
                response = requests.post(apiUrl + "/" + title2 + "/" + content2 + "?icon=https://i.328888.xyz/2023/05/12/iq597J.jpeg&group=WeChat&sound=healthnotification&url=WeChat://")
            
            if response.status_code > 299:
                raise RuntimeError
        except:
            if str(i) == '4':
                prt('连续三次向接口发送数据超时/失败，可能是网络问题或接口失效，终止发送')
                break
            prt('向接口发送数据超时/失败，第' + str(i) + '次重试')
        else:
            prt('成功向接口发送数据↑')
            break


@itchat.msg_register(itchat.content.INCOME_MSG, isFriendChat=True, isGroupChat=True)
def simple_reply(msg):
    notify = 0
    if int(value.get('shield_mode')):
        if not int(msg.get('ChatRoom')) or str(msg.get('NickName')) in list(value.get('whitelist')):
            notify = 1
    elif str(msg.get('NickName')) not in list(value.get('blacklist')):
        notify =  1
    if (str(value.get('group')) == '0' and int(msg.get('ChatRoom'))):
        notify =  0
    if int(notify) and not int(msg.get('NotifyCloseContact')):
        typesymbol = {
            itchat.content.TEXT: str(msg.get('Text')),
            itchat.content.FRIENDS: '好友请求',
            itchat.content.PICTURE: '[图片]',
            itchat.content.RECORDING: '[语音]',
            itchat.content.VIDEO: '[视频]',
            itchat.content.LOCATIONSHARE: '[共享实时位置]',
            itchat.content.CHATHISTORY: '[聊天记录]',
            itchat.content.TRANSFER: '[转账]',
            itchat.content.REDENVELOPE: '[红包]',
            itchat.content.EMOTICON: '[动画表情]',
            itchat.content.SPLITTHEBILL: '[群收款]',
            itchat.content.SHARING: '[卡片消息]',
            itchat.content.UNDEFINED: '[发送了一条消息]',
            itchat.content.VOIP: '[通话邀请]请及时打开微信查看',
            itchat.content.SYSTEMNOTIFICATION: '[系统通知]',
            itchat.content.ATTACHMENT: '[文件]' + str(msg.get('Text')),
            itchat.content.CARD: '[名片]' + str(msg.get('Text')),
            itchat.content.MUSICSHARE: '[音乐]' + str(msg.get('Text')),
            itchat.content.SERVICENOTIFICATION: str(msg.get('Text')),
            itchat.content.MAP: '[位置分享]' + str(msg.get('Text')),
            itchat.content.WEBSHARE: '[链接]' + str(msg.get('Text')),
            itchat.content.MINIPROGRAM: '[小程序]' + str(msg.get('Text')) }.get(msg['Type'])
        Name = str(msg.get('Name')) if str(msg.get('ChatRoom')) == '0' else '群聊 ' + str(msg.get('ChatRoomName'))
        if int(msg.get('ChatRoom')):
            typesymbol = str(msg.get('Name')) + ': ' + str(typesymbol)
        if str(msg.get('Type')) == str(itchat.content.SHARING):
            prt('[未知卡片消息，请在github上提交issue]: AppMsgType=' + str(msg.get('Text')))
        elif str(msg.get('Type')) == str(itchat.content.UNDEFINED):
            prt('[未知消息类型，请在github上提交issue]: MsgType=' + str(msg.get('Text')))
        else:
            prt(str(Name) + ': ' + str(typesymbol))
        if str(msg.get('Type')) == str(itchat.content.VOIP):
            if str(value.get('VoIP_push')) == '1' and str(value.get('tdtt_alias')) != '':
                data_send(str(value.get('tdtt_interface')), title='微信 ' + str(Name), content=str(typesymbol), alias=str(value.get('tdtt_alias')))
            elif str(value.get('VoIP_push')) == '2' and str(value.get('FarPush_regID')) != '':
                data_send(str(value.get('FarPush_interface')), title='微信 ' + str(Name), content=str(typesymbol), regID=str(value.get('FarPush_regID')), phone=str(value.get('FarPush_Phone_Type')), through='0')
            elif str(value.get('VoIP_push')) == '3' and str(value.get('WirePusher_ID')) != '':
                data_send(str(value.get('WirePusher_interface')), title='微信 ' + str(Name), message=str(typesymbol), id=str(value.get('WirePusher_ID')), type='WeChat_VoIP', action='weixin://')
            else:
                prt('配置有误，请更改配置')
        else:
            if str(value.get('chat_push')) == '1' and str(value.get('tdtt_alias')) != '':
                data_send(str(value.get('tdtt_interface')), title='微信 ' + str(Name), content=str(typesymbol), alias=str(value.get('tdtt_alias')))
            elif str(value.get('chat_push')) == '2' and str(value.get('FarPush_regID')) != '':
                data_send(str(value.get('FarPush_interface')), title='微信 ' + str(Name), content=str(typesymbol), regID=str(value.get('FarPush_regID')), phone=str(value.get('FarPush_Phone_Type')), through='0')
            elif str(value.get('chat_push')) == '3' and str(value.get('WirePusher_ID')) != '':
                data_send(str(value.get('WirePusher_interface')), title='微信 ' + str(Name), message=str(typesymbol), id=str(value.get('WirePusher_ID')), type='WeChat_chat', action='weixin://')
            else:
                prt('配置有误，请更改配置')


if __name__ == '__main__':
    try:
        urllib3.disable_warnings()
        run(itchat.check_login())
        run(itchat.auto_login(hotReload=True, enableCmdQR=2))
        value = Manager().dict()
        value.update({'pid': str(pid), 'ppid': str(ppid), 'local_dir': str(local_dir), 'chat_push': str(config.chat_push),
                        'VoIP_push': str(config.VoIP_push), 'tdtt_alias': str(config.tdtt_alias),
                        'FarPush_regID': str(config.FarPush_regID), 'WirePusher_ID': str(config.WirePusher_ID),
                        'FarPush_Phone_Type': str(config.FarPush_Phone_Type), 'shield_mode': str(config.shield_mode),
                        'blacklist': list(config.blacklist), 'whitelist': list(config.whitelist), 'tdtt_interface': str(config.tdtt_interface), 
                        'FarPush_interface': str(config.FarPush_interface), 'WirePusher_interface': str(config.WirePusher_interface),'group': str(config.group), 'Bark_Url': str(config.Bark_Url), 'noti_detail': str(config.noti_detail), 'encode_message': str(config.encode_message), 'bark_encode_key': str(config.bark_encode_key), 'bark_encode_iv': str(config.bark_encode_iv)})
        conf_update = Process(target=config_update, args=(value, ))
        conf_update.daemon = True
        conf_update.start()
        if int(value.get('shield_mode')):
            prt('白名单模式：群聊' + str(value.get('whitelist')) + '以及非群聊的消息将会推送')
        else:
            prt('黑名单模式：' + str(value.get('blacklist')) + '的消息将不会推送')
        run(itchat.run())
    except KeyboardInterrupt:
        prt('由于触发了KeyboardInterrupt(同时按下了Ctrl+C等情况)，程序强制停止运行')
    except:
        error(pid, ppid, local_dir)
