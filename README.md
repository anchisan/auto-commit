# Git Commit Message Generator

This script generates commit messages for Git repositories based on the changes made in the working directory. It utilizes the OpenAI GPT-3.5 Turbo model to provide descriptive and relevant commit messages for each logical change.

# Installation
[Windows(latest)](https://github.com/anchisan/auto-commit/releases/download/v1.0.0/auto-commit.exe)


# Installation(manual)
Before using the Git Commit Message Generator, make sure you have the required dependencies installed:

- Python (version 3.6 or higher)
- OpenAI Python library
- Git

You can install the Python dependencies using pip:

```bash
pip install python-dotenv openai rich
```
Ensure that you have set up the OpenAI API key as an environment variable (OPENAI_API_KEY) to access the GPT-3.5 Turbo model.

To use the Git Commit Message Generator, simply run the script from your terminal:


```python
python main.py
```

# Optional Arguments:

`--multiline (-m)`: If set, the commit message will be allowed to be multiline.
The script will interactively guide you through the process of selecting and creating commit messages based on the changes in your Git repository.

# License
This project is licensed under the MIT License - see the LICENSE file for details.

# Disclaimer
The Git Commit Message Generator script uses the OpenAI GPT-3.5 Turbo model for generating commit messages. OpenAI's GPT models are powerful language models, but they may not always produce optimal or desired results. Use the generated commit messages with caution and review them before committing to your repository. The author of this script and OpenAI are not responsible for any issues caused by the generated commit messages.
