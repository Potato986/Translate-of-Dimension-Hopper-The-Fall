import asyncio
import json
import os
import shutil
from typing import Dict, Optional

import httpx
from httpx import HTTPStatusError

PARATRANZ_TOKEN = '5a75445bb99b4ece98b7e721a53fc8e1'
PROJECT_ID = 9743

paratranz_files = []


async def get_project_files():
    global paratranz_files
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'https://paratranz.cn/api/projects/{PROJECT_ID}/files',
            headers={'Authorization': PARATRANZ_TOKEN}
        )
    response.raise_for_status()
    paratranz_files = response.json()


def get_fileid_in_project(path: str) -> Optional[int]:
    for file in paratranz_files:
        if file['name'] == path:
            return file['id']
    return None


async def upload_project_file(path: str):
    path = path.replace('\\', '/')
    file_id = get_fileid_in_project(path[8:])
    if file_id is None:
        url = f'https://paratranz.cn/api/projects/{PROJECT_ID}/files'
    else:
        url = f'https://paratranz.cn/api/projects/{PROJECT_ID}/files/{file_id}'
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers={'Authorization': PARATRANZ_TOKEN},
            data={'path': os.path.dirname(path)[8:]},
            files={'file': (os.path.basename(path), open(path, 'rb'))}
        )
        response.raise_for_status()
        print(f'{path} 上传成功')


def read_lang(lang_file) -> Dict[str, str]:
    with open(lang_file, 'r') as f:
        lines = f.readlines()
    return dict(line.strip().split('=', maxsplit=1) for line in lines if '=' in line and not line.startswith('#'))


async def main():
    await get_project_files()
    for path in os.listdir('assets'):
        en = None
        zh = None
        dir_path = 'assets/' + path + '/lang/'
        if not os.path.isdir(dir_path):
            continue
        for lang in os.listdir(dir_path):
            if 'en_us' in lang.lower() and lang.endswith('lang'):
                en = os.path.join(dir_path, lang)
            if 'zh_cn' in lang.lower() and lang.endswith('lang'):
                zh = os.path.join(dir_path, lang)
        en_lang = read_lang(en) if en else {}
        zh_lang = read_lang(zh) if zh else {}

        pz = []
        for k, v in en_lang.items():
            pz.append({
                "key": k,
                "original": v,
                "translation": zh_lang[k] if k in zh_lang else ""
            })
        if pz:
            with open(en + '.json', 'w', encoding='utf-8') as f:
                json.dump(pz, f, ensure_ascii=False, indent=4)
            # os.makedirs(os.path.dirname(en.replace('assets', 'sources/resources')), exist_ok=True)
            # shutil.copy(en, en.replace('assets', 'sources/resources'))
            # shutil.copy(en + '.json', en.replace('assets', 'sources/resources') + '.json')
            # try:
            #     await upload_project_file(en.replace('assets', 'sources/resources') + '.json')
            # except Exception as e:
            #     print(e)
            #     print(en.replace('assets', 'sources/resources') + '.json' + ' 上传失败')
            # await asyncio.sleep(0.7)


if __name__ == '__main__':
    asyncio.run(main())
