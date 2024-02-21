import requests
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
from typing_extensions import Annotated

err_console = Console(stderr=True)

from dangling_finder.exceptions import GitHubRepoError
from dangling_finder.listing import get_pull_request_highest_number, main

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True
)


@app.command(no_args_is_help=True)
def find_heads(owner: str, repo: str, github_token: Annotated[str, typer.Option()] = None):
    """List dangling commits SHA-1 in a GitHub repository's pull requests.
    NB: Only upper parents are returned.

    Args:
        owner (str): name of the repository owner
        repo (str): name of the repository
    """
    url = f"https://github.com/{owner}/{repo}"
    err_console.print(f"Loading dangling commits on GitHub: {url}")
    r = requests.get(url)
    if r.status_code != 200:
        raise GitHubRepoError(f"Could not connect to the following repo: {url}")
    err_console.print("✅ GitHub repository found")
    pr_max = get_pull_request_highest_number(owner, repo)
    err_console.print(f"{pr_max} pull requests to scan.")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=err_console,
    ) as progress:
        progress.add_task(description="Processing...", total=None)
        main(owner, repo, pr_max)
    err_console.print("Done.")


@app.command(no_args_is_help=True)
def find_children(csv_file: str, github_token: Annotated[str, typer.Option()] = None):
    """List all children dangling commits, starting from the parents found by `find-heads` command.

    Args:
        csv_file (str): path to the result of the find-heads command
        github_token (Annotated[str, typer.Argument): Optional GitHub token, might be needed to avoid rate limiting.

    Returns:
        _type_: _description_
    """
    
    return None
