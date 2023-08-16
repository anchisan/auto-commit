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
from sys import exit
import tiktoken

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")


def main(multiline: bool = False, debug: bool = False, model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k"),
         granularity: float = 0.5):
    # logger setup
    logging.basicConfig(
        level="DEBUG" if debug else os.getenv("LOG_LEVEL", "INFO"),
        # colored format
        format="%(message)s",
        datefmt="[%X]",
        handlers=[rich.logging.RichHandler(rich_tracebacks=True)]
    )
    proc = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True, encoding="utf-8")
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

    description = \
        """
        # This function generates a commit message from the output of `git diff`.
        # Generate a commit message that is generally considered desirable.
        # If arg multiline is True, the commit message will be multiline.
        # return value is json string.
        # Use prefix which is generally used in commit message.
        # It is desirable to write following 5w1h.
        # content of json string is a list of dict.
        # return in yaml which can read with `json.load()`
        # One commit per logical change.
        # argument `granularity` is granularity of commit. max:1 min:0 higher is more granular.
        # First letter of first line should be capitalized.
        # DO NOT end the first line with a period.
        # DO NOT end `message` with blank line.
        # return value example
        # [
        #   {
        #    "message": <commit message>,
        #    "files": ["file1", "file2"]
        #   },
        #   <same format>
        # ]
        """
    fn_args = proc.stdout
    messages = [
        {"role": "system", "content": f"You are now the following python function:```{description}"
                                      f"\ngenerate_commit_msg(diff:str,multiline:bool=False) -> str```\n\nOnly respond with your `return` value.\nNot python code."
                                      f"\nOther text will be ignored."},
        {"role": "user", "content": f"diff={fn_args},multiline={multiline},granularity={granularity}"},
    ]

    token_len = len(tiktoken.encoding_for_model(model).encode("\n".join([m["content"] for m in messages])))
    logging.debug(f"tokens: {token_len}")
    if "gpt-4" in model and token_len > 8192:
        logging.warning(f"Token length is {token_len}, which is over 8192. Using gpt-4-32k instead.")
        model = model.replace("gpt-4", "gpt-4-32k")
    elif "gpt-3.5-turbo" in model and token_len > 4096:
        logging.warning(f"Token length is {token_len}, which is over 4096. Using gpt-3.5-turbo-16k instead.")
        model = model.replace("gpt-3.5-turbo", "gpt-3.5-turbo-16k")
    elif "16k" or "32k" in model:
        pass

    result = openai.ChatCompletion.create(
        model=model,
        messages=messages
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
        table = rich.table.Table(title="Commit Suggestions")
        table.add_column("#")
        table.add_column("Message")
        table.add_column("Files")
        for i, commit in enumerate(commits):
            message = commit.get("message", "").rstrip()
            # if message is multiline, only show first line
            if not multiline:
                message = message.split("\n")[0]
            files = commit.get("files", [])
            table.add_row(str(i), message, "\n".join(files))
        console.print(table)
        index = input("Select commit: ")
        confirm = input("Confirm? [(y)es/(n)o/(e)dit]: ")
        if confirm == "y":
            message = commits[int(index)].get("message", "").rstrip()
            # if message is multiline, only show first line
            if not multiline:
                message = message.split("\n")[0]
            files = commits[int(index)].get("files", [])
            proc = subprocess.run(
                ["git", "commit", "-q", "-m", message, "--", *files],
                capture_output=True, text=True, encoding="utf-8")
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
                editor = os.getenv("EDITOR", "code --wait")
                logging.info("Waiting for editor to close...")
                subprocess.run([editor, f.name], shell=True)
                if "--wait" not in editor:
                    # if editor does not support --wait, wait for user to close editor
                    input("When you are done, press enter to continue")
                f.seek(0)
                commits[int(index)]["message"] = f.read()
            continue
        else:
            print("Unknown command")
            continue
    console.print(
        f"Commits: {commit_count}, Skipped: [yellow]{skipped_count}[/yellow], Errors: [red]{error_count}[/red]"
    )


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description="Generate commit message from git diff")
        parser.add_argument("--multiline", "-M", action="store_true", help="If set, commit message will be multiline")
        parser.add_argument("--debug", "-d", action="store_true", help="If set, debug log will be shown")
        parser.add_argument("--model", "-m", default="gpt-3.5-turbo", help="OpenAI model to use")
        parser.add_argument("--granularity", "-g", default=0.5, type=float, help="Granularity of commit")
        args = parser.parse_args()
        main(multiline=args.multiline, debug=args.debug, model=args.model, granularity=args.granularity)
    except KeyboardInterrupt:
        print("Interrupted")
        exit(0)
