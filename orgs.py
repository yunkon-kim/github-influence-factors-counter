import csv
import datetime
import json
import logging
import os
import urllib.parse
from datetime import date

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta

logging.basicConfig(
    filename="github-influence-factors-counter.log", level=logging.DEBUG
)

# 'start_date' and 'end_date' are only needed for counting number of commits
start_date = datetime.date(2023, 4, 1)
# starting_date.strftime('%Y-%m-%d')
end_date = datetime.date(2023, 12, 8)
# ending_date.strftime('%Y-%m-%d')

# Rate limiting: https://developer.github.com/v3/#rate-limiting
BASE_URL_OF_ORGS_API = "https://api.github.com/orgs/"
REPOS_API_URL = "http://api.github.com/repos/"

PER_PAGE_100 = "100"  # Default 30, Max 100

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


def get_orgs_info(orgs_name):
    global BASE_URL_OF_ORGS_API, PER_PAGE_100
    ###########################################################################
    # Result of organization information

    # Request organization information
    orgs_url = BASE_URL_OF_ORGS_API + orgs_name
    org_info = json.loads(gh_session.get(orgs_url).text)

    # logging.debug(org_info)

    # Request organization members
    params = {"per_page": PER_PAGE_100}
    # e.g., "members_url":
    # "https://api.github.com/orgs/cloud-barista/members{/member}"
    members_url = org_info["members_url"].split("{")[0]

    request_url = members_url + "?" + urllib.parse.urlencode(params)
    members_info = json.loads(gh_session.get(request_url).text)

    logging.debug("Organization name: %s" % org_info["name"])
    logging.debug("Public repos: %s" % (org_info["public_repos"]))
    logging.debug("Members: %s" % (len(members_info)))

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


def get_contributors(contributors_url):
    number_of_contributors = 0
    page = 1
    while True:
        params = {"page": str(page), "per_page": PER_PAGE_100}

        request_url = contributors_url + "?" + urllib.parse.urlencode(params)
        contributors = json.loads(gh_session.get(request_url).text)
        num = len(contributors)

        if num == 0:
            break

        number_of_contributors += num
        page += 1

    return number_of_contributors


def get_commits_during_a_period(commit_url, start, end):
    number_of_commits_in_a_month = 0
    page = 1

    while True:
        params = {
            "since": start.strftime("%Y-%m-%d"),
            "until": end.strftime("%Y-%m-%d"),
            "page": str(page),
            "per_page": PER_PAGE_100,
        }

        request_url = commit_url + "?" + urllib.parse.urlencode(params)
        commits = json.loads(gh_session.get(request_url).text)
        num = int(len(commits))
        logging.debug(urllib.parse.urlencode(params))
        logging.debug("Number of commits in a page: %s" % num)

        if num == 0:
            break

        number_of_commits_in_a_month += num
        page += 1

    return number_of_commits_in_a_month


