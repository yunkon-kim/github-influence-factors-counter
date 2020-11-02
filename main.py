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

    # Rate limiting: https://developer.github.com/v3/#rate-limiting
    api_root = "http://api.github.com/repos/"

    # GitHub API example
    #  http://api.github.com/repos/[username]/[reponame]
    # link = "http://api.github.com/repos/cloud-barista/cb-spider"
    # with urllib.request.urlopen(link) as url:
    #     data = json.loads(url.read().decode())
    #     pretty_json = json.dumps(data, indent=4, sort_keys=True)
    #     print(pretty_json)
    #
    # print("Stars: %s" % (data["stargazers_count"]))
    # print("Forks: %s" % (data["forks_count"]))
    # print("Watches: %s" % (data["subscribers_count"]))

    result_file = open("Result.csv", "w", newline="")
    csv_writer = csv.writer(result_file)

    with open('repos.json') as json_file:
        repos = json.load(json_file)

    today = date.today()
    this_year = today.year

    csv_writer.writerow(["Repo", "Stars", "Forks", "Watches", "Commits(" + str(this_year) + ")"])
    for repo in repos:
        print("\n%s(%s)" % (repo["Name"], repo["Path"]))
        repo_link = api_root + repo["Path"]

        gh_session = requests.Session()
        gh_session.auth = (username, password)

        # Request repository statistics/information to get the number of stars, forks, watches
        repo_info = json.loads(gh_session.get(repo_link).text)
        # pretty_json = json.dumps(repo_info, indent=4, sort_keys=True)
        # print(pretty_json)

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
            commit_link = api_root + repo["Path"] + "/commits?since=" + start_date.strftime(
                '%Y-%m-%d') + "&until=" + end_date.strftime('%Y-%m-%d')

            # with urllib.request.urlopen(commit_link) as commit_url:
            #     commits = json.loads(commit_url.read().decode())
            commits = json.loads(gh_session.get(commit_link).text)
            number_of_commits.append(int(len(commits)))

            start_date = start_date + relativedelta(months=1)
            end_date = end_date + relativedelta(months=1)

        commit_link2 = api_root + repo["Path"] + "/commits?since=" + start_date.strftime(
            '%Y-%m-%d') + "&until=" + today.strftime('%Y-%m-%d')
        # with urllib.request.urlopen(commit_link2) as commit_url2:
        #     commits2 = json.loads(commit_url2.read().decode())
        commits2 = json.loads(gh_session.get(commit_link2).text)
        number_of_commits.append(int(len(commits2)))

        print("Stars: %s" % (repo_info["stargazers_count"]))
        print("Forks: %s" % (repo_info["forks_count"]))
        print("Watches: %s" % (repo_info["subscribers_count"]))
        print("Commits in this year: %s" % (sum(number_of_commits)))

        csv_writer.writerow(
            [repo["Name"], repo_info["stargazers_count"], repo_info["forks_count"], repo_info["subscribers_count"],
             sum(number_of_commits)])

    json_file.close()
    result_file.close()
    gh_session.close()
