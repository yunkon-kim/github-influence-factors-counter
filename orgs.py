import csv
import datetime
import json
import logging
import os
import sys
import urllib.parse
from datetime import date

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta

##############################################################################
# Constants
BASE_URL_OF_ORGS_API = "https://api.github.com/orgs/"
REPOS_API_URL = "http://api.github.com/repos/"
PER_PAGE_100 = "100"  # Default 30, Max 100
# Rate limiting: https://developer.github.com/v3/#rate-limiting

##############################################################################
# Logging

# Create a logger
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

# Create handlers: one for file and one for stdout
file_handler = logging.FileHandler("app.log")
stdout_handler = logging.StreamHandler()

# Set logging level for each handler (optional, can be different for each handler)
file_handler.setLevel(logging.DEBUG)
stdout_handler.setLevel(logging.INFO)

# Create a formatter with caller details and set it for both handlers
# This will include file name, function name, and line number
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s"
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
since = config["since"]
until = config["until"]

config_file.close()

try:
    # Convert 'since' and 'until' to datetime.date objects
    since = datetime.datetime.strptime(since, "%Y-%m-%d").date()
    until = datetime.datetime.strptime(until, "%Y-%m-%d").date()
except ValueError:
    print("Invalid date format. Please make sure the date format is YYYY-MM-DD.")
    sys.exit(1)

##############################################################################
# Create a session
gh_session = requests.Session()


