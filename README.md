# GitHub influence factors counter

GitHub influence factors counter를 활용하면 Repositories, Members, Contributors, Stars, Forks, Watches, Commits, Followers, Following과 같은 영향요인의 수를 보다 편하게 확인할 수 있습니다. :thumbsup:   
Open Source Software (OSS) 관련 프로젝트에서 편리하게 활용하시기 바랍니다. :smile:   

**OSS 연구/개발 프로젝트에서 Commit 하나 하나의 가치는 중요하지만 Commit 마다 정성적인 가치는 다릅니다.**   
**만약 본 프로그램을 평가에 활용하신다면, <ins>정성적인 가치 평가를 꼭 함께 수행하시기를 기원합니다.</ins>**  :pray:

Organization의 영향요인 측정 및 User의 영향요인 측정을 구분하여 개발 하였습니다.

## Prerequities
- python 3.8 에서 테스트하였습니다.
- clone후 import되어 있는 packages를 별도 설치 바랍니다.

## 사용방법
### 조직(Organization)의 영향요인 측정
#### 소스코드 내려 받기

`git clone`을 통해 소스 코드를 내려 받습니다.

```bash
git clone https://github.com/yunkon-kim/github-influence-factors-counter.git
```

#### 실행 환경 구성

참고 - 최초 한번만 수행하면 되는 사항입니다.

##### `venv` 환경 설절

`venv`를 설정 합니다. `./venv` 디렉토리가 생성되고 `venv` 관련 사항들이 설치됩니다.
```bash
python3 -m venv ./venv
```

`venv` 활성화
```bash
source .venv/bin/activate
```

##### Python 모듈 설치

```bash
pip install -r requirements.txt
```


#### 3. `auth.json` 생성
GitHub API 사용에 Rating limit이 있기 때문에 설정 하는 것이 좋습니다.   
아래 양식을 바탕으로 `auth.json`을 `orgs.py` 또는 `users.py`가 있는 위치에 생성합니다.   
```json
{
  "username": "xxxxxxx",
  "personal-access-token": "xxxxxxx"
}
```

#### 3. `orgs.json`에 자신의 레포지토리를 기입합니다.
"Name"을 아래와 같이 기입 합니다.
```json
[
  {
    "Name": "cloud-barista"
  }
]
```

#### 4. 실행후 결과 생성
`orgs.py` 실행 후 잠시 기다리면 아래 두가지 결과를 얻을 수 있습니다. (Excel로 열어서 작업하시면 편하실거에요.)

결과1:
`./results/orgs-result.csv` 는 Organization, Repositories, Members를 포함합니다. 

결과2:
`./results/org-repos-result.csv`는 Repository, Contributors, Stars, Forks, Watches, Commits(year)을 포함합니다. 


### 유저(User)의 영향요인 측정
#### 1. 본 레포지토리를 `clone`합니다.
#### 2. `auth.json` 생성
GitHub API 사용에 Rating limit이 있기 때문에 설정 하는 것이 좋습니다.   
아래 양식을 바탕으로 `auth.json`을 `orgs.py` 또는 `users.py`가 있는 위치에 생성합니다.   
```json
{
  "username": "xxxxxxx",
  "personal-access-token": "xxxxxxx"
}
```

#### 3. `users.json`에 정보를 기입합니다.
"username"과 "is_filtered_by_name"을 아래와 같이 기입 합니다. "is_filtered_by_name"은 각 레포지토리에서 해당 User의 Commit만 측정하기 위한 값 입니다. 
```json
[
  {
    "username": "hermitkim1",
    "is_filtered_by_name": true
  }
]
```

#### 4. 실행후 결과 생성
`user.py` 실행 후 잠시 기다리면 아래 두가지 결과를 얻을 수 있습니다. (Excel로 열어서 작업하시면 편하실거에요.)

결과1:
`./results/users-result.csv` 는 User, Repositories, Follwers, Following를 포함합니다. 

결과2:
`./results/user-repos-result.csv`는 Repository, Contributors, Starts, Forks, Watches, Commits(year)을 포함합니다. 
