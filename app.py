import asyncio
import json
import os
import uuid

import streamlit as st

from src.github_release import GitHubClient, parse_repo_input
from src.gpt import create_gpt_client

DATA_DIR = "data"
REPOS_FILE = os.path.join(DATA_DIR, "repos.json")


def ensure_data_file() -> None:
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(REPOS_FILE):
        with open(REPOS_FILE, "w") as f:
            json.dump({}, f)  # Initialize with an empty JSON object


def get_session_id() -> str:
    # Generate a unique session ID if it doesn't exist
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id


def read_repos(session_id: str) -> list[str]:
    ensure_data_file()
    with open(REPOS_FILE, "r") as f:
        data = json.load(f)
    return data.get(session_id, [])


def add_repo(session_id: str, repo_str: str) -> tuple[bool, str]:
    try:
        username, repo = parse_repo_input(repo_str)
    except ValueError:
        return False, "Invalid repository format."

    ensure_data_file()
    with open(REPOS_FILE, "r") as f:
        data = json.load(f)

    repos = data.get(session_id, [])
    new_repo = f"{username}/{repo}"
    if new_repo in repos:
        return False, "Repository already exists."

    repos.append(new_repo)
    data[session_id] = repos

    with open(REPOS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return True, "Repository added."


def remove_repo(session_id: str, repo_str: str) -> tuple[bool, str]:
    ensure_data_file()
    with open(REPOS_FILE, "r") as f:
        data = json.load(f)

    repos = data.get(session_id, [])
    if repo_str not in repos:
        return False, "Repository not found."

    repos.remove(repo_str)
    data[session_id] = repos

    with open(REPOS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return True, "Repository removed."


async def main() -> None:
    st.set_page_config(page_title="GitHub Release Summarizer", layout="wide")
    st.title("GitHub Release Summarizer")
    st.markdown("This app summarizes recent GitHub release changes using GPT (default language: English).")

    session_id = get_session_id()

    # Sidebar Settings
    st.sidebar.header("Settings")
    language = st.sidebar.selectbox(
        "Output Language",
        options=["English", "繁體中文zh-tw", "簡體中文zh-cn", "Spanish", "French", "German"],
        index=0
    )

    # GPT Provider Settings
    st.sidebar.subheader("GPT Provider Settings")
    gpt_provider = st.sidebar.selectbox("Select GPT Provider", options=["OpenAI", "ZhipuAI"], index=0)
    gpt_api_key = ""
    if gpt_provider == "OpenAI":
        if "openai" in st.secrets and "api_key" in st.secrets["openai"]:
            gpt_api_key = st.secrets["openai"]["api_key"]
        else:
            gpt_api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")
    else:  # gpt_provider == "ZhipuAI"
        if "zhipuai" in st.secrets and "api_key" in st.secrets["zhipuai"]:
            gpt_api_key = st.secrets["zhipuai"]["api_key"]
        else:
            gpt_api_key = st.sidebar.text_input("Enter ZhipuAI API Key", type="password")

    # Repository Manager in Sidebar
    st.sidebar.subheader("Repository Manager")
    add_input = st.sidebar.text_input("Add repository (username/repo or URL)", key="add_repo_input")
    if st.sidebar.button("Add Repository"):
        if add_input:
            success, message = add_repo(session_id, add_input)
            if success:
                st.sidebar.success(message)
                st.session_state.pop("add_repo_input", None)
            else:
                st.sidebar.error(message)
        else:
            st.sidebar.error("Please enter a repository.")

    repos = read_repos(session_id)
    if repos:
        st.sidebar.markdown("### Current Repositories")
        repo_to_remove = st.sidebar.selectbox("Select repository to remove", options=[""] + repos, key="remove_repo")
        if repo_to_remove and st.sidebar.button("Remove Repository"):
            success, message = remove_repo(session_id, repo_to_remove)
            if success:
                st.sidebar.success(message)
                st.experimental_rerun()
            else:
                st.sidebar.error(message)
    else:
        st.sidebar.info("No repositories saved.")

    # Main area: Summarization Settings
    st.markdown("### Summarization Settings")
    n_days = st.number_input("Enter number of days", min_value=1, max_value=365, value=7)

    if st.button("Summarize All Repositories"):
        repos = read_repos(session_id)
        if not repos:
            st.error("No repositories saved in file.")
            return

        # Create the GPT client using the selected provider.
        try:
            gpt_client = create_gpt_client(gpt_provider, gpt_api_key)
        except Exception as e:
            st.error(f"Error creating GPT client: {e}")
            return

        # Process each repository
        for repo_str in repos:
            st.markdown(f"#### Repository: {repo_str}")
            try:
                username, repo = parse_repo_input(repo_str)
            except ValueError as e:
                st.error(f"Invalid repository format for {repo_str}: {e}")
                continue
            st.info(f"Fetching GitHub releases for {repo_str}...")
            try:
                releases = await GitHubClient(username, repo).get_recent_releases(n_days)
                if not releases:
                    st.error("No releases found or GitHub API returned 403. Skipping summarization for this repository.")
                    continue
            except Exception as e:
                if "403" in str(e):
                    st.error("GitHub API rate limit exceeded (403). Skipping summarization for this repository.")
                    continue
                else:
                    st.error(f"Error fetching data for {repo_str}: {e}")
                    continue

            st.info("Generating summary from GPT...")
            placeholder = st.empty()
            summary_text = ""
            async for chunk in gpt_client.stream_summary(
                json.dumps(releases, ensure_ascii=False, indent=2),
                n_days,
                language=language
            ):
                summary_text += chunk
                placeholder.markdown(summary_text)
            st.markdown("---")


if __name__ == "__main__":
    asyncio.run(main())
