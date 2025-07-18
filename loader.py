import os
import sys
import threading
import subprocess
from rich import print as rprint

env = os.environ.copy()
env["FORCE_COLOR"] = "1"


bot_info = [
    {
        "dir": "Taiga",
        "start": "main.py",
        "args": ["-e", ".env.prod"],
        "tag": "[Taiga]",
        "github": "https://github.com/jadenlabs/Taiga",
        "github_branch": "master",
    },
]


class CLI:
    loader = "[black][Loader][/]"
    info = "[green][INFO][/]"
    debug = "[green][DEBUG][/]"
    warning = "[yellow][WARNING][/]"


def github(dir: str, github: str, github_branch: str = "master"):
    if not os.path.exists(dir):
        rprint(
            f"{CLI.loader}{CLI.warning} Directory '{dir}' not found, cloning from {github}"
        )
        subprocess.run(
            ["git", "clone", "--branch", github_branch, github, dir], check=True
        )
        return

    git_dir = os.path.join(dir, ".git")
    if not os.path.isdir(git_dir):
        rprint(
            f"{CLI.loader}{CLI.warning} No Git repo found in {dir}, initializing one"
        )
        subprocess.run(["git", "init"], cwd=dir, check=True)
        subprocess.run(["git", "remote", "add", "origin", github], cwd=dir, check=True)
    else:
        result = subprocess.run(
            ["git", "remote"], cwd=dir, capture_output=True, text=True
        )
        if "origin" not in result.stdout:
            subprocess.run(
                ["git", "remote", "add", "origin", github], cwd=dir, check=True
            )

    subprocess.run(["git", "reset", "--hard"], cwd=dir, check=True)
    subprocess.run(["git", "clean", "-fd"], cwd=dir, check=True)

    subprocess.run(["git", "checkout", "-B", github_branch], cwd=dir, check=True)
    try:
        subprocess.run(
            ["git", "pull", "--rebase", "origin", github_branch], cwd=dir, check=True
        )
        rprint(f"{CLI.loader}{CLI.info} Pulled latest from {github}")
    except subprocess.CalledProcessError as e:
        rprint(f"{CLI.loader}{CLI.warning} Failed to pull: {e}")


def runfile(dir: str, start: str, tag: str, args: list[str] = [], **kwargs):
    full_path = os.path.join(dir, start)
    tag = kwargs.get("tag", f"[{dir}]")

    rprint(f"{CLI.loader}{CLI.info} Opening file: `{full_path}`")

    process = subprocess.Popen(
        [sys.executable, "-O", "-u", start, *args],
        cwd=dir or ".",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )

    assert process.stdout is not None

    with process.stdout:
        for line in iter(process.stdout.readline, ""):
            print(f"{tag} {line.rstrip()}")

    process.wait()
    rprint(f"{CLI.loader}{CLI.warning} File {full_path} stopped")


def main():
    # ----- IP Check for Sanity -----
    import requests

    ip = requests.get("https://api.ipify.org").text
    rprint(f"{CLI.loader}{CLI.info} Server IP:", ip)
    # -------------------------------

    rprint(f"{CLI.loader}{CLI.info} Loading {len(bot_info)} bot(s)")
    for info in bot_info:
        rprint(
            f"{CLI.loader}{CLI.info}   -  {info.get('tag', '[Unknown]')} - {info.get('dir', 'No Directory')}"
        )

    threads = []

    for kwargs in bot_info:
        if "github" in kwargs:
            github(
                kwargs["dir"], kwargs["github"], kwargs.get("github_branch", "master")
            )
        thread = threading.Thread(target=runfile, kwargs=kwargs)
        thread.start()
        threads += [thread]

    for thread in threads:
        thread.join()

    rprint(f"{CLI.loader}{CLI.warning} All files have exited, quitting.")


if __name__ == "__main__":
    main()
