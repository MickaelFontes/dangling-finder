# dangling-finder

The goal of this tool is to help you find dangling commits on your GitHub repository and check if they contain sensitive information or technical secrets.
As described by GitHub [in their documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository), any information inside a commit pushed to GitHub should be considered has compromised.

Strategy:

* one target repo
* on each pull request, get all force-pushed events and save a list of all former heads
* from those former heads, use the GitHub REST API to get all previous commits until the current history is rejoigned.
  store all those commits in a json
* print the gitleaks/trufflehog command to scan both the repo and the dangling commits
