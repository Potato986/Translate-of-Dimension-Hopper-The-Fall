import asyncio
import json
import os
import shutil
import zipfile

import httpx

PARATRANZ_TOKEN = os.environ.get('PARATRANZ_TOKEN')
PROJECT_ID = 9743

if not PARATRANZ_TOKEN:
    raise RuntimeError("环境变量 PARATRANZ_TOKEN 未设置，请在 GitHub Secrets 中配置并传入。")

async def download_project():
    print("开始下载项目翻译数据...")
    for retry in range(3):
        try:
            async with httpx.AsyncClient() as client:
                # 请求生成翻译文件
                response = await client.post(
                    f'https://paratranz.cn/api/projects/{PROJECT_ID}/artifacts',
                    headers={'Authorization': f'Bearer {PARATRANZ_TOKEN}'}
                )
                response.raise_for_status()

                # 下载翻译文件
                response = await client.get(
                    f'https://paratranz.cn/api/projects/{PROJECT_ID}/artifacts/download',
                    headers={'Authorization': f'Bearer {PARATRANZ_TOKEN}'},
                    follow_redirects=True
                )
                response.raise_for_status()

                with open('artifacts.zip', 'wb') as file:
                    file.write(response.content)

            print("✅ 下载成功")
            break
        except Exception as e:
            print(f"❌ 下载失败，错误：{e}")
            if retry == 2:
                raise
            print(f"尝试下载第 {retry + 2} 次")

def covert_paratranz_json_to_lang(json_file: str) -> str:
    with open(json_file, 'r', encoding='utf-8') as f:
        translated = json.load(f)

    return '\n'.join(
        [f'{t["key"]}={t["translation"] if t["translation"] != "" else t["original"]}' for t in translated]
    )

def covert_paratranz_json_to_json(json_file: str) -> dict:
    with open(json_file, 'r', encoding='utf-8') as f:
        translated = json.load(f)
    return dict([(t["key"], t["translation"] if t["translation"] != "" else t["original"]) for t in translated])

async def main():
    await download_project()
    with zipfile.ZipFile('artifacts.zip', 'r') as zip_ref:
        zip_ref.extractall('temp/')

    for root, dirs, files in os.walk('temp/utf8'):
        for file in files:
            path = os.path.join(root, file).replace('\\', '/')
            new_path = 'translated' + path.replace('temp/utf8', '')
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            if file.endswith('.lang.json'):
                lang = covert_paratranz_json_to_lang(path).replace('\\n', '%n')
                with open(f'{os.path.dirname(new_path)}/zh_cn.lang', 'w', encoding='utf-8') as f:
                    f.write(lang)
            if file.endswith('.json') and '.lang' not in file:
                lang = covert_paratranz_json_to_json(path)
                with open(f'{os.path.dirname(new_path)}/zh_cn.json', 'w', encoding='utf-8') as f:
                    json.dump(lang, f, ensure_ascii=False, indent=4)

    shutil.rmtree('temp')

if __name__ == '__main__':
    asyncio.run(main())

