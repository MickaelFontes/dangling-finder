"""Module used for output generation"""

import json
from dataclasses import dataclass
from textwrap import dedent


@dataclass
class OutputFormat:
    """Class for generating output with correct formatting"""

    owner: str
    repo: str
    bash_script: bool
    git_config: bool
    json_dangling_heads: list

    @property
    def dangling_heads(self):
        dangling_heads = [
            e["commitUrl"][::-1].split("/", 1)[0][::-1]
            for e in self.json_dangling_heads
        ]
        return dangling_heads

    def generate_bash_script(self):
        dangling_heads = self.dangling_heads
        regroup_git_commands = []
        current_command = (
            f"git fetch origin {dangling_heads[0]}"
            f":refs/remotes/origin/dangling-{dangling_heads[0][:10]}"
        )
        next_command = (
            f"git fetch origin {dangling_heads[0]}"
            f":refs/remotes/origin/dangling-{dangling_heads[0][:10]}"
        )
        i = 1
        while i < len(dangling_heads):
            while len(next_command) < 4096 and i < len(dangling_heads):
                current_command = next_command
                next_command = (
                    current_command
                    + f" {dangling_heads[i]}"
                    + f":refs/remotes/origin/dangling-{dangling_heads[i][:10]}"
                )
                i += 1
            if len(next_command) < 4096:
                continue
            else:
                regroup_git_commands.append(current_command)
                next_command = (
                    f"git fetch origin {dangling_heads[i-1]}"
                    f":refs/remotes/origin/dangling-{dangling_heads[i-1][:10]}"
                )
        regroup_git_commands.append(next_command)
        return "\n".join(regroup_git_commands)

    def generate_git_config(self):
        dangling_heads = self.dangling_heads
        template = f"""
        [remote "dangling-REPLACE"]
        \turl = git@github.com:{self.owner}/{self.repo}.git
        \tfetch = REPLACE:refs/remotes/origin/dangling-REPLACE"""
        template = dedent(template)
        git_config = [
            template.replace("REPLACE", hash) for hash in dangling_heads
        ]
        return "\n".join(git_config)

    def output(self):
        if self.bash_script:
            return self.generate_bash_script()
        elif self.git_config:
            return self.generate_git_config()
        return json.dumps(self.json_dangling_heads, indent=4)
