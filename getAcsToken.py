#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from playwright.sync_api import sync_playwright
import time


def get_cache_file_path():
    """
    获取缓存文件路径
    """
    return os.path.join(os.path.dirname(__file__), 'acs_token_cache.json')


def save_token_to_cache(token, timestamp=None):
    """
    将Acs-Token保存到缓存文件
    """
    if timestamp is None:
        timestamp = int(time.time())

    cache_data = {
        'token': token,
        'timestamp': timestamp,
    }

    try:
        with open(get_cache_file_path(), 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print(f"Acs-Token已缓存到文件: {get_cache_file_path()}")
        return True
    except Exception as e:
        print(f"保存缓存失败: {e}")
        return False


def load_token_from_cache():
    """
    从缓存文件加载Acs-Token
    """
    cache_file = get_cache_file_path()

    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        return cache_data['token']

    except Exception as e:
        print(f"读取缓存失败: {e}")
        return None


def get_baidu_fanyi_acs_token(text_to_translate="Hello"):
    """
    通过模拟浏览器操作，触发百度翻译请求，并截取生成的 acs-token。
    Alfred workflow专用版本
    """
    acs_token = None

    try:
        with sync_playwright() as p:
            # 启动 Chromium 浏览器，headless=True 表示无界面运行
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 定义请求监听器，用于拦截目标 API 请求
            def handle_request(request):
                nonlocal acs_token
                # 检查请求 URL 是否为翻译 API 接口
                if "https://fanyi.baidu.com/ait/text/translate" in request.url:
                    # 从请求头中提取 acs-token
                    token = request.headers.get("acs-token")
                    if token:
                        acs_token = token

            # 注册请求监听器
            page.on("request", handle_request)

            # 访问百度翻译页面
            page.goto(f"https://fanyi.baidu.com/mtpe-individual/transText?query={text_to_translate}")

            # 等待页面加载
            # page.wait_for_timeout(2000)

            # 尝试找到输入框并输入文本
            # try:
            #     # 百度翻译输入框的选择器
            #     input_selector = "textarea#baidu_translate_input"
            #     page.wait_for_selector(input_selector, timeout=5000)
            #     page.fill(input_selector, text_to_translate)

            #     # 等待翻译请求
            #     page.wait_for_timeout(3000)

            # except Exception as e:
            #     print(f"输入框操作失败: {e}")
            #     # 尝试备用方案
            #     try:
            #         # 尝试通过键盘输入
            #         page.keyboard.type(text_to_translate)
            #         page.wait_for_timeout(3000)
            #     except:
            #         pass

            # 等待一段时间获取token
            start_time = time.time()
            while acs_token is None and (time.time() - start_time) < 10:
                page.wait_for_timeout(500)

            browser.close()

    except Exception as e:
        print(f"获取Acs-Token失败: {e}")
    if acs_token:
        save_token_to_cache(acs_token)
    return acs_token


if __name__ == '__main__':
    # 测试获取Acs-Token
    token = get_baidu_fanyi_acs_token("test")
    if token:
        print(f"成功获取Acs-Token: {token[:50]}...")
    else:
        print("未能获取Acs-Token")
