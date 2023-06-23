import os
import sys

import jsonlines
import yaml
from langchain.schema import Document


class TransformersDocsJSONLLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self):
        with jsonlines.open(self.file_path) as reader:
            documents = []
            for obj in reader:
                page_content = obj.get("text", "")
                metadata = {
                    "title": obj.get("title", ""),
                    "repo_owner": obj.get("repo_owner", ""),
                    "repo_name": obj.get("repo_name", ""),
                }
                documents.append(Document(page_content=page_content, metadata=metadata))
        return documents


def load_config():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(root_dir, "config.yaml")) as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def get_openai_api_key():
    # Get the env variable OPENAI_API_KEY
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = input("Please enter your OPENAI_API_KEY: ")
    return openai_api_key


def get_cohere_api_key():
    # Get the env variable COHERE_API_KEY
    cohere_api_key = os.getenv("COHERE_API_KEY")
    if not cohere_api_key:
        cohere_api_key = input("Please enter your COHERE_API_KEY: ")
    return cohere_api_key


def get_file_path():
    # Relative path to the parent directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.join(root_dir, "..")

    # Use os.path.join to build file paths
    return os.path.join(parent_dir, "data/docs_en_2023_06_14.jsonl")


def get_query_from_user() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        print("Error: Please provide a query.")
        sys.exit(1)
