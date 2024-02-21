import asyncio
import requests
import time

import aiohttp as aiohttp
import typer
from bs4 import BeautifulSoup


def get_pull_request_highest_number(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?per_page=1"
    resp = requests.get(url)
    body = resp.json()
    return body[0]["number"]


async def extract_dangling_commits(owner, repo, pull_nb):
    url = f"https://github.com/{owner}/{repo}/pull/{pull_nb}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            body = await resp.text()
            soup = BeautifulSoup(body, 'html.parser')
            push_link = soup.find_all(string='force-pushed', href=True)
            commit_hashes = [link['href'].split("/")[-1].split("..")[0] for link in push_link]
            if len(commit_hashes) > 0:
                await save_dangling_commits_list(owner, repo, commit_hashes, pull_nb)


async def save_dangling_commits_list(owner, repo, commit_hashes, pull_nb):
    for hash in commit_hashes:
        typer.echo(f"{owner}/{repo},{pull_nb},{hash}")

# async def retrieve_dangling_commit(owner, repo, commit_hash):
#     url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_hash}"
#     async with aiohttp.ClientSession(headers=headers) as session:
#         async with session.get(url) as resp:
#             commit = await resp.text()
#             print(commit[:15])


async def process(owner, repo, pr_max):
    start_time = time.time()
    global headers
    headers = {"X-GitHub-Api-Version": "2022-11-28"}

    pr_to_scan = range(1, pr_max+1)

    tasks = []

    for i in pr_to_scan:
        task = asyncio.create_task(extract_dangling_commits(owner, repo, i))
        tasks.append(task)

    print("Saving the results to stdout in csv format.")
    typer.echo("repository,pull_request_number,dangling_commit_hash")
    await asyncio.gather(*tasks)

    time_difference = time.time() - start_time
    print("Scraping time: %.2f seconds." % time_difference)


def main(path, github_token):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process(path, github_token))
