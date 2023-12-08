import json

import requests


def get_organization_repos(org_name, access_token=None):
    """
    Get a list of repositories for a given organization.

    Parameters:
        org_name (str): Name of the organization
        access_token (str): GitHub Access Token (optional)

    Returns:
        list of str: List of repository names
    """
    url = f"https://api.github.com/orgs/{org_name}/repos?per_page=100"
    headers = {}
    if access_token:
        headers["Authorization"] = f"token {access_token}"

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        repos = response.json()
        print("Retrieved repositories successfully.")
        print(f"Number of repositories: {len(repos)}")
        return [repo["name"] for repo in repos]
    else:
        status_code = response.status_code
        text = response.text
        print(f"Failed to retrieve repos for {org_name}: {status_code}, {text}")
        return []


def main():
    # Read authentication information from a file
    with open("auth.json") as auth_file:
        auth_info = json.load(auth_file)

    personal_access_token = auth_info["personal-access-token"]

    auth_file.close()

    # Read configuration from the file
    with open("config.json", "r", encoding="utf-8") as file:
        config = json.load(file)

    org_name = config["org-name"]

    repositories = get_organization_repos(org_name, personal_access_token)

    # Print the list of repositories separated by commas
    quoted_repositories = ['"{}"'.format(repo) for repo in repositories]
    print(", ".join(quoted_repositories))


if __name__ == "__main__":
    main()
