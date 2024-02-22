import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing_extensions import Annotated

err_console = Console(stderr=True)

from dangling_finder.listing import graphQL

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True
)


@app.command(no_args_is_help=True)
def find_lost_heads(
    owner: str,
    repo: str,
    github_token: Annotated[str, typer.Option()],
    git_script: Annotated[bool, typer.Option()] = False,
):
    """List dangling commits SHA-1 in a GitHub repository's pull requests.
    NB: Only upper parents are returned.

    Args:
        owner (str): name of the repository owner
        repo (str): name of the repository
        github_token (str): personnal GitHub access token
        git_script (bool): if True, return a bash script to execute git commands to retrieve dangling commits
    """
    graphql_api = graphQL(owner, repo, github_token, git_script)
    graphql_api.check_repository()
    pr_max = graphql_api.get_pull_request_highest_number()
    err_console.print(f"{pr_max} pull requests to scan.")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=err_console,
    ) as progress:
        progress.add_task(description="Processing...", total=None)
        result, remaining_rate_limit = graphql_api.process_single_response()
    err_console.print("Done.\nGitHub API quotas:")
    err_console.print(f'Remaining rate limit - {remaining_rate_limit["remaining"]}')
    err_console.print(f'Reset date rate limit - {remaining_rate_limit["resetAt"]}')
    typer.echo(result)
