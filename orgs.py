import csv
import datetime
import json
from datetime import date

import requests
from dateutil.relativedelta import relativedelta

# 'staring_date' and 'ending_date' are only needed for counting number of commits
starting_date = datetime.date(2023, 4, 1)
# starting_date.strftime('%Y-%m-%d')
ending_date = datetime.date(2023, 12, 31)
# ending_date.strftime('%Y-%m-%d')


def get_commits_per_month(link, first_day, last_day):
    number_of_commits_in_a_month = 0
    page = 1

    while True:
        commit_link = link + "/commits?since=" + first_day.strftime('%Y-%m-%d') + "&until=" + last_day.strftime(
            '%Y-%m-%d') + "&page=" + str(page)
        commits = json.loads(gh_session.get(commit_link).text)
        num = int(len(commits))
        print("since=%s&until=%s&page=%s" % (first_day, last_day, str(page)))
        print("Number of commits in a page: %s" % num)

        number_of_commits_in_a_month += num

        if num < 30:
            break
        page += 1

    return number_of_commits_in_a_month

def get_forks_after_certain_day(fork_url, starting_day):
    number_of_forks_in_a_month = 0
    
    forks = json.loads(gh_session.get(fork_url).text)

    for fork in forks:

        create_at = datetime.datetime.strptime(fork["created_at"], '%Y-%m-%dT%H:%M:%SZ')
        create_at = create_at.date()
        if create_at >= starting_day:
            number_of_forks_in_a_month += 1
        else:
            break
    
    return number_of_forks_in_a_month

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
    orgs_api_root = "https://api.github.com/orgs/"
    repos_api_root = "http://api.github.com/repos/"
    number_of_result_per_page = "100" # Default 30

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
    orgs_result_file = open("./results/orgs-result.csv", "w", newline="")
    orgs_result_writer = csv.writer(orgs_result_file)

    # Header
    orgs_result_writer.writerow(["Organization", "Public repositories", "Members"])

    # Read repos
    with open('orgs.json') as orgs_file:
        orgs_json = json.load(orgs_file)
    orgs_name = orgs_json[0]["Name"]

    org_link = orgs_api_root + orgs_name
    org_info = json.loads(gh_session.get(org_link).text)
    print(org_info)

    members_link = orgs_api_root + orgs_name + "/members"
    members_info = json.loads(gh_session.get(members_link+"?per_page="+number_of_result_per_page).text)
    print("Organization name: %s" % org_info["name"])
    print("Public repos: %s" % (org_info["public_repos"]))
    print("Members: %s" % (len(members_info)))

    orgs_result_writer.writerow([org_info["name"], org_info["public_repos"], len(members_info)])

    orgs_result_file.close()
    orgs_file.close()

    #############################################################################
    # Results of each repository
    repos_result_file = open("./results/org-repos-result.csv", "w", newline="")
    repos_result_writer = csv.writer(repos_result_file)

    # Header
    # repos_result_writer.writerow(
    #     ["Repo", "Contributors", "Stars", "Forks", "Watches", "Commits(" + str(this_year) + ")"])
    repos_result_writer.writerow(
        ["Period", starting_date, ending_date])

    repos_result_writer.writerow(
        ["Repo", "Contributors", "Stars total", "Forks total", "Watches total", "Commits during the period", "Forks during the preiod"])

    monthly_commits_of_repos = []

    # Read repos from a repos_url from organization    
    repos = json.loads(gh_session.get(org_info["repos_url"]+"?per_page="+number_of_result_per_page).text)
    print(repos)

    for repo in repos:
        print("\n%s(%s)" % (repo["name"], repo["full_name"]))

        repo_link = repos_api_root + repo["full_name"]

        # Request repository statistics/information to get the number of stars, forks, watches
        repo_info = json.loads(gh_session.get(repo_link).text)

        contributors_link = repo_info["contributors_url"]+"?per_page="+number_of_result_per_page
        contributors = json.loads(gh_session.get(contributors_link).text)
        number_of_contributors = len(contributors)

        # Request the number of monthly commits
        # reference: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-commits

        today = date.today()
        the_first_day_of_the_month = starting_date
        the_last_day_of_the_month = (the_first_day_of_the_month + relativedelta(months=1)) # - datetime.timedelta(days=1)

        number_of_commits = []

        while the_last_day_of_the_month < today and the_last_day_of_the_month < ending_date:
            # print(start_date)
            # print(end_date)

            # page iteration is necessary because a page show max 100 commits
            commits_in_a_month = get_commits_per_month((repos_api_root + repo["full_name"]),
                                                        the_first_day_of_the_month, the_last_day_of_the_month)

            # with urllib.request.urlopen(commit_link) as commit_url:
            #     commits = json.loads(commit_url.read().decode())
            # commits = json.loads(gh_session.get(commit_link).text)
            number_of_commits.append(commits_in_a_month)

            the_first_day_of_the_month = the_first_day_of_the_month + relativedelta(months=1)
            the_last_day_of_the_month = (the_first_day_of_the_month + relativedelta(months=1)) # - datetime.timedelta(days=1)

        commits_in_a_month = get_commits_per_month((repos_api_root + repo["full_name"]), the_first_day_of_the_month,
                                                    ending_date)
        
        # with urllib.request.urlopen(commit_link2) as commit_url2:
        #     commits2 = json.loads(commit_url2.read().decode())
        # commits2 = json.loads(gh_session.get(commit_link2).text)
        number_of_commits.append(commits_in_a_month)

        forks_url = repo_info["forks_url"] + "?per_page=" + number_of_result_per_page
        number_of_forks_after_certain_day = get_forks_after_certain_day(forks_url, starting_date)

        print("Contributors: %s" % number_of_contributors)
        print("Stars: %s" % (repo_info["stargazers_count"]))
        print("Forks: %s" % (repo_info["forks_count"]))
        print("Watches: %s" % (repo_info["subscribers_count"]))
        print("Commits during the period: %s" % (sum(number_of_commits)))
        print("Forks during the period: %s" % number_of_forks_after_certain_day)

        repos_result_writer.writerow(
            [repo_info["name"], number_of_contributors, repo_info["stargazers_count"], repo_info["forks_count"],
                repo_info["subscribers_count"],
                sum(number_of_commits), number_of_forks_after_certain_day])

        temp = [repo["name"], ]
        temp.extend(number_of_commits)
        monthly_commits_of_repos.append(temp)

    #############################################################################
    # Repositories' monthly commits in the period
    org_repos_monthly_commits_file = open("./results/org-monthly-commits.csv", "w", newline="")
    org_repos_monthly_commits_writer = csv.writer(org_repos_monthly_commits_file)

    # Create header
    header = ["YYYY-MM", ]
    year_month = starting_date

    while year_month <= ending_date:
        header.append(year_month.strftime('%Y-%m'))
        year_month = year_month + relativedelta(months=1)

    header.append("Sum")

    # Write header
    org_repos_monthly_commits_writer.writerow(header)

    # Write data
    # Data structure in a row : [repo name, commits[0], commits[1], ......, sum of commits]
    for monthly_commits_of_a_repo in monthly_commits_of_repos:
        # Create row
        row = monthly_commits_of_a_repo                     # [repo name, commits[0], .... commits[n]]
        row.extend([sum(monthly_commits_of_a_repo[1:])])    # [repo name, commits[0], .... commits[n], sum of commits]

        # Write row
        org_repos_monthly_commits_writer.writerow(row)

    org_repos_monthly_commits_file.close()
    repos_result_file.close()
    gh_session.close()
