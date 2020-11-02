# GitHub influence factors counter
<ins>**GitHub influence factors counter를 활용하면 Stars, Forks, Watches, Commits와 같은 영향요인의 수를 보다 편하게 확인할 수 있습니다.**</ins>    
Open Source Software (OSS) 관련 프로젝트에서 편리하게 활용하시기 바랍니다. :smile:

## Prerequities
- python 3.8 에서 테스트하였습니다.
- clone후 import되어 있는 packages를 별도 설치 바랍니다.

## 사용방법
### 1. 본 레포지토리를 `clone`합니다.
### 2. `auth.json` 생성
GitHub API 사용에 Rating limit이 있기 때문에 설정 하는 것이 좋습니다.   
아래 양식을 바탕으로 `auth.json`을 `main.py`가 있는 위치에 생성합니다.   
```json
{
  "username": "xxxxxxx",
  "password": "xxxxxxx"
}
```

### 3. `repos.json`에 자신의 레포지토리를 기입합니다.
아래 "Path" 기입시, Onwer/Repository 또는 Organization/Repository 형태로 기입합니다.   
예) hermitkim1/github-influence-factors-counter 또는 cloud-barista/cb-spider   
```json
[
  {
    "Name": "cb-spier",
    "Path": "cloud-barista/cb-spider"
  },
  {
    "Name": "cb-tumblebug",
    "Path": "cloud-barista/cb-tumblebug-api-web"
  },
  {
    "Name": "xxx",
    "Path": "xxx"
  }
]
```

### 4. 실행후 잠시 기다리면 `Result.csv`가 생성됩니다.
`Result.csv`는 Repository, Stars, Forks, Watches, Commits(year)을 포함합니다.