def get_forks_since_the_input_date(forks_url, start_date):
    number_of_forks_in_a_month = 0

    params = {"per_page": PER_PAGE_100}

    request_url = forks_url + "?" + urllib.parse.urlencode(params)
    forks = json.loads(gh_session.get(request_url).text)

    for fork in forks:
        create_at = datetime.datetime.strptime(fork["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        create_at = create_at.date()
        if create_at >= start_date:
            number_of_forks_in_a_month += 1
        else:
            break

    return number_of_forks_in_a_month


def get_issues_since(issues_url, state, start):
    global PER_PAGE_100
    page = 1
    closed_issues_count = 0

    while True:
        params = {
            "state": "closed",
            "since": start,
            "page": page,
            "per_page": PER_PAGE_100,
        }
        response = requests.get(issues_url, params=params)
        issues = response.json()

        # Break loop if no issues are returned
        print("Isseus: %s" % issues)
        if not issues:
            break

        # Count issues closed in the period
        closed_issues_count += sum(1 for issue in issues if "pull_request" not in issue)

        page += 1

    return closed_issues_count


def get_prs(prs_url, state):
    number_of_prs = 0
    page = 1

    while True:
        params = {
            "page": str(page),
            "per_page": PER_PAGE_100,
            "state": state,
        }

        request_url = prs_url + "?" + urllib.parse.urlencode(params)
        prs = json.loads(gh_session.get(request_url).text)
        num = int(len(prs))
        logging.debug(urllib.parse.urlencode(params))
        logging.debug("Number of commits in a page: %s" % num)

        if num == 0:
            break

        number_of_prs += num
        page += 1

    return number_of_prs


def get_prs_since(url, state, start):
    global PER_PAGE_100
    page = 1
    closed_prs_count = 0

    while True:
        params = {
            "state": "closed",
            "since": start,
            "page": page,
            "per_page": PER_PAGE_100,
        }
        response = requests.get(url, params=params)
        issues = response.json()

        # Break loop if no issues are returned
        print("Isseus: %s" % issues)
        if not issues:
            break

        # Count issues closed in the period
        closed_prs_count += sum(1 for issue in issues if "pull_request" in issue)

        page += 1

    return closed_prs_count


def get_all_repos_info(repos_url):
    global start_date, end_date

    ##########################################################################
    # Results of each repository
    # repos_result_file = open("./results/repos-info.csv", "w", newline="")
    # repos_result_writer = csv.writer(repos_result_file)

    # repos_result_writer.writerow(
    #     ["Period", starting_date, ending_date])

    headers = [
        "Repo",
        "Contributors",
        "Stars total",
        "Forks total",
        "Watches total",
        "Commits during the period",
        "Forks during the preiod",
        "Issues (closed) during the period",
        "Pull requests (closed) during the period",
        "Repo name",
        "Repo link",
    ]

    # repos_result_writer.writerow(headers)

    df_repos_info = pd.DataFrame(columns=headers)

    # monthly_commits_of_repos = []

    params = {"per_page": PER_PAGE_100}
    request_url = repos_url + "?" + urllib.parse.urlencode(params)

    # Read repos from a repos_url from organization
    repos = json.loads(gh_session.get(request_url).text)

    # logging.debug(repos)

    for repo in repos:
        # if target_repos and repo["name"] not in target_repos:
        #     print("Ignore repo: %s" % repo["name"])
        #     continue

        # Just for test
        # if repo["name"] != "cb-spider":
        #     continue

        print("Start to get %s's info" % repo["name"])

        repo_api_url = REPOS_API_URL + repo["full_name"]

        # Request repository statistics/information
        # to get the number of stars, forks, watches
        repo_info = json.loads(gh_session.get(repo_api_url).text)

        # Request the number of contributors
        number_of_contributors = get_contributors(repo_info["contributors_url"])

        # Request the number of monthly commits
        # reference:
        # https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-commits

        today = date.today()
        first_day_of_the_month = start_date
        last_day_of_the_month = first_day_of_the_month + relativedelta(
            months=1
        )  # - datetime.timedelta(days=1)

        number_of_commits = []

        commits_url = REPOS_API_URL + repo["full_name"] + "/commits"
        while last_day_of_the_month < today and last_day_of_the_month < end_date:
            # page iteration is necessary because a page show max 100 commits
            commits_in_a_month = get_commits_during_a_period(
                commits_url, first_day_of_the_month, last_day_of_the_month
            )

            number_of_commits.append(commits_in_a_month)

            delta = relativedelta(months=1)
            first_day_of_the_month = first_day_of_the_month + delta
            last_day_of_the_month = first_day_of_the_month + delta
            # - datetime.timedelta(days=1)

        commits_in_a_month = get_commits_during_a_period(
            commits_url, first_day_of_the_month, end_date
        )

        number_of_commits.append(commits_in_a_month)

        forks_url = repo_info["forks_url"]
        number_of_forks_after_certain_day = get_forks_since_the_input_date(
            forks_url, start_date
        )

        issues_url = REPOS_API_URL + repo["full_name"] + "/issues"
        number_of_issues_closed = get_issues_since(issues_url, "closed", start_date)

        # prs_url = REPOS_API_URL + repo["full_name"] + "/pulls"
        number_of_prs_closed = get_prs_since(issues_url, "closed", start_date)

        repo_name = repo["name"]
        repo_link = "https://github.com/" + repo["full_name"]

        logging.debug("Contributors: %s" % number_of_contributors)
        logging.debug("Stars: %s" % (repo_info["stargazers_count"]))
        logging.debug("Forks: %s" % (repo_info["forks_count"]))
        logging.debug("Watches: %s" % (repo_info["subscribers_count"]))
        logging.debug("Commits during the period: %s" % sum(number_of_commits))
        logging.debug("Forks during the period: %s" % number_of_forks_after_certain_day)
        logging.debug("Issues (closed): %s" % number_of_issues_closed)
        logging.debug("Pull requests (closed): %s" % number_of_prs_closed)
        logging.debug("Repo name: %s" % repo_name)
        logging.debug("Repo link: %s" % repo_link)

        df_repos_info.loc[len(df_repos_info)] = [
            repo_info["name"],
            number_of_contributors,
            repo_info["stargazers_count"],
            repo_info["forks_count"],
            repo_info["subscribers_count"],
            sum(number_of_commits),
            number_of_forks_after_certain_day,
            number_of_issues_closed,
            number_of_prs_closed,
            repo_name,
            repo_link,
        ]

    print("Save all repos info")
    outputfile_name = (
        "./results/("
        + org_name
        + ")repos-statistics-rawdata-"
        + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".csv"
    )
    df_repos_info.to_csv(outputfile_name, mode="w", header=True, index=False)

    return df_repos_info


def get_repos_commits(repos_url, repos_ignore):
    global start_date, end_date

    params = {"per_page": PER_PAGE_100}
    request_url = repos_url + "?" + urllib.parse.urlencode(params)

    # Read repos from a repos_url from organization
    repos = json.loads(gh_session.get(request_url).text)
    logging.debug(repos)

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
        repo_commits = get_commits_during_a_period(commits_url, start_date, end_date)

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


def get_target_repos_info(repos_url, target_repos):
    global start_date, end_date

    ##########################################################################
    # Results of each repository
    # repos_result_file = open("./results/repos-info.csv", "w", newline="")
    # repos_result_writer = csv.writer(repos_result_file)

    # repos_result_writer.writerow(
    #     ["Period", starting_date, ending_date])

    headers = [
        "Repo",
        "Contributors",
        "Stars total",
        "Forks total",
        "Watches total",
        "Commits during the period",
        "Forks during the preiod",
        "Issues (closed) during the period",
        "Pull requests (closed) during the period",
        "Repo name",
        "Repo link",
    ]

    # repos_result_writer.writerow(headers)

    df_repos_info = pd.DataFrame(columns=headers)

    # monthly_commits_of_repos = []

    params = {"per_page": PER_PAGE_100}
    request_url = repos_url + "?" + urllib.parse.urlencode(params)

    # Read repos from a repos_url from organization
    repos = json.loads(gh_session.get(request_url).text)

    # logging.debug(repos)

    for repo in repos:
        if target_repos and repo["name"] not in target_repos:
            print("Ignore repo: %s" % repo["name"])
            continue

        # Just for test
        # if repo["name"] != "cb-spider":
        #     continue

        print("Start to get %s's info" % repo["name"])

        repo_api_url = REPOS_API_URL + repo["full_name"]

        # Request repository statistics/information
        # to get the number of stars, forks, watches
        repo_info = json.loads(gh_session.get(repo_api_url).text)

        # Request the number of contributors
        number_of_contributors = get_contributors(repo_info["contributors_url"])

        # Request the number of monthly commits
        # reference:
        # https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-commits

        today = date.today()
        first_day_of_the_month = start_date
        last_day_of_the_month = first_day_of_the_month + relativedelta(
            months=1
        )  # - datetime.timedelta(days=1)

        number_of_commits = []

        commits_url = REPOS_API_URL + repo["full_name"] + "/commits"
        while last_day_of_the_month < today and last_day_of_the_month < end_date:
            # page iteration is necessary because a page show max 100 commits
            commits_in_a_month = get_commits_during_a_period(
                commits_url, first_day_of_the_month, last_day_of_the_month
            )

            number_of_commits.append(commits_in_a_month)

            delta = relativedelta(months=1)
            first_day_of_the_month = first_day_of_the_month + delta
            last_day_of_the_month = first_day_of_the_month + delta
            # - datetime.timedelta(days=1)

        commits_in_a_month = get_commits_during_a_period(
            commits_url, first_day_of_the_month, end_date
        )

        number_of_commits.append(commits_in_a_month)

        forks_url = repo_info["forks_url"]
        number_of_forks_after_certain_day = get_forks_since_the_input_date(
            forks_url, start_date
        )

        issues_url = REPOS_API_URL + repo["full_name"] + "/issues"
        number_of_issues_closed = get_issues_since(issues_url, "closed", start_date)

        # prs_url = REPOS_API_URL + repo["full_name"] + "/pulls"
        number_of_prs_closed = get_prs_since(issues_url, "closed", start_date)

        repo_name = repo["name"]
        repo_link = "https://github.com/" + repo["full_name"]

        logging.debug("Contributors: %s" % number_of_contributors)
        logging.debug("Stars: %s" % (repo_info["stargazers_count"]))
        logging.debug("Forks: %s" % (repo_info["forks_count"]))
        logging.debug("Watches: %s" % (repo_info["subscribers_count"]))
        logging.debug("Commits during the period: %s" % sum(number_of_commits))
        logging.debug("Forks during the period: %s" % number_of_forks_after_certain_day)
        logging.debug("Issues (closed): %s" % number_of_issues_closed)
        logging.debug("Pull requests (closed): %s" % number_of_prs_closed)
        logging.debug("Repo name: %s" % repo_name)
        logging.debug("Repo link: %s" % repo_link)

        df_repos_info.loc[len(df_repos_info)] = [
            repo_info["name"],
            number_of_contributors,
            repo_info["stargazers_count"],
            repo_info["forks_count"],
            repo_info["subscribers_count"],
            sum(number_of_commits),
            number_of_forks_after_certain_day,
            number_of_issues_closed,
            number_of_prs_closed,
            repo_name,
            repo_link,
        ]

    print("Save all repos info")
    outputfile_name = (
        "./results/("
        + org_name
        + ")repos-statistics-rawdata-"
        + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".csv"
    )
    df_repos_info.to_csv(outputfile_name, mode="w", header=True, index=False)

    return df_repos_info


def get_repos_commits(repos_url, repos_ignore):
    global start_date, end_date

    params = {"per_page": PER_PAGE_100}
    request_url = repos_url + "?" + urllib.parse.urlencode(params)

    # Read repos from a repos_url from organization
    repos = json.loads(gh_session.get(request_url).text)
    logging.debug(repos)

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
        repo_commits = get_commits_during_a_period(commits_url, start_date, end_date)

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


def get_monthly_commits(repos_url, repos_ignore):
    global start_date, end_date

    params = {"per_page": PER_PAGE_100}
    request_url = repos_url + "?" + urllib.parse.urlencode(params)

    # Read repos from a repos_url from organization
    repos = json.loads(gh_session.get(request_url).text)
    logging.debug(repos)

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
        first_day_of_the_month = start_date
        last_day_of_the_month = first_day_of_the_month + delta
        # - datetime.timedelta(days=1)

        number_of_commits = []

        commits_url = REPOS_API_URL + repo["full_name"] + "/commits"
        while last_day_of_the_month < today and last_day_of_the_month < end_date:
            # page iteration is necessary because a page show max 100 commits
            commits_in_a_month = get_commits_during_a_period(
                commits_url, first_day_of_the_month, last_day_of_the_month
            )

            number_of_commits.append(commits_in_a_month)

            first_day_of_the_month = first_day_of_the_month + delta
            last_day_of_the_month = first_day_of_the_month + delta
            # - datetime.timedelta(days=1)

        commits_in_a_month = get_commits_during_a_period(
            commits_url, first_day_of_the_month, end_date
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
    year_month = start_date

    while year_month <= end_date:
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


if __name__ == "__main__":
    # Create a directory for results
    directory = os.path.join("results")
    os.makedirs(directory, exist_ok=True)

    # Read authentication information from a file
    with open("auth.json") as auth_file:
        auth_info = json.load(auth_file)

    username = auth_info["username"]
    personal_access_token = auth_info["personal-access-token"]

    auth_file.close()

    # Read organization name from a file
    with open("config.json") as config_file:
        config = json.load(config_file)
    org_name = config["org-name"]
    repositories = config["repositories"]

    config_file.close()

    if repositories:
        print("Target repositories: %s" % repositories)

    # Get today's date
    today = date.today()
    this_year = today.year

    # Create a session
    gh_session = requests.Session()
    gh_session.auth = (username, personal_access_token)

    # Get organization information
    org_info = get_orgs_info(org_name)

    df_repos_info = get_target_repos_info(org_info["repos_url"], repositories)

    # get_repos_commits(org_info["repos_url"], repos_ignore)
    # get_monthly_commits(org_info["repos_url"], repos_ignore)

    gh_session.close()
