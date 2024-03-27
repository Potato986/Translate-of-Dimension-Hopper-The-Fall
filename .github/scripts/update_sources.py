import asyncio
import json
import os
from typing import Optional

import httpx

PARATRANZ_TOKEN = os.environ.get('PARATRANZ_TOKEN')
PROJECT_ID = 9750

paratranz_files = []


async def get_project_files():
    global paratranz_files
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'https://paratranz.cn/api/projects/{PROJECT_ID}/files',
            headers={'Authorization': PARATRANZ_TOKEN}
        )
    if response.status_code != 200:
        raise Exception(f'Error getting project files: {response.text}')
    paratranz_files = response.json()
    print(paratranz_files)


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
        if response.status_code != 200:
            raise Exception(f'Error getting project files: {response.text}')
        print(f'{path} 上传成功')


def covert_lang(path: str) -> list:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    rt = []
    for line in lines:
        if '=' not in line:
            continue
        line = line.strip().split('=')
        if len(line) == 2:
            rt.append({
                'key': line[0],
                'original': line[1],
                'translation': ''
            })

    return rt


async def main():
    await get_project_files()
    for root, dirs, files in os.walk("sources"):
        for file in files:
            if file.endswith(".lang"):
                pz = covert_lang(f'{root}\\{file}')
                with open(f"{root}\\{file}.json", 'w', encoding='utf-8') as f:
                    json.dump(pz, f, ensure_ascii=False, indent=4)
                await upload_project_file(f"{root}\\{file}.json")


if __name__ == '__main__':
    asyncio.run(main())
