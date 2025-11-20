import csv
import datetime
import json
import logging
import os
import sys

import requests

##############################################################################
# Constants
REPOS_API_URL = "http://api.github.com/repos/"
PER_PAGE_100 = "100"  # Default 30, Max 100

##############################################################################
# Logging

# Create a logger
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

# Create handlers: one for file and one for stdout
file_handler = logging.FileHandler("app.log")
stdout_handler = logging.StreamHandler()

# Set logging level for each handler
file_handler.setLevel(logging.DEBUG)
stdout_handler.setLevel(logging.INFO)

# Create a formatter with caller details and set it for both handlers
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - " "[%(filename)s:%(funcName)s:%(lineno)d] - %(message)s"
)
file_handler.setFormatter(formatter)
stdout_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stdout_handler)

##############################################################################
# Read configs

# Create a directory for results
directory = os.path.join("results")
os.makedirs(directory, exist_ok=True)

# Read auth.json
with open("auth.json") as auth_file:
    auth_info = json.load(auth_file)

username = auth_info["username"]
personal_access_token = auth_info["personal-access-token"]

auth_file.close()

# Read config.json file
with open("config.json") as config_file:
    config = json.load(config_file)

org_name = config["org-name"]
repositories = config["repositories"]

config_file.close()

##############################################################################
# Create a session
gh_session = requests.Session()


def request_github_api(url, params=None):
    global gh_session
    """
    Makes a request to a specified GitHub API endpoint and fetches data.

    :param url: URL of the GitHub API endpoint.
    :param params: Dictionary of query parameters (optional).
    :return: JSON response from the API if successful,
             otherwise raises an exception.
    """

    logger.debug("Request URL: %s" % url)
    logger.debug("Request params: %s" % params)

    try:
        response = gh_session.get(url, params=params)

        # Check if the request was successful.
        if response.status_code == 200:
            return response.json()

        # Handle rate limit exceeded error.
        elif response.status_code == 403:
            raise Exception("API request rate limit exceeded.")

        # Handle other errors.
        else:
            raise Exception(f"API error: {response.status_code}")

    except requests.exceptions.RequestException as e:
        # Handle network errors.
        raise Exception(f"Network error: {e}")


def get_all_contributors_from_repo(owner, repo_name):
    """
    Fetch all contributors from a specific repository.
    Returns a dict with username as key and type info as value.
    """
    contributors_dict = {}
    page = 1

    while True:
        contributors_url = f"{REPOS_API_URL}{owner}/{repo_name}/contributors"
        params = {"page": str(page), "per_page": PER_PAGE_100}

        try:
            response_json = request_github_api(contributors_url, params)
        except Exception as e:
            logger.error(f"Error fetching contributors for {repo_name}: {e}")
            break

        if not response_json or len(response_json) == 0:
            break

        for contributor in response_json:
            username = contributor.get("login", "")
            contributor_type = contributor.get("type", "")
            if username:
                contributors_dict[username] = contributor_type

        page += 1

    logger.info(f"Found {len(contributors_dict)} contributors in {repo_name}")
    return contributors_dict


def collect_unique_contributors(org_name, repositories):
    """
    Collect all unique contributors from specified repositories.
    Uses username as key to avoid duplicates.
    Returns a dictionary with username as key and user info as value.
    """
    unique_contributors = {}
    failed_users = []
    repo_contributor_counts = {}

    logger.info(f"Collecting contributors from {len(repositories)} repos")

    for repo_name in repositories:
        logger.info(f"Processing repository: {repo_name}")

        contributors = get_all_contributors_from_repo(org_name, repo_name)
        repo_contributor_counts[repo_name] = len(contributors)

        for username, contributor_type in contributors.items():
            if username not in unique_contributors:
                # Define project-specific bot accounts
                project_bots = ["cb-spider", "cb-github-robot", "fossabot"]

                # Classify special accounts
                if username == "Copilot":
                    user_type = "Agent"
                    logger.info(f"Classified {username} as Agent")
                    unique_contributors[username] = {
                        "username": username,
                        "name": "",
                        "email": "",
                        "type": user_type,
                        "repo_count": 1,
                        "repositories": [repo_name],
                    }
                elif contributor_type == "Bot" or username in project_bots:
                    user_type = "Bot"
                    logger.info(f"Classified {username} as Bot")
                    unique_contributors[username] = {
                        "username": username,
                        "name": "",
                        "email": "",
                        "type": user_type,
                        "repo_count": 1,
                        "repositories": [repo_name],
                    }
                else:
                    # Fetch detailed user info only for regular users
                    user_url = f"https://api.github.com/users/{username}"
                    try:
                        user_data = request_github_api(user_url)
                        user_type = user_data.get("type", "User")

                        unique_contributors[username] = {
                            "username": username,
                            "name": user_data.get("name", ""),
                            "email": user_data.get("email", ""),
                            "type": user_type,
                            "repo_count": 1,
                            "repositories": [repo_name],
                        }
                        logger.debug(f"Added contributor: {username} (type: {user_type})")
                    except Exception as e:
                        logger.error(f"Error fetching user {username}: {e}")
                        failed_users.append(username)
                        # Still add with basic info for verification
                        unique_contributors[username] = {
                            "username": username,
                            "name": "",
                            "email": "",
                            "type": "Unknown (API Error)",
                            "repo_count": 1,
                            "repositories": [repo_name],
                        }
            else:
                # User already exists, increment repo count
                unique_contributors[username]["repo_count"] += 1
                unique_contributors[username]["repositories"].append(repo_name)

    logger.info(f"Total unique contributors: {len(unique_contributors)}")
    if failed_users:
        logger.warning(f"Failed to fetch details for {len(failed_users)} users: " f"{', '.join(failed_users)}")

    return unique_contributors, repo_contributor_counts, failed_users


