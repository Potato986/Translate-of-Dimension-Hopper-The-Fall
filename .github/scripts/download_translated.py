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
                lang = covert_paratranz_json_to_lang(path).replace('\\n', '\n')
                with open(f'{os.path.dirname(new_path)}/zh_cn.lang', 'w', encoding='utf-8') as f:
                    f.write(lang)
            if file.endswith('.json') and '.lang' not in file:
                lang = covert_paratranz_json_to_json(path).replace('\\n', '\n')
                with open(f'{os.path.dirname(new_path)}/zh_cn.json', 'w', encoding='utf-8') as f:
                    json.dump(lang, f, ensure_ascii=False, indent=4)

    shutil.rmtree('temp')


if __name__ == '__main__':
    asyncio.run(main())
