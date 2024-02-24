# dangling-finder

Find dangling commits inside your GitHub repositories.

## Introduction

This is an attempt to find ways to recover dangling commits inside a GitHub repository, to help you improve your use of repository secret scanning tools like [trufflehog](https://github.com/trufflesecurity/trufflehog) or [gitleaks](https://github.com/gitleaks/gitleaks).
For now, only one way is used:

* recover all `force-pushed` events in a pull request and list all former HEADs of the PR (most probably dangling-commits)
* TODO: get all available Push events from GitHub API (but only the X last events can be retrieved)
* TODO: add closed and not merged PR, in addition to their lost force-pushed commits
* TODO: try with user specific events to get more dangling commits

## Limitations

This tool only focuses on potential dangling-commits sources. It doesn't list:

* current HEADS of pull requests (whether opened, merged or closed - TODO: check if closed PRs are already covered by popular tools)
* parent dangling-commits of the dangling HEADs found in a "force-pushed" event (`git fetch` can be used to avoid thinking about this, see below in [Usage](#usage))
* the content of the dangling-commits found: it would require to browse all commits from the dangling HEADs found (unecessary if you use `git fetch`) and to have a way to get the content of each commit (the GitHub GraphQL API does not seem to provide a way to do so, and it would cost too much using the REST API - `git fetch` avoid us this trouble)

## Installation

```bash
git clone git@github.com:MickaelFontes/dangling-finder.git && cd dangling-finder
poetry install
```

## Usage

To show the help, run:

```bash
poetry run dangling-finder -h
```

To use the commands, you will need to provide a GitHub API token. Read the documentation [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) to generate a token.

Use the script to find the dangling heads and use the generated script with the dangling heads to add the dangling commits in the clone repo.

```bash
poetry run dangling-finder owner repo --github-token $GITHUB_TOKEN --git-script > owner-repo-dangling-scirpt.sh
git clone git@github.com:owner/repo.git && cd owner/repo
chmod +x ../owner-repo-dangling-scirpt.sh && bash ../owner-repo-dangling-scirpt.sh
```

Then scan the repo local for secrets with your favorite tool.