def save_contributors_to_csv(contributors_dict, org_name):
    """Save unique contributors to a CSV file."""
    output_filename = (
        f"./results/({org_name})unique-contributors-" f"{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
    )

    with open(output_filename, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Username", "Name", "Email", "Type", "Repo Count", "Repositories"])

        # Sort by repo_count descending
        for username, info in sorted(
            contributors_dict.items(),
            key=lambda x: x[1].get("repo_count", 0),
            reverse=True,
        ):
            repos_list = ", ".join(info.get("repositories", []))
            writer.writerow(
                [
                    username,
                    info["name"],
                    info["email"],
                    info.get("type", "User"),
                    info.get("repo_count", 1),
                    repos_list,
                ]
            )

    logger.info(f"Contributors saved to {output_filename}")
    return output_filename


def print_validation_report(unique_contributors, repo_counts, failed_users):
    """Print a validation report of the collected data."""
    report_lines = []

    report_lines.append("=" * 70)
    report_lines.append("VALIDATION REPORT")
    report_lines.append("=" * 70)
    report_lines.append("")
    report_lines.append("=" * 60)
    report_lines.append(f"Organization: {org_name}")
    report_lines.append(f"Total repositories analyzed: {len(repo_counts)}")

    # Calculate totals first
    total_contributors_sum = sum(repo_counts.values())

    report_lines.append(f"Total contributors (with duplicates)                  : {total_contributors_sum}")
    report_lines.append(f"Total unique contributors: {len(unique_contributors)}")
    report_lines.append("=" * 60)

    # Repository breakdown
    report_lines.append("\nRepository Contributor Counts:")
    report_lines.append("-" * 70)
    for repo, count in sorted(repo_counts.items(), key=lambda x: x[1], reverse=True):
        report_lines.append(f"  {repo:40} : {count:3} contributors")

    # Contribution distribution
    report_lines.append("\nContributor Distribution by Repo Count:")
    report_lines.append("-" * 70)
    repo_count_distribution = {}
    for info in unique_contributors.values():
        count = info.get("repo_count", 1)
        repo_count_distribution[count] = repo_count_distribution.get(count, 0) + 1

    for repo_count in sorted(repo_count_distribution.keys(), reverse=True):
        contributor_count = repo_count_distribution[repo_count]
        report_lines.append(f"  {repo_count:2} repos : {contributor_count:3} contributors")

    # Top contributors
    report_lines.append("\nTop 15 Multi-repo Contributors:")
    report_lines.append("-" * 70)
    sorted_contributors = sorted(
        unique_contributors.items(),
        key=lambda x: x[1].get("repo_count", 0),
        reverse=True,
    )
    # Filter only User type
    user_contributors = [(u, i) for u, i in sorted_contributors if i.get("type") == "User"]
    for i, (username, info) in enumerate(user_contributors[:15]):
        name = info.get("name") or "N/A"
        repo_count = info.get("repo_count", 1)
        report_lines.append(f"  {i+1:2}. {username:20} ({name:20}) : {repo_count:2} repos")

    # Failed fetches
    if failed_users:
        report_lines.append("\nFailed API Fetches:")
        report_lines.append("-" * 70)
        for username in failed_users:
            user_info = unique_contributors.get(username, {})
            user_type = user_info.get("type", "Unknown")
            report_lines.append(f"  {username:40} : {user_type}")
        report_lines.append(f"\n  Total failed: {len(failed_users)}")

    # Contributors with missing info
    report_lines.append("\nContributors with Missing Information:")
    report_lines.append("-" * 70)
    missing_name = [u for u, i in unique_contributors.items() if not i.get("name")]
    missing_email = [u for u, i in unique_contributors.items() if not i.get("email")]

    report_lines.append(f"  Missing name  : {len(missing_name):3}")
    report_lines.append(f"  Missing email : {len(missing_email):3}")

    report_lines.append("\n" + "=" * 70)

    # Print to console
    print("\n" + "\n".join(report_lines))

    return report_lines


def save_report_to_markdown(report_lines, org_name, unique_contributors, repo_counts, failed_users):
    """Save the validation report to a markdown file."""
    output_filename = (
        f"./results/({org_name})unique-contributors-report-" f"{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    )

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(f"# Contributor Analysis Report - {org_name}\n\n")
        f.write(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        # Summary section
        f.write("## Summary\n\n")
        total_contributors_sum = sum(repo_counts.values())
        f.write(f"- **Total Repositories Analyzed:** {len(repo_counts)}\n")
        f.write(f"- **Total Contributors (with duplicates):** {total_contributors_sum}\n")

        # Count contributors by type
        type_counts = {}
        for info in unique_contributors.values():
            user_type = info.get("type", "Unknown")
            type_counts[user_type] = type_counts.get(user_type, 0) + 1

        f.write(f"- **Unique Contributors:** {len(unique_contributors)}\n")
        for user_type in ["User", "Bot", "Agent"]:
            if user_type in type_counts:
                f.write(f"  - {user_type}: {type_counts[user_type]}\n")
        # Add any other types that might exist
        for user_type, count in sorted(type_counts.items()):
            if user_type not in ["User", "Bot", "Agent"]:
                f.write(f"  - {user_type}: {count}\n")
        f.write("\n")

        # Repository breakdown
        f.write("## Repository Contributor Counts\n\n")
        f.write("| Repository | Contributors |\n")
        f.write("|------------|-------------:|\n")
        for repo, count in sorted(repo_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"| {repo} | {count} |\n")

        # Top contributors
        f.write("\n## Top 15 Multi-repo Contributors\n\n")
        sorted_contributors = sorted(
            unique_contributors.items(),
            key=lambda x: x[1].get("repo_count", 0),
            reverse=True,
        )
        # Filter only User type
        user_contributors = [(u, i) for u, i in sorted_contributors if i.get("type") == "User"]
        f.write("| Rank | Username | Name | Repo Count |\n")
        f.write("|-----:|----------|------|----------:|\n")
        for i, (username, info) in enumerate(user_contributors[:15]):
            name = info.get("name", "N/A")
            repo_count = info.get("repo_count", 1)
            f.write(f"| {i+1} | {username} | {name} | {repo_count} |\n")

        # Failed fetches
        if failed_users:
            f.write("\n## Failed API Fetches\n\n")
            f.write("| Username | Status |\n")
            f.write("|----------|--------|\n")
            for username in failed_users:
                user_info = unique_contributors.get(username, {})
                user_type = user_info.get("type", "Unknown")
                f.write(f"| {username} | {user_type} |\n")

        # Missing info
        f.write("\n## Contributors with Missing Information\n\n")
        missing_name = [u for u, i in unique_contributors.items() if not i.get("name")]
        missing_email = [u for u, i in unique_contributors.items() if not i.get("email")]

        f.write(f"- **Missing name:** {len(missing_name)}\n")
        f.write(f"- **Missing email:** {len(missing_email)}\n")

    logger.info(f"Report saved to {output_filename}")
    return output_filename


if __name__ == "__main__":
    logger.info("Starting to count unique contributors")

    if repositories:
        logger.info(f"Target repositories: {repositories}")
    else:
        logger.error("No repositories specified in config.json")
        sys.exit(1)

    # Set auth info
    gh_session.auth = (username, personal_access_token)

    # Collect unique contributors
    logger.info(f"Collecting contributors from organization: {org_name}")
    result = collect_unique_contributors(org_name, repositories)
    unique_contributors, repo_counts, failed_users = result

    # Display summary
    print("\n" + "=" * 60)
    print(f"Organization: {org_name}")
    print(f"Total repositories analyzed: {len(repositories)}")
    print(f"Total unique contributors: {len(unique_contributors)}")
    print("=" * 60 + "\n")

    # Save results to CSV
    output_file = save_contributors_to_csv(unique_contributors, org_name)
    print(f"Results saved to: {output_file}")

    # Display sample of contributors (first 10)
    print("\nSample of contributors (first 10):")
    print("-" * 70)
    sample_items = list(unique_contributors.items())[:10]
    for i, (username, info) in enumerate(sample_items):
        name = info["name"] if info["name"] else "N/A"
        repo_count = info.get("repo_count", 1)
        user_type = info.get("type", "User")
        print(f"{i+1}. {username:20} | {name:20} | {repo_count:2} repos")

    if len(unique_contributors) > 10:
        print(f"... and {len(unique_contributors) - 10} more")

    # Print validation report
    report_lines = print_validation_report(unique_contributors, repo_counts, failed_users)

    # Save report to markdown
    report_file = save_report_to_markdown(report_lines, org_name, unique_contributors, repo_counts, failed_users)
    print(f"\nReport saved to: {report_file}")

    gh_session.close()
    logger.info("Process completed successfully")
