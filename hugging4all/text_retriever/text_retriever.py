import datetime
import json
import os
import re
import tarfile

import emoji
import requests
import yaml
from termcolor import colored
from transformers import pipeline

# Load configurations from yaml file
with open("text_retriever/config.yaml", "r") as stream:
    config = yaml.safe_load(stream)

# Initialize the summarizer with the model from the config
summarizer_model = config["summarizer_model"]
summarizer = pipeline("summarization", model=summarizer_model)

# Get the GitHub token from the environment variables
github_token = os.getenv("GITHUB_TOKEN")
if github_token is None:
    raise ValueError("GITHUB_TOKEN is not set in the environment variables.")

# The headers for API requests
headers = {
    "Authorization": f"Bearer {github_token}",
    "Accept": "application/vnd.github.v3.raw",
}

# Get the current date and format it as yyyy_mm_dd
current_date = datetime.date.today().strftime("%Y_%m_%d")

# Define the output file name
jsonl_file_name = f"data/docs_en_{current_date}.jsonl"

# Ensure 'data/' directory exists, otherwise create it
if not os.path.exists("data/"):
    os.makedirs("data/")

# If a file with the same date exists, remove it
if os.path.exists(jsonl_file_name):
    os.remove(jsonl_file_name)

# The function to download a file from a given URL and save it in JSONL format
def download_file(url, repo_info):
    # Send a request to the URL
    response = requests.get(url)

    # Extract the filename from the URL
    filename = url.split("/")[-1]

    text = response.text

    if text is not None and isinstance(text, str):
        # Remove all content inside < > (HTML tags)
        text = re.sub(r"<[^>]*>", "", text)

        # Remove all URLs
        text = re.sub(r"http\S+|www.\S+", "", text)

        # Remove all content starting with "Copyright"
        text = re.sub(r"Copyright.*", "", text)

        # Replace "\n" with a space
        text = text.replace("\n", " ")

        # Remove emojis
        text = emoji.demojize(text)
        text = re.sub(r":[a-z_&+-]+:", "", text)

        # Split the text into code and non-code
        sequences = re.split(
            r"(```.*?```)", text
        )  # split by the code markers but keep the markers
        for i in range(len(sequences)):
            if sequences[i].startswith("```"):  # it is a code sequence, leave as is
                continue
            else:  # non-code text, apply summarization
                sequences[i] = summarizer(
                    sequences[i], max_length=130, min_length=30, do_sample=False
                )[0]["summary_text"]

        # Join the code and summarized non-code text
        summarized_text = " ".join(sequences)

        # Remove multiple spaces
        summarized_text = re.sub(r"\s+", " ", summarized_text)

        # Remove unnecessary white spaces
        summarized_text = summarized_text.strip()

        # Prepare the dictionary for JSONL
        file_dict = {
            "title": filename,
            "repo_owner": repo_info["owner"],
            "repo_name": repo_info["repo"],
            "text": summarized_text,  # use summarized text here
        }

        # Write the dictionary to the JSONL file
        with open(jsonl_file_name, "a") as jsonl_file:
            jsonl_file.write(json.dumps(file_dict) + "\n")
    else:
        print(f"Unexpected response text: {text}")


def process_directory(path, repo_info):
    base_url = f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}/contents/"
    print(colored(f"Processing directory: {path} of repo: {repo_info['repo']}", "blue"))
    response = requests.get(base_url + path, headers=headers)

    # Check the status of the request
    if response.status_code == 200:
        files = response.json()
        for file in files:
            if file["type"] == "file" and (
                file["name"].endswith(".mdx") or file["name"].endswith(".md")
            ):
                print(colored(f"Downloading file: {file['name']}", "green"))
                print(colored(f"Download URL: {file['download_url']}", "cyan"))
                download_file(file["download_url"], repo_info)
            elif file["type"] == "dir":
                process_directory(file["path"], repo_info)
        print(colored("Successfully retrieved files from the directory.", "green"))
    else:
        print(
            colored(
                "Failed to retrieve files. Please check your GitHub token and the repo details.",
                "red",
            )
        )


# Iterate over all repos in the config
for repo_info in config["github"]["repos"]:
    process_directory(repo_info["path"], repo_info)

# After processing all directories, compress the jsonl file to tar
with tarfile.open(f"data/docs_en_{current_date}.tar", "w") as tar:
    tar.add(jsonl_file_name)
    print(colored("Successfully compressed the JSONL file.", "green"))
