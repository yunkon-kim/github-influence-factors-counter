import csv
import datetime
import json
from datetime import date

import requests
from dateutil.relativedelta import relativedelta

DAY_GAP = 4


def get_commits_per_month(link, first_day, last_day, name, is_filtered_by_name):
    number_of_commits_in_a_month = 0
    page = 1

    while True:
        commit_link = link + "/commits?since=" + first_day.strftime('%Y-%m-%d') + "&until=" + last_day.strftime(
            '%Y-%m-%d') + "&page=" + str(page)
        commits = json.loads(gh_session.get(commit_link).text)
        num = int(len(commits))

        if is_filtered_by_name:
            for commit in commits:
                if commit["commit"]["author"]["name"].strip() == name.strip():
                    number_of_commits_in_a_month += 1
        else:
            print("since=%s&until=%s&page=%s" % (first_day, last_day, str(page)))
            print("Number of commits in a page: %s" % num)
            number_of_commits_in_a_month += num

        if num < 30:
            break
        page += 1

    return number_of_commits_in_a_month


# start = first_day
# # end = last_day
# end = start + relativedelta(days=(DAY_GAP - 1))
#
# next_start = start + relativedelta(months=1)
#
# number_of_commits_in_a_month = 0
#
# # day loop
# while start < next_start:
#     page = 1
#     # page loop
#     while True:
#         commit_link = link + "/commits?since=" + start.strftime('%Y-%m-%d') + "&until=" + end.strftime(
#             '%Y-%m-%d') + "&page=" + str(page)
#         commits = json.loads(gh_session.get(commit_link).text)
#         num = int(len(commits))
#         print("since=%s&until=%s&page=%s" % (start, end, str(page)))
#         print("Number of commits in a page: %s" % num)
#
#         number_of_commits_in_a_month = number_of_commits_in_a_month + num
#         page = page + 1
#
#         if num < 30:
#             break
#
#     start = start + relativedelta(days=DAY_GAP)
#     end = end + relativedelta(days=DAY_GAP)
#     if end >= next_start:
#         end = next_start - datetime.timedelta(days=1)


if __name__ == '__main__':

    with open('auth.json') as auth_file:
        auth_info = json.load(auth_file)

    username = auth_info["username"]
    password = auth_info["personal-access-token"]

    auth_file.close()

    today = date.today()
    this_year = today.year

    # Authentication
    gh_session = requests.Session()
    gh_session.auth = (username, password)

    # Rate limiting: https://developer.github.com/v3/#rate-limiting
    users_api_root = "https://api.github.com/users/"
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
    users_result_file = open("./results/users-result.csv", "w", newline="")
    users_result_writer = csv.writer(users_result_file)

    # Header
    users_result_writer.writerow(["User", "Repositories", "Followers", "Following"])

    # Read repos
    with open('users.json') as users_file:
        users_json = json.load(users_file)
    users_name = users_json[0]["username"]
    is_filtered_by_name = users_json[0]["is_filtered_by_name"]

    user_link = users_api_root + users_name
    user_info = json.loads(gh_session.get(user_link).text)

    members_link = users_api_root + users_name
    members_info = json.loads(gh_session.get(members_link).text)
    print("User name: %s" % user_info["name"])
    print("Public repos: %s" % (user_info["public_repos"]))
    print("Followers: %s" % (user_info["followers"]))
    print("Following: %s" % (user_info["following"]))

    users_result_writer.writerow(
        [user_info["name"], user_info["public_repos"], user_info["followers"], user_info["following"]])

    users_result_file.close()
    users_file.close()

    #############################################################################
    # Results of each repository
    user_repos_result_file = open("./results/user-repos-result.csv", "w", newline="")
    user_repos_result_writer = csv.writer(user_repos_result_file)

    # Header
    user_repos_result_writer.writerow(
        ["Repo", "Contributors", "Stars", "Forks", "Watches", "Commits(" + str(this_year) + ")"])

    # Read repos from a repos_url from organization
    repos = json.loads(gh_session.get(user_info["repos_url"]).text)
    for repo in repos:
        print("\n%s(%s)" % (repo["name"], repo["full_name"]))

        repo_link = repos_api_root + repo["full_name"]

        # Request repository statistics/information to get the number of stars, forks, watches
        repo_info = json.loads(gh_session.get(repo_link).text)

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

            # page iteration is necessary because a page show max 100 commits
            commits_in_a_month = get_commits_per_month((repos_api_root + repo["full_name"]),
                                                       start_date, end_date, user_info["name"], is_filtered_by_name)

            # with urllib.request.urlopen(commit_link) as commit_url:
            #     commits = json.loads(commit_url.read().decode())
            # commits = json.loads(gh_session.get(commit_link).text)
            number_of_commits.append(commits_in_a_month)

            start_date = start_date + relativedelta(months=1)
            end_date = (start_date + relativedelta(months=1)) - datetime.timedelta(days=1)

        commits_in_a_month = get_commits_per_month((repos_api_root + repo["full_name"]), start_date,
                                                   end_date, user_info["name"], is_filtered_by_name)

        # with urllib.request.urlopen(commit_link2) as commit_url2:
        #     commits2 = json.loads(commit_url2.read().decode())
        # commits2 = json.loads(gh_session.get(commit_link2).text)
        number_of_commits.append(commits_in_a_month)

        print("Contributors: %s" % number_of_contributors)
        print("Stars: %s" % (repo_info["stargazers_count"]))
        print("Forks: %s" % (repo_info["forks_count"]))
        print("Watches: %s" % (repo_info["subscribers_count"]))
        print("Commits in this year: %s" % (sum(number_of_commits)))

        user_repos_result_writer.writerow(
            [repo_info["name"], number_of_contributors, repo_info["stargazers_count"], repo_info["forks_count"],
             repo_info["subscribers_count"],
             sum(number_of_commits)])

    user_repos_result_file.close()
    gh_session.close()