def request_github_api(url, params=None):
    global gh_session
    """
    Makes a request to a specified GitHub API endpoint and fetches data.

    :param url: URL of the GitHub API endpoint.
    :param params: Dictionary of query parameters (optional).
    :return: JSON response from the API if successful, otherwise raises an exception.
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


def get_orgs_info(orgs_name):
    global BASE_URL_OF_ORGS_API, PER_PAGE_100
    ###########################################################################
    # Result of organization information

    # Request organization information
    orgs_url = BASE_URL_OF_ORGS_API + orgs_name
    try:
        # Request GitHub API
        response_json = request_github_api(orgs_url)
    except Exception as e:
        # Handle any errors that occurred during the API request.
        print("Error occurred: ", e)
    org_info = response_json

    # Request organization members
    params = {"per_page": PER_PAGE_100}
    # e.g., "members_url":
    # "https://api.github.com/orgs/cloud-barista/members{/member}"
    members_url = org_info["members_url"].split("{")[0]

    try:
        # Request GitHub API
        response_json = request_github_api(members_url, params)
    except Exception as e:
        # Handle any errors that occurred during the API request.
        logger.error("Error occurred: ", e)

    members_info = response_json

    logger.debug("Organization name: %s" % org_info["name"])
    logger.debug("Public repos: %s" % (org_info["public_repos"]))
    logger.debug("Members: %s" % (len(members_info)))

    # Create a file for results
    orgs_result_file = open("./results/orgs-info.csv", "w", newline="")
    orgs_result_writer = csv.writer(orgs_result_file)

    # CSV header
    orgs_result_writer.writerow(["Organization", "Public repositories", "Members"])
    orgs_result_writer.writerow(
        [org_info["name"], org_info["public_repos"], len(members_info)]
    )

    orgs_result_file.close()

    return org_info


def get_contributors(url_contributors):
    number_of_contributors = 0
    page = 1
    while True:
        params = {"page": str(page), "per_page": PER_PAGE_100}

        try:
            # Request GitHub API
            response_json = request_github_api(url_contributors, params)
        except Exception as e:
            # Handle any errors that occurred during the API request.
            logger.error("Error occurred: ", e)

        contributors = response_json
        num = len(contributors)

        if num == 0:
            break

        number_of_contributors += num
        page += 1

    return number_of_contributors


def get_commits_during_the_period(url_commits, since, until):
    total_commits_count = 0
    page = 1

    while True:
        params = {
            "since": since,
            "until": until,
            "page": str(page),
            "per_page": PER_PAGE_100,
        }

        try:
            # Request GitHub API
            response_json = request_github_api(url_commits, params)
        except Exception as e:
            # Handle any errors that occurred during the API request.
            logger.error("Error occurred: ", e)

        commits = response_json

        num = int(len(commits))
        logger.debug("Number of commits in a page: %s" % num)

        if num == 0:
            break

        total_commits_count += num
        page += 1

    return total_commits_count


def get_issues_since(url_issues, state, since):
    global PER_PAGE_100
    page = 1
    closed_issues_count = 0

    while True:
        params = {
            "state": state,
            "since": since,
            "page": page,
            "per_page": PER_PAGE_100,
        }

        try:
            # Request GitHub API
            response_json = request_github_api(url_issues, params)
        except Exception as e:
            # Handle any errors that occurred during the API request.
            logger.error("Error occurred: ", e)

        issues = response_json

        # Break loop if no issues are returned
        if not issues:
            break

        # Count issues closed in the period
        closed_issues_count += sum(1 for issue in issues if "pull_request" not in issue)

        page += 1

    return closed_issues_count


def get_prs_since(url_prs, state, since):
    global PER_PAGE_100
    page = 1
    closed_prs_count = 0

    while True:
        params = {
            "state": state,
            "since": since,
            "page": page,
            "per_page": PER_PAGE_100,
        }

        try:
            # Request GitHub API
            response_json = request_github_api(url_prs, params)
        except Exception as e:
            # Handle any errors that occurred during the API request.
            logger.error("Error occurred: ", e)

        issues = response_json

        # Break loop if no issues are returned
        if not issues:
            break

        # Count issues closed in the period
        closed_prs_count += sum(1 for issue in issues if "pull_request" in issue)

        page += 1

    return closed_prs_count


def get_target_repos_info(repos_url, target_repos):
    global org_name, since, until, gh_session, REPOS_API_URL, PER_PAGE_100

    ##########################################################################
    # Target repos information

    outputfile_name = (
        "./results/("
        + org_name
        + ")repos-statistics-rawdata-"
        + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".csv"
    )

    logger.info("Output file: %s" % outputfile_name)

    # Create a file for results
    logger.debug("Create a file for results")
    orgs_result_file = open(outputfile_name, "w", newline="")
    orgs_result_writer = csv.writer(orgs_result_file)

    # CSV header
    headers = [
        "Repo",
        "Repo link",
        f"Commits since {since} until {until}",
        "Forks total",
        "Stars total",
        f"Issues (closed) since {since}",
        f"Pull requests (closed) since {since}",
        "Contributors",
    ]

    # Write header
    orgs_result_writer.writerow(headers)

    # Setup a dataframe for statistics
    df_repos_info = pd.DataFrame(columns=headers)

    # Read repos from a repos_url from organization
    logger.debug("Read repos from a repos_url from organization")
    params = {"per_page": PER_PAGE_100}
    repos = request_github_api(repos_url, params)

    for repo in repos:
        if repo["name"] not in target_repos:
            logger.debug("Skip repo: %s" % repo["name"])
            continue

        logger.info("Starting to get %s's info" % repo["name"])

        # Request repository statistics/information
        # to get the number of stars, forks, watches
        logger.info("Get this repository information")
        repo_api_url = REPOS_API_URL + repo["full_name"]
        repo_info = request_github_api(repo_api_url)

        # Request the number of contributors
        logger.info("Get the number of contributors")
        number_of_contributors = get_contributors(repo_info["contributors_url"])

        # Request the number of commits
        # reference:
        # https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-commits

        logger.info("Get the number of commits since %s until %s" % (since, until))
        commits_url = REPOS_API_URL + repo["full_name"] + "/commits"
        number_of_commits = get_commits_during_the_period(commits_url, since, until)

        # logger.info("Get the number of forks since %s" % since)
        # forks_url = repo_info["forks_url"]
        # number_of_forks = get_forks_since(forks_url, since)

        logger.info("Get the number of issues closed since %s" % since)
        issues_url = REPOS_API_URL + repo["full_name"] + "/issues"
        number_of_issues_closed = get_issues_since(issues_url, "closed", since)

        logger.info("Get the number of pull requests closed since %s" % since)
        # prs_url = REPOS_API_URL + repo["full_name"] + "/pulls"
        number_of_prs_closed = get_prs_since(issues_url, "closed", since)

        # repo_name = repo["name"]
        repo_link = "https://github.com/" + repo["full_name"]

        logger.debug("Repo name: %s" % repo_info["name"])
        logger.debug("Repo link: %s" % repo_link)
        logger.debug(
            "Commits (since %s until %s): %s" % (since, until, number_of_commits)
        )
        logger.debug("Forks: %s" % (repo_info["forks_count"]))
        logger.debug("Stars: %s" % (repo_info["stargazers_count"]))
        logger.debug("Issues closed (since %s): %s" % (since, number_of_issues_closed))
        logger.debug(
            "Pull requests closed (since %s): %s" % (since, number_of_prs_closed)
        )
        logger.debug("Contributors: %s" % number_of_contributors)
        # logger.debug("Forks (since %s): %s" % (since, number_of_forks))
        # logger.debug("Watches: %s" % (repo_info["subscribers_count"]))

        row = [
            repo_info["name"],
            repo_link,
            number_of_commits,
            repo_info["forks_count"],
            repo_info["stargazers_count"],
            number_of_issues_closed,
            number_of_prs_closed,
            number_of_contributors,
        ]
        #     repo_info["subscribers_count"],
        # ]

        df_repos_info.loc[len(df_repos_info)] = row

        orgs_result_writer.writerow(row)

    # Sum all rows for each column except column 0 and 1
    column_sums = df_repos_info.iloc[:, 2:].sum(axis=0)
    row = pd.Series(["Sum", "-"])._append(column_sums)

    orgs_result_writer.writerow(row)

    logger.info("Saved all repos info")
    orgs_result_file.close()

    return df_repos_info


if __name__ == "__main__":
    logger.info("Starting to get organization information")

    # global gh_session, org_name, repositories, username, personal_access_token

    if repositories:
        logger.info("Target repositories: %s" % repositories)

    # # Get today's date
    # today = date.today()
    # this_year = today.year

    # Set auth info
    gh_session.auth = (username, personal_access_token)

    # Get organization information
    logger.info("Getting organization information")
    org_info = get_orgs_info(org_name)

    logger.info("Getting target repositories information")
    df_repos_info = get_target_repos_info(org_info["repos_url"], repositories)

    # get_repos_commits(org_info["repos_url"], repos_ignore)
    # get_monthly_commits(org_info["repos_url"], repos_ignore)

    gh_session.close()

##################################################################
##################################################################
##################################################################
# Keep this code

# Test code - GitHub API example
#  http://api.github.com/repos/[username]/[reponame]
# link = "http://api.github.com/repos/cloud-barista/cb-spider"
# data = json.loads(gh_session.get(link).text)
# pretty_json = json.dumps(data, indent=4, sort_keys=True)
# print(pretty_json)
#
# print("Stars: %s" % (data["stargazers_count"]))
# print("Forks: %s" % (data["forks_count"]))
# print("Watches: %s" % (data["subscribers_count"]))


def get_all_repos_info(repos_url):
    global org_name, since, until, gh_session, REPOS_API_URL, PER_PAGE_100

    ##########################################################################
    # Target repos information

    outputfile_name = (
        "./results/("
        + org_name
        + ")repos-statistics-rawdata-"
        + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".csv"
    )

    logger.info("Output file: %s" % outputfile_name)

    # Create a file for results
    logger.debug("Create a file for results")
    orgs_result_file = open(outputfile_name, "w", newline="")
    orgs_result_writer = csv.writer(orgs_result_file)

    # CSV header
    headers = [
        "Repo",
        "Repo link",
        f"Commits since {since} until {until}",
        "Forks total",
        "Stars total",
        f"Issues (closed) since {since}",
        f"Pull requests (closed) since {since}",
        "Contributors",
    ]

    # Write header
    orgs_result_writer.writerow(headers)

    # Setup a dataframe for statistics
    df_repos_info = pd.DataFrame(columns=headers)

    # Read repos from a repos_url from organization
    logger.debug("Read repos from a repos_url from organization")
    params = {"per_page": PER_PAGE_100}
    repos = request_github_api(repos_url, params)

    for repo in repos:
        logger.info("Starting to get %s's info" % repo["name"])

        # Request repository statistics/information
        # to get the number of stars, forks, watches
        logger.info("Get this repository information")
        repo_api_url = REPOS_API_URL + repo["full_name"]
        repo_info = request_github_api(repo_api_url)

        # Request the number of contributors
        logger.info("Get the number of contributors")
        number_of_contributors = get_contributors(repo_info["contributors_url"])

        # Request the number of commits
        # reference:
        # https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-commits

        logger.info("Get the number of commits since %s until %s" % (since, until))
        commits_url = REPOS_API_URL + repo["full_name"] + "/commits"
        number_of_commits = get_commits_during_the_period(commits_url, since, until)

        # logger.info("Get the number of forks since %s" % since)
        # forks_url = repo_info["forks_url"]
        # number_of_forks = get_forks_since(forks_url, since)

        logger.info("Get the number of issues closed since %s" % since)
        issues_url = REPOS_API_URL + repo["full_name"] + "/issues"
        number_of_issues_closed = get_issues_since(issues_url, "closed", since)

        logger.info("Get the number of pull requests closed since %s" % since)
        # prs_url = REPOS_API_URL + repo["full_name"] + "/pulls"
        number_of_prs_closed = get_prs_since(issues_url, "closed", since)

        # repo_name = repo["name"]
        repo_link = "https://github.com/" + repo["full_name"]

        logger.debug("Repo name: %s" % repo_info["name"])
        logger.debug("Repo link: %s" % repo_link)
        logger.debug(
            "Commits (since %s until %s): %s" % (since, until, number_of_commits)
        )
        logger.debug("Forks: %s" % (repo_info["forks_count"]))
        logger.debug("Stars: %s" % (repo_info["stargazers_count"]))
        logger.debug("Issues closed (since %s): %s" % (since, number_of_issues_closed))
        logger.debug(
            "Pull requests closed (since %s): %s" % (since, number_of_prs_closed)
        )
        logger.debug("Contributors: %s" % number_of_contributors)
        # logger.debug("Forks (since %s): %s" % (since, number_of_forks))
        # logger.debug("Watches: %s" % (repo_info["subscribers_count"]))

        row = [
            repo_info["name"],
            repo_link,
            number_of_commits,
            repo_info["forks_count"],
            repo_info["stargazers_count"],
            number_of_issues_closed,
            number_of_prs_closed,
            number_of_contributors,
        ]
        #     repo_info["subscribers_count"],
        # ]

        df_repos_info.loc[len(df_repos_info)] = row

        orgs_result_writer.writerow(row)

    # Sum all rows for each column except column 0 and 1
    column_sums = df_repos_info.iloc[:, 2:].sum(axis=0)
    row = pd.Series(["Sum", "-"])._append(column_sums)

    orgs_result_writer.writerow(row)

    logger.info("Saved all repos info")
    orgs_result_file.close()

    return df_repos_info


def get_prs(url_prs, state):
    number_of_prs = 0
    page = 1

    while True:
        params = {
            "page": str(page),
            "per_page": PER_PAGE_100,
            "state": state,
        }

        request_url = url_prs + "?" + urllib.parse.urlencode(params)
        prs = json.loads(gh_session.get(request_url).text)
        num = int(len(prs))
        logger.debug(urllib.parse.urlencode(params))
        logger.debug("Number of commits in a page: %s" % num)

        if num == 0:
            break

        number_of_prs += num
        page += 1

    return number_of_prs


def get_monthly_commits(repos_url, repos_ignore):
    global since, until

    params = {"per_page": PER_PAGE_100}
    request_url = repos_url + "?" + urllib.parse.urlencode(params)

    # Read repos from a repos_url from organization
    repos = json.loads(gh_session.get(request_url).text)
    logger.debug(repos)

    monthly_commits_of_repos = []

    for repo in repos:
        if repo["name"] in repos_ignore:
            print("Ignore repo: %s" % repo["name"])
            continue

        print("Start to get %s's info" % repo["name"])

        # Request the number of monthly commits
        # reference:
        # https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-commits

        today = date.today()
        delta = relativedelta(months=1)
        first_day_of_the_month = since
        last_day_of_the_month = first_day_of_the_month + delta
        # - datetime.timedelta(days=1)

        number_of_commits = []

        commits_url = REPOS_API_URL + repo["full_name"] + "/commits"
        while last_day_of_the_month < today and last_day_of_the_month < until:
            # page iteration is necessary because a page show max 100 commits
            commits_in_a_month = get_commits_during_the_period(
                commits_url, first_day_of_the_month, last_day_of_the_month
            )

            number_of_commits.append(commits_in_a_month)

            first_day_of_the_month = first_day_of_the_month + delta
            last_day_of_the_month = first_day_of_the_month + delta
            # - datetime.timedelta(days=1)

        commits_in_a_month = get_commits_during_the_period(
            commits_url, first_day_of_the_month, until
        )

        number_of_commits.append(commits_in_a_month)

        temp = [
            repo["name"],
        ]
        temp.extend(number_of_commits)
        monthly_commits_of_repos.append(temp)

    ###########################################################################
    # Repositories' monthly commits in the period
    org_repos_monthly_commits_file = open(
        "./results/org-monthly-commits.csv", "w", newline=""
    )
    org_repos_monthly_commits_writer = csv.writer(org_repos_monthly_commits_file)

    # Create header
    header = [
        "YYYY-MM",
    ]
    year_month = since

    while year_month <= until:
        header.append(year_month.strftime("%Y-%m"))
        year_month = year_month + relativedelta(months=1)

    header.append("Sum")

    # Write header
    org_repos_monthly_commits_writer.writerow(header)

    # Write data
    # Data structure in a row :
    # [repo name, commits[0], commits[1], ......, sum of commits]
    for monthly_commits_of_a_repo in monthly_commits_of_repos:
        # Create row, e.g., [repo name, commits[0], .... commits[n]]
        row = monthly_commits_of_a_repo
        row.extend(
            [sum(monthly_commits_of_a_repo[1:])]
        )  # [repo name, commits[0], .... commits[n], sum of commits]

        # Write row
        org_repos_monthly_commits_writer.writerow(row)

    org_repos_monthly_commits_file.close()


def get_repos_commits(repos_url, repos_ignore):
    global since, until

    params = {"per_page": PER_PAGE_100}
    request_url = repos_url + "?" + urllib.parse.urlencode(params)

    # Read repos from a repos_url from organization
    repos = json.loads(gh_session.get(request_url).text)
    logger.debug(repos)

    headers = [
        "Repo",
        "Commits",
    ]

    # repos_result_writer.writerow(headers)

    df_repos_info = pd.DataFrame(columns=headers)

    for repo in repos:
        if repo["name"] in repos_ignore:
            print("Ignore repo: %s" % repo["name"])
            continue

        print("Start to get %s's info" % repo["name"])

        repo_api_url = REPOS_API_URL + repo["full_name"]

        # Request repository statistics/information
        # to get the number of stars, forks, watches
        repo_info = json.loads(gh_session.get(repo_api_url).text)

        commits_url = REPOS_API_URL + repo["full_name"] + "/commits"
        repo_commits = get_commits_during_the_period(commits_url, since, until)

        df_repos_info.loc[len(df_repos_info)] = [
            repo_info["name"],
            repo_commits,
        ]

    print("Save all repos info")
    outputfile_name = (
        "./results/("
        + org_name
        + ")repos-commits-rawdata-"
        + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".csv"
    )
    df_repos_info.to_csv(outputfile_name, mode="w", header=True, index=False)


def get_forks_since(url_forks, since):
    number_of_forks_in_a_month = 0

    params = {"per_page": PER_PAGE_100}

    request_url = url_forks + "?" + urllib.parse.urlencode(params)
    forks = json.loads(gh_session.get(request_url).text)

    for fork in forks:
        create_at = datetime.datetime.strptime(fork["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        create_at = create_at.date()
        if create_at >= since:
            number_of_forks_in_a_month += 1
        else:
            break

    return number_of_forks_in_a_month
