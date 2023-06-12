import yaml
import requests
import os
import json
import datetime
from termcolor import colored
import tarfile
from tqdm import tqdm

# Load configurations from yaml file
with open("text_retriever/config.yaml", 'r') as stream:
    config = yaml.safe_load(stream)

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
if not os.path.exists('data/'):
    os.makedirs('data/')

# If a file with the same date exists, remove it
if os.path.exists(jsonl_file_name):
    os.remove(jsonl_file_name)

# The function to download a file from a given URL and save it in JSONL format
def download_file(url, repo_info):
    # Send a request to the URL
    response = requests.get(url)

    # Extract the filename from the URL
    filename = url.split("/")[-1]

    # Prepare the dictionary for JSONL
    file_dict = {
        "title": filename,
        "repo_owner": repo_info['owner'],
        "repo_name": repo_info['repo'],
        "text": response.text
    }

    # Write the dictionary to the JSONL file
    with open(jsonl_file_name, 'a') as jsonl_file:
        jsonl_file.write(json.dumps(file_dict) + '\n')

def process_directory(path, repo_info):
    base_url = f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}/contents/"
    print(colored(f"Processing directory: {path} of repo: {repo_info['repo']}", "blue"))
    response = requests.get(base_url + path, headers=headers)

    # Check the status of the request
    if response.status_code == 200:
        files = response.json()
        for file in tqdm(files, desc="Processing files", unit="file"):
            if file["type"] == "file" and (file["name"].endswith(".mdx") or file["name"].endswith(".md")):
                print(colored(f"Downloading file: {file['name']}", "green"))
                print(colored(f"Download URL: {file['download_url']}", "cyan"))
                download_file(file["download_url"], repo_info)
            elif file["type"] == "dir":
                process_directory(file["path"], repo_info)
        print(colored("Successfully retrieved files from the directory.", "green"))
    else:
        print(colored("Failed to retrieve files. Please check your GitHub token and the repo details.", "red"))

# Iterate over all repos in the config
for repo_info in config['github']['repos']:
    process_directory(repo_info['path'], repo_info)

# After processing all directories, compress the jsonl file to tar
with tarfile.open(f"data/docs_en_{current_date}.tar", "w") as tar:
    tar.add(jsonl_file_name)
    print(colored("Successfully compressed the JSONL file.", "green"))

# Remove the original jsonl file after compressing it
# os.remove(jsonl_file_name)
