# Script para la integración entre Github y ChatGPT
# flake8: noqa: E231


import base64
import logging
import openai
import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# Repository data
OWNER: str = "OscHer"
REPO: str = "C.U.N.Y.A.I."
BRANCH: str = "devel"

# GitHub API headers
AUTH_TOKEN: str = f"token {GITHUB_TOKEN}"
HEADERS: Dict[str, str] = {"Authorization": AUTH_TOKEN}
#logging.info(f"🔑 Github token Loaded: {bool(GITHUB_TOKEN)}")

# Logging configuration
# TODO-oscar: get logging level from variable or parameter
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def get_repo_files() -> List[str]:
    """Retrieve list of repository files.

    Returns
    -------
    List[str]
        List of file paths in the repository.
    """

    url: str = (
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees/"
        f"{BRANCH}?recursive=1"
    )

    logging.info(f"🔍 Fetching repository file list from {url}")

    response: requests.Response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        files = [
            file["path"]
            for file in response.json().get("tree", [])
            if file["type"] == "blob"
        ]
        logging.info(f"📂 Found {len(files)} files: {files}.")
        return files  # No need to break since we're returning

    logging.error(f"❌ Error fetching repository files: {response.json()}")
    return []



def get_file_content(file_path: str) -> str:
    """Retrieve the content of a file from the repository.

    Parameters
    ----------
    file_path : str
        Path of the file to retrieve.

    Returns
    -------
    str
        Decoded file content.
    """

    url: str = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{file_path}?ref={BRANCH}"
    logging.info(f"📥 Fetching content from: {url}")

    response: requests.Response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        file_data: Dict[str, Any] = response.json()
        return base64.b64decode(file_data["content"]).decode("utf-8")

    logging.error(f"❌ Error fetching {file_path}: {response.json()}")
    return ""

def analyze_code_with_gpt(file_name: str, file_content: str) -> str:
    """Analyze a code file using GPT-4.

    Parameters
    ----------
    file_name : str
        Name of the file.
    file_content : str
        Content of the file.

    Returns
    -------
    str
        Analysis result from GPT.
    """

    if not file_content.strip():  # Avoid empty files
        logging.error(f"⚠️  File {file_name} is empty or could not be read.")
        return f"⚠️  File {file_name} is empty or could not be read."

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(  # New API
        model="gpt-4",  # TODO-oscar: abstract models available
        messages=[
            {
                "role": "system",
                "content": "You ar an AI assistant that reviews code and \
                suggests improvements.",
            },
            {
                "role": "user",
                "content": (
                    f"Analyze the code in file '{file_name}' and "
                    f"suggest improvements:\n\n{file_content}"
                ),
            },
        ],
    )

    return response.choices[0].message.content


# Main: Execute analysis for all files in the repository
if __name__ == "__main__":
    logging.info("🔍 Getting files from the repository...")
    files: List[str] = get_repo_files()

    if not files:
        logging.error("❌ No files found in the repository.")
    else:
        logging.info(f"📂 Found {len(files)} files. Analyzing each one...")
        for file in files:
            logging.info(f"🔍 Analyzing file: {file}")
            content: str = get_file_content(file)

            if not content:
                logging.warning("⚠️  Could not retrive content of {file}.")
                continue

            result: str = analyze_code_with_gpt(file, content)
            logging.info(f"📝 Analysis for {file}:\n{result}")

