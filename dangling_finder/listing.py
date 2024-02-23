import requests
from rich.console import Console

from dangling_finder.exceptions import GitHubRepoError

err_console = Console(stderr=True)


class graphQL:
    """docstring for graphQL"""

    def __init__(self, owner, repo, github_token, return_git_script):
        super(graphQL, self).__init__()
        self._github_token = github_token
        self._repo = repo
        self._owner = owner
        self._return_git_script = return_git_script
        self._rest_headers = {
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Bearer {self._github_token}",
            "Accept": "application/vnd.github+json",
        }

    def check_repository(self):
        url_api = f"https://api.github.com/repos/{self._owner}/{self._repo}"
        url_repo = f"https://github.com/repos/{self._owner}/{self._repo}"
        err_console.print(f"Loading dangling commits on GitHub: {url_repo}")
        r = requests.get(url_api, headers=self._rest_headers)
        if r.status_code != 200:
            raise GitHubRepoError(
                f"Could not connect to the following repo: {url_repo}"
            )
        err_console.print("✅ GitHub repository found")

    def get_pull_request_highest_number(self):
        url = f"https://api.github.com/repos/{self._owner}/{self._repo}/pulls?state=all"
        resp = requests.get(url, headers=self._rest_headers)
        body = resp.json()
        if len(body[0]) == 0:
            return 0
        return body[0]["number"]

    def process_single_response(self):
        end_cursor = ""
        dangling_heads = []
        total_cost = 0
        while True:
            has_next_page = False
            query = """
                    query ($owner: String!, $repo: String!) {
                    rateLimit {
                        resetAt
                        cost
                        remaining
                    }
                    repository(name: $repo, owner: $owner ) {
                        pullRequests(first: 100REPLACE_THIS) {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        nodes {
                            ... on PullRequest {
                            timelineItems(first: 100, itemTypes: [HEAD_REF_FORCE_PUSHED_EVENT]) {
                                nodes {
                                ... on HeadRefForcePushedEvent {
                                    beforeCommit {
                                    commitUrl
                                    }
                                }
                                }
                            }
                            }
                        }
                        }
                    }
                    }
                """
            query = query.replace("REPLACE_THIS", end_cursor)
            variables = {"owner": self._owner, "repo": self._repo}
            request = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers={"Authorization": f"Bearer {self._github_token}"},
            )
            if request.status_code == 200:
                result = request.json()
                has_next_page = result["data"]["repository"]["pullRequests"][
                    "pageInfo"
                ]["hasNextPage"]
                new_cursor = result["data"]["repository"]["pullRequests"]["pageInfo"][
                    "endCursor"
                ]
                total_cost += result["data"]["rateLimit"]["cost"]
                result_data = result["data"]["repository"]["pullRequests"]["nodes"]
                for e in result_data:
                    loop_array = e["timelineItems"]["nodes"]
                    if loop_array:
                        for dangling_head in loop_array:
                            if dangling_head["beforeCommit"] is not None:
                                dangling_heads += [
                                    dangling_head["beforeCommit"]["commitUrl"]
                                ]
                if has_next_page:
                    end_cursor = ', after:"' + new_cursor + '"'
                else:
                    break
            else:
                raise Exception(
                    f"""Query failed to run by returning code of {request.status_code}.
                    Response body:\n{request.text}
                    Response headers:\n{request.headers}"""
                )
        remaining_rate_limit = result["data"]["rateLimit"]
        remaining_rate_limit["total"] = total_cost
        if self._return_git_script:
            dangling_heads = self.generate_bash_script(dangling_heads)
        return "\n".join(dangling_heads), remaining_rate_limit

    def generate_bash_script(self, dangling_heads):
        dangling_heads = [e[::-1].split("/", 1)[0][::-1] for e in dangling_heads]
        regroup_git_commands = []
        current_command = f"git fetch origin {dangling_heads[0]}:refs/remotes/origin/dangling-{dangling_heads[0][:10]}"
        next_command = f"git fetch origin {dangling_heads[0]}:refs/remotes/origin/dangling-{dangling_heads[0][:10]}"
        i = 1
        while i < len(dangling_heads):
            while len(next_command) < 4096 and i < len(dangling_heads):
                current_command = next_command
                next_command = (
                    current_command
                    + f" {dangling_heads[i]}:refs/remotes/origin/dangling-{dangling_heads[i][:10]}"
                )
                i += 1
            if len(next_command) < 4096:
                continue
            else:
                regroup_git_commands.append(current_command)
                next_command = f"git fetch origin {dangling_heads[i-1]}:refs/remotes/origin/dangling-{dangling_heads[i-1][:10]}"
        regroup_git_commands.append(next_command)
        return regroup_git_commands
