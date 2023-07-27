from dotenv import load_dotenv
import openai
import os
import subprocess
import rich
from rich.logging import RichHandler
from dataclasses import dataclass
import logging
import tempfile
import json
import argparse

log_level = logging.getLevelName(os.getenv("LOG_LEVEL", "INFO"))

logging.basicConfig(
    level=logging.DEBUG,
    # colored format
    format="%(message)s",
    datefmt="[%X]",
    handlers=[rich.logging.RichHandler(rich_tracebacks=True)]
)
logging.getLogger('openai').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")


def main(multiline: bool = False):
    proc = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True)
    if proc.returncode != 0:
        if proc.stderr.startswith("warning: Not a git repository."):
            logging.error("Not a git repository")
            exit(1)
        logging.error(f"git diff failed: {proc.stderr}")
        exit(1)
    logging.debug(f"git diff: {proc.stdout}")
    if proc.stdout == "":
        logging.info("No changes")
        exit(0)

    # This string is not a python comment.
    description = \
        """
        # This function generates a commit message from the output of `git diff`.
        # Generate a commit message that is generally considered desirable.
        # return value is json string.
        # Use prefix which is generally used in commit message.
        # It is desirable to write following 5w1h.
        # content of json string is a list of dict.
        # return in yaml which can read with `json.load()`
        # One commit per logical change.
        # First letter of first line should be capitalized.
        # Do not end the first line with a period.
        # Do not end `message` with blank line.
        # If `multiline` is True, `message` should be multiline string.
        # return value example
        # [
        #   {
        #    "message": <commit message>,
        #    "files": ["file1", "file2"]
        #   },
        #   <same format as above>
        # ]
        """

    fn_args = proc.stdout
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are now the following python function:```{description}"
                                          f"\ngenerate_commit_msg(diff:str,multiline:bool=False) -> str```\n\nOnly respond with your `return` value.\nNot python code."
                                          f"\nOther text will be ignored."},
            {"role": "user", "content": f"diff={fn_args},multiline={multiline}"},
        ]
    )
    try:
        commits = json.loads(result.choices[0]["message"]["content"])
    except json.JSONDecodeError:
        logging.error(f"Failed to parse yaml: {result.choices[0]['message']['content']}")
        exit(1)
    except KeyError:
        logging.error(f"Failed to get output from Openai")
        exit(1)
    console = rich.console.Console()
    commit_count = 0
    skipped_count = 0
    error_count = 0
    while commits:
        table = rich.table.Table(title="Commits")
        table.add_column("#")
        table.add_column("Message")
        table.add_column("Files")
        for i, commit in enumerate(commits):
            table.add_row(str(i), commit.get("message", ""), "\n".join(commit["files"]))
        console.print(table)
        index = input("Select commit: ")
        confirm = input("Confirm? [(y)es/(n)o/(e)dit]: ")
        if confirm == "y":
            proc = subprocess.run(
                ["git", "commit","-q", "-m", commits[int(index)]["message"], "--", *commits[int(index)]["files"]],
                capture_output=True, text=True)
            if proc.returncode != 0:
                commits.pop(int(index))
                error_count += 1
                logging.error(f"git commit failed: {proc.stderr}")
                continue
            logging.debug(f"git commit: {proc.stdout}")
            commits.pop(int(index))
            commit_count += 1
            continue
        elif confirm == "n":
            commits.pop(int(index))
            skipped_count += 1
            continue
        elif confirm == "e":
            with tempfile.NamedTemporaryFile(mode="w+") as f:
                f.write(commits[int(index)]["message"])
                f.flush()
                subprocess.run([os.getenv("EDITOR", "code"), f.name], shell=True)
                input("When you are done, press enter to continue")
                f.seek(0)
                commits[int(index)]["message"] = f.read()
            continue
        else:
            print("Unknown command")
            continue
    console.print(f"Commits: {commit_count}, Skipped: {skipped_count}, Errors: {error_count}")


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description="Generate commit message from git diff")
        parser.add_argument("--multiline", "-m", action="store_true", help="If set, commit message will be multiline",
                            default=False)
        args = parser.parse_args()
        main(multiline=args.multiline)
    except KeyboardInterrupt:
        print("Interrupted")
        exit(0)
