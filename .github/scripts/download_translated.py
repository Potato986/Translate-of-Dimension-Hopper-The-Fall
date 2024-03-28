import asyncio
import json
import os
import shutil
import zipfile

import httpx

PARATRANZ_TOKEN = os.environ.get('PARATRANZ_TOKEN')
PROJECT_ID = 9743


async def download_project():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f'https://paratranz.cn/api/projects/{PROJECT_ID}/artifacts',
            headers={'Authorization': PARATRANZ_TOKEN}
        )
        response.raise_for_status()
        response = await client.get(
            f'https://paratranz.cn/api/projects/{PROJECT_ID}/artifacts/download',
            headers={'Authorization': PARATRANZ_TOKEN},
            follow_redirects=True
        )
        response.raise_for_status()
        with open('artifacts.zip', 'wb') as file:
            file.write(response.content)


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


def read_lang(lang_path) -> dict:
    with open(lang_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return dict(line.strip().split('=') for line in lines if '=' in line and not line.startswith('#'))


def replace_quest_book():
    with open('sources/config/betterquesting/langquests.json', 'r', encoding='utf-8') as f:
        lang_quest = json.load(f)
    translated = read_lang('translated/config/betterquesting/resources/dimensionhopper/lang/zh_cn.lang')

    result = []

    def change_value(v: str):
        t = lang_quest
        for k in result[:-1]:
            t = t[k]
        t[result[-1]] = v

    def travel_dict(d):
        if isinstance(d, dict):
            for k, v in d.items():
                result.append(k)
                travel_dict(v)
                result.pop()
        if isinstance(d, list):
            for i, v in enumerate(d):
                result.append(i)
                travel_dict(v)
                result.pop()
        if isinstance(d, str):
            if d in translated:
                change_value(translated[d])

    travel_dict(lang_quest)
    with open('translated/config/betterquesting/DefaultQuests.json', 'w', encoding='utf-8') as f:
        json.dump(lang_quest, f, ensure_ascii=False, indent=2)


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
                lang = covert_paratranz_json_to_lang(path)
                with open(f'{os.path.dirname(new_path)}/zh_cn.lang', 'w', encoding='utf-8') as f:
                    f.write(lang)
            if file.endswith('.json') and '.lang' not in file:
                lang = covert_paratranz_json_to_json(path)
                with open(f'{os.path.dirname(new_path)}/zh_cn.json', 'w', encoding='utf-8') as f:
                    json.dump(lang, f, ensure_ascii=False, indent=4)

    shutil.rmtree('temp')

    replace_quest_book()


if __name__ == '__main__':
    asyncio.run(main())
