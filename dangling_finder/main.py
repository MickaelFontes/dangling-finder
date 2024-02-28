"""CLI module of dangling-finder"""

import time
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing_extensions import Annotated

from dangling_finder.listing import _GraphQL

err_console = Console(stderr=True)

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)


@app.command(no_args_is_help=True)
def find_lost_pr_heads(
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
        git_script (bool): return bash script for local git repo
    """
    graphql_api = _GraphQL(owner, repo, github_token, git_script)
    graphql_api.check_repository()
    pr_max = graphql_api.get_pull_request_highest_number()
    err_console.print(f"{pr_max} pull requests to scan.")
    start_time = time.time()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=err_console,
    ) as progress:
        task1 = progress.add_task(
            description="Get all force-pushed events in PRs...", total=10
        )
        result1, old_rate_limit, prs = (
            graphql_api.execute_force_pushed_queries()
        )
        progress.update(
            task1, completed=10, description="Force-pushed PR events retrieved."
        )
        task2 = progress.add_task(
            description="Get all closed-and-not-merged PRs...", total=10
        )
        result2, rate_limit = graphql_api.execute_closed_pr_queries(
            prs, old_rate_limit
        )
        progress.update(
            task2,
            completed=10,
            description="Closed-and-not-merged PRs retrieved.",
        )
    duration = time.time() - start_time
    err_console.print(
        "Done. Duration: " + time.strftime("%H:%M:%S", time.gmtime(duration))
    )
    err_console.print("GitHub API quotas:")
    err_console.print(f'Remaining rate limit - {rate_limit["remaining"]}')
    err_console.print(f'Reset date rate limit - {rate_limit["resetAt"]}')
    err_console.print(f'Total cost used - {rate_limit["total"]}')
    typer.echo("# Force-pushed events in PRs")
    typer.echo(result1)
    typer.echo("# Closed PRs not merged")
    typer.echo(result2)


if __name__ == "__main__":
    app()
