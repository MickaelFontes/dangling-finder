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
            "Accept": "application/vnd.github+json"
        }

    def check_repository(self):
        url_api = f"https://api.github.com/repos/{self._owner}/{self._repo}"
        url_repo = f"https://github.com/repos/{self._owner}/{self._repo}"
        err_console.print(f"Loading dangling commits on GitHub: {url_repo}")
        r = requests.get(url_api, headers=self._rest_headers)
        if r.status_code != 200:
            raise GitHubRepoError(f"Could not connect to the following repo: {url_repo}")
        err_console.print("✅ GitHub repository found")

    def get_pull_request_highest_number(self):
        url = (
            f"https://api.github.com/repos/{self._owner}/{self._repo}/pulls"
        )
        resp = requests.get(url, headers=self._rest_headers)
        body = resp.json()
        if len(body[0]) == 0:
            return 0
        return body[0]["number"]

    def process_single_response(self):
        end_cursor = ""
        dangling_heads = []
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
        if self._return_git_script:
            dangling_heads = [e[::-1].split("/", 1)[0][::-1] for e in dangling_heads]
            dangling_heads = [
                f"git fetch origin {e}:refs/remotes/origin/dangling-{e}"
                for e in dangling_heads
            ]
        return "\n".join(dangling_heads), remaining_rate_limit

    def process_extracted_lists(self):
        return None
