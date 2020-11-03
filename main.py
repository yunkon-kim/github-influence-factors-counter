import csv
import datetime
import json
from datetime import date

import requests
from dateutil.relativedelta import relativedelta

if __name__ == '__main__':

    with open('auth.json') as auth_file:
        auth_info = json.load(auth_file)

    username = auth_info["username"]
    password = auth_info["password"]

    auth_file.close()

    today = date.today()
    this_year = today.year

    # Authentication
    gh_session = requests.Session()
    gh_session.auth = (username, password)

    # Rate limiting: https://developer.github.com/v3/#rate-limiting
    orgs_api_root = "https://api.github.com/orgs/"
    repos_api_root = "http://api.github.com/repos/"

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

    #############################################################################
    # Result of organization
    orgs_result_file = open("orgs-result.csv", "w", newline="")
    orgs_result_writer = csv.writer(orgs_result_file)

    # Header
    orgs_result_writer.writerow(["Organization", "Repositories", "Members"])

    # Read repos
    with open('org.json') as orgs_file:
        orgs = json.load(orgs_file)

    org_link = orgs_api_root + orgs["Name"]
    org_info = json.loads(gh_session.get(org_link).text)

    members_link = orgs_api_root + orgs["Name"] + "/members"
    members_info = json.loads(gh_session.get(members_link).text)
    print("Organization name: %s" % org_info["name"])
    print("Public repos: %s" % (org_info["public_repos"]))
    print("Members: %s" % (len(members_info)))

    orgs_result_writer.writerow([org_info["name"], org_info["public_repos"], len(members_info)])

    orgs_result_file.close()
    orgs_file.close()

    #############################################################################
    # Results of each repository
    repos_result_file = open("repos-result.csv", "w", newline="")
    repos_result_writer = csv.writer(repos_result_file)

    # Header
    repos_result_writer.writerow(
        ["Repo", "Contributors", "Stars", "Forks", "Watches", "Commits(" + str(this_year) + ")"])

    # Read repos
    with open('repos.json') as json_file:
        repos = json.load(json_file)

    for repo in repos:
        print("\n%s(%s)" % (repo["Name"], repo["Path"]))
        repo_link = repos_api_root + repo["Path"]

        # Request repository statistics/information to get the number of stars, forks, watches
        repo_info = json.loads(gh_session.get(repo_link).text)
        # pretty_json = json.dumps(repo_info, indent=4, sort_keys=True)
        # print(pretty_json)

        contributors_link = repo_info["contributors_url"]
        contributors = json.loads(gh_session.get(contributors_link).text)
        number_of_contributors = len(contributors)

        # Request the number of monthly commits
        # reference: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-commits
        today = date.today()
        this_year = today.year
        start_date = datetime.date(this_year, 1, 1)
        start_date.strftime('%Y-%m-%d')
        end_date = datetime.date(this_year, 1, 31)
        end_date.strftime('%Y-%m-%d')

        number_of_commits = []

        while end_date < today:
            # print(start_date)
            # print(end_date)
            commit_link = repos_api_root + repo["Path"] + "/commits?since=" + start_date.strftime(
                '%Y-%m-%d') + "&until=" + end_date.strftime('%Y-%m-%d')

            # with urllib.request.urlopen(commit_link) as commit_url:
            #     commits = json.loads(commit_url.read().decode())
            commits = json.loads(gh_session.get(commit_link).text)
            number_of_commits.append(int(len(commits)))

            start_date = start_date + relativedelta(months=1)
            end_date = end_date + relativedelta(months=1)

        commit_link2 = repos_api_root + repo["Path"] + "/commits?since=" + start_date.strftime(
            '%Y-%m-%d') + "&until=" + today.strftime('%Y-%m-%d')
        # with urllib.request.urlopen(commit_link2) as commit_url2:
        #     commits2 = json.loads(commit_url2.read().decode())
        commits2 = json.loads(gh_session.get(commit_link2).text)
        number_of_commits.append(int(len(commits2)))

        print("Contributors: %s" % number_of_contributors)
        print("Stars: %s" % (repo_info["stargazers_count"]))
        print("Forks: %s" % (repo_info["forks_count"]))
        print("Watches: %s" % (repo_info["subscribers_count"]))
        print("Commits in this year: %s" % (sum(number_of_commits)))

        repos_result_writer.writerow(
            [repo["Name"], number_of_contributors, repo_info["stargazers_count"], repo_info["forks_count"],
             repo_info["subscribers_count"],
             sum(number_of_commits)])

    json_file.close()
    repos_result_file.close()
    gh_session.close()
