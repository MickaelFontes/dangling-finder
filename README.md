# dangling-finder

Find dangling commits inside your GitHub repositories.

## Introduction

This is an attempt to find ways to recover dangling commits inside a GitHub repository, to help you improve your use of repository secret scanning tools like [trufflehog](https://github.com/trufflesecurity/trufflehog) or [gitleaks](https://github.com/gitleaks/gitleaks).
For now, two technics are used:

* recover all `force-pushed` events in a pull request and list all former HEADs of the PR (most probably dangling-commits)
* add closed and not merged PR, in addition to their lost force-pushed commits

Coming in the future:

* TODO: get all available Push events from GitHub API (but only the X last events can be retrieved)
* TODO: try with user specific events to get more dangling commits

## Installation

```bash
# Using Pypi package
pip install dangling-finder
dangling-finder -h

# Using source repository directly
git clone git@github.com:MickaelFontes/dangling-finder.git && cd dangling-finder
poetry install
poetry run dangling-finder -h
```

## Usage

Run `dangling-finder` after your `git clone` to add found dangling commits to your locally cloned repository.

```bash
GITHUB_REPO=my_repository
GITHUB_OWNER=owner
GITHUB_TOKEN=my_token

git clone git@github.com:$GITHUB_TOKEN/$GITHUB_REPO.git
cd $GITHUB_REPO
dangling-finder pull-requests $GITHUB_OWNER $GITHUB_REPO --github-token $GITHUB_TOKEN --git-config >> ./.git/config
git fetch --all

# Then use your favorite secret scanning tool, example below
gitleaks detect --source . -v
```

### GitHub authentication

To use the commands, you will need to provide a GitHub API token. Read the documentation [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) to generate a token.

### About dangling commits enumeration

The tool only enumerates the "top" dangling commits found using various enumeration technics - top meaning their parents commits are not enumerated recursively to check if they are also dangling commits or not.

Therefore, one should not consider any output of `dangling-finder` as exhaustive, each for a given technique covered by the tool.

The prefered way is to use `git fetch` to retrieve their parent commits (and so forth) easily to enrich your local repository copy.

```bash
DANGLING_COMMIT_HASH=123456789
git fetch $DANGLING_COMMIT_HASH:refs/remotes/origin/dangling-$DANGLING_COMMIT_HASH
```

## Limitations

This tool only focuses on enumerating potential dangling commits' sources, usually not covered by default git secret scanning (`git clone` + `gitleaks detect`). It only focuses on **listing** the top dangling commits (no enumeration of their **parent commits** that are also dangling commits), not included in the usual `git clone` from GitHub.  
It doesn't list:

* all found dangling commits (only the top dangling commits, not their parents and so forth - for exhaustivity, use `git fetch` see [Usage part](#about-dangling-commits-enumeration))
* all HEADS of pull requests (only closed and not merged pull requests are listed - `git clone` already clones the branches of opened and not merged)
* the content of the dangling commits found: it would require long recursive enumeration of dangling commits and many API calls to retrieve their content (see [commits enumeration](#about-dangling-commits-enumeration))

Moreover, in its current implementation, other limits exist:

* only the first 100 `HeadRefForcePushedEvent` are scanned in pull requests (state of current implementation - never encountered a pull request with more than 100 `HeadRefForcePushedEvent`)
