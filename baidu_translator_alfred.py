#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from os import path
import os
import time
import requests
import re
import sys

from getAcsToken import get_baidu_fanyi_acs_token, load_token_from_cache
next_url = "https://fanyi.baidu.com/mtpe-individual/transText?query="


def detect_language(text):
    """
    检测文本的语言
    返回: 'zh' (中文) 或 'en' (英文)
    """
    # 检查是否包含中文字符
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    if chinese_pattern.search(text):
        return 'zh'
    else:
        return 'en'


def is_single_word(text):
    """
    判断是否为单个单词（不包含空格和标点符号）
    """
    # 去除首尾空格，检查是否只包含字母和可能的连字符
    cleaned_text = text.strip()
    if len(cleaned_text.split()) == 1 and re.match(r'^[a-zA-Z\-]+$', cleaned_text):
        return True
    return False


def baidu_translate_ai(query):
    """
    调用百度翻译AI API进行翻译（Alfred专用版本）
    """
    url = 'https://fanyi.baidu.com/ait/text/translate'

    # 设置请求头
    headers = {
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
        'Acs-Token': load_token_from_cache(),
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://fanyi.baidu.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'accept': 'text/event-stream',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }

    detect_lang = detect_language(query)

    # 设置请求数据
    data = {
        "isAi": False,
        "sseStartTime": int(time.time() * 1000) - 100,
        "query": query,
        "from": detect_lang,
        "to": 'zh' if detect_lang == 'en' else 'en',
        "corpusIds": [],
        "needPhonetic": False,
        "domain": "ai_advanced",
        "detectLang": "",
        "isIncognitoAI": False,
        "milliTimestamp": int(time.time() * 1000)
    }

    try:
        # 发送POST请求，启用流式响应
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30,
            stream=True
        )

        if response.status_code == 200:
            # 处理服务器发送事件（SSE）响应
            if 'text/event-stream' in response.headers.get('content-type', ''):
                buffer = ""
                events = {}

                # 实时处理流数据
                for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                    if chunk:
                        buffer += chunk
                        lines = buffer.split('\n')
                        buffer = lines[-1]

                        for line in lines[:-1]:
                            line = line.strip()
                            if line.startswith('data:'):
                                data_content = line[5:].strip()
                                if data_content:
                                    try:
                                        json_data = json.loads(data_content)
                                        if json_data.get('errno') == 995:
                                            get_baidu_fanyi_acs_token(query)
                                            return baidu_translate_ai(query)
                                        elif json_data.get('errno') != 0:
                                            return None
                                        json_data = json_data['data']
                                        if 'event' in json_data:
                                            events[json_data['event']] = json_data
                                    except json.JSONDecodeError:
                                        pass

                # 返回处理结果
                if 'GetDictSucceed' in events:
                    dictResult = events['GetDictSucceed']['dictResult']
                    simple_means = dictResult['simple_means']
                    if detect_lang == 'en':
                        return format_alfred_output_en(query, simple_means)
                    else:
                        return format_alfred_output_ch(query, simple_means)
                elif 'InterpretingSucceed' in events:
                    content = events['InterpretingSucceed']['content']
                    return format_alfred_output_simple(query, content)
                elif 'Translating' in events:
                    content = events['Translating']['list'][0]['dst']
                    return format_alfred_output_simple(query, content)

            else:
                # 普通JSON响应
                result = response.json()
                return format_alfred_output_simple(query, str(result))
        else:
            return format_alfred_error(f"请求失败，状态码: {response.status_code}")

    except requests.exceptions.RequestException as e:
        return format_alfred_error(f"请求异常: {e}")


def format_alfred_output_en(query, data):
    """
    将英文单词信息格式化为Alfred JSON格式
    """
    word_name = data.get("word_name", query)
    symbols = data.get("symbols", [{}])[0]
    ph_en = symbols.get("ph_en", "")
    ph_am = symbols.get("ph_am", "")

    # 构建Alfred items
    items = []

    # 主翻译结果 - 添加uid和明确的排序控制
    title = f"{word_name} - 英/{ph_en}/    美/{ph_am}/"
    items.append({
        "uid": "main_translation",
        "title": title,
        "arg": next_url + query,
        "icon": {
            "path": path.join(os.path.dirname(__file__), "icon.png")
        }
    })

    # 构建详细释义
    parts = symbols.get("parts", [])
    details = []
    for i, part in enumerate(parts):
        part_name = part.get("part", "")
        means = "；".join(part.get("means", []))
        details.append(f"{part_name} {means}")

    # 添加词形变化
    exchange = data.get("exchange", {})
    if exchange:
        details.append("词形变化:")
        word_third = exchange.get("word_third", [])
        word_ing = exchange.get("word_ing", [])
        word_past = exchange.get("word_past", [])
        word_done = exchange.get("word_done", [])

        if word_third:
            details.append(f"第三人称单数：{', '.join(word_third)}")
        if word_ing:
            details.append(f"现在进行时：{', '.join(word_ing)}")
        if word_past:
            details.append(f"过去式：{', '.join(word_past)}")
        if word_done:
            details.append(f"过去分词：{', '.join(word_done)}")

    # 添加详细释义选项 - 使用递增的uid确保顺序
    for i, detail in enumerate(details):
        items.append({
            "uid": f"detail_{i:03d}",  # 使用格式化数字确保排序
            "title": detail,
            "arg": next_url + query,
            "icon": {
                "path": path.join(os.path.dirname(__file__), "icon.png")
            }
        })

    return json.dumps({"items": items})


def format_alfred_output_ch(query, data):
    """
    将中文单词信息格式化为Alfred JSON格式
    """
    word_name = data.get("word_name", query)
    symbols = data.get("symbols", [{}])

    items = []
    result = []
    for symbol in symbols:
        result.append(f"[{symbol.get('word_symbol', '')}]")
        parts = symbol.get("parts", [])
        if parts:
            for part in parts:
                means = part.get("means", [])
                for m in means:
                    result.append(f"{m.get('text', '')}")
                    result.append(f"{m.get('part', '')} {'；'.join(m.get('means', []))}")
        result.append("")

    for line in result:
        items.append({
            "uid": "detail",
            "title": line,
            "arg": next_url + query,
            "icon": {
                "path": path.join(os.path.dirname(__file__), "icon.png")
            }
        })

    return json.dumps({"items": items})


def format_alfred_output_simple(query, content):
    """
    将简单翻译结果格式化为Alfred JSON格式
    """
    items = []

    items.append({
        "uid": "translation",
        "title": '翻译结果',
        "subtitle": content,
        "icon": {
            "path": path.join(os.path.dirname(__file__), "icon.png")
        }
    })

    return json.dumps({"items": items})


def format_alfred_error(error_message):
    """
    格式化错误信息为Alfred JSON格式
    """
    items = [{
        "uid": "error",
        "title": "翻译失败",
        "subtitle": error_message,
        "arg": error_message,
        "icon": {
            "path": "error.png"
        }
    }]

    return json.dumps({"items": items})


def main():
    """
    主函数 - Alfred workflow入口点
    """

    # 输出Alfred JSON格式
    if len(sys.argv) > 1:
        query = sys.argv[1].strip()
        if query:
            result = baidu_translate_ai(query)
            if result:
                print(result)
            else:
                print(format_alfred_error("翻译服务暂时不可用"))
        else:
            print(format_alfred_error("请输入要翻译的内容"))
    else:
        print(format_alfred_error("请输入要翻译的内容"))


if __name__ == "__main__":
    main()
