# GitHub meaningful achievements counter

공개SW R&D의 유의미한 성과들은 각 저장소(Repository)에 기록이 남습니다. 
그래서 조직(Organization)차원에서 성과를 파악하는 것은 상당히 소모적인 작업이라 할 수 있습니다.
조직 내의 여러 저장소들의 유의미한 성과들을 효율적으로 파악하고자 도구를 만들게 되었습니다.
GitHub API를 호출하여 유의미한 성과들을 파악하여 GitHub UI 상에 나타나는 수치와 일치합니다. 

참고 - [GitHub REST API documentation](https://docs.github.com/en/rest?apiVersion=2022-11-28) 

본 도구를 활용하면 조직 정보, 저장소 정보, 및 아래와 같은 성과를 파악할 수 있습니다. :thumbsup:  

![image](https://github.com/yunkon-kim/github-influence-factors-counter/assets/7975459/217b4a6e-a4ce-457a-a9b4-05c6509ad48c)

Open Source Software (OSS) 관련 프로젝트에서 편리하게 활용되기를 바랍니다. :smile:   

**앞에서 유의미한 성과로 표현했지만, 공개SW 생태계에서 일어나는 모든 기여는 너무나도 중요하고 소중합니다.**   
**만약 본 프로그램이 평가에 활용된다면, <ins>필히! 정성적인 가치 평가가 함께 이루어져야할 것 입니다.</ins>** :pray:


## Environment

다음과 같은 환경에서 개발 및 테스트를 진행하였습니다.

- Ubuntu 22.04.3 LTS (on WSL2)
- Python 3.10.12
- pip 22.0.2 

## 사용방법

### 소스코드 내려 받기

`git clone`을 통해 소스 코드를 내려 받습니다.

```bash
git clone https://github.com/yunkon-kim/github-influence-factors-counter.git
```

### 실행 환경 구성

참고 - 최초 한번만 수행하면 되는 사항입니다. 

#### Python 및 관련 패키지 설치

아래 명령어를 통해 Python 및 관련 패키지를 설치하실 수 있습니다.

```bash
sudo apt update -y
sudo apt install python3
sudo apt install python3-pip
apt install python3.10-venv -y
```

#### `venv` 환경 설정

아래 명령어를 통해 `venv`를 설정 합니다. 
(`./venv` 디렉토리가 생성되고 `venv` 관련 사항들이 설치될 것 입니다.)

```bash
python3 -m venv ./venv
```

아래 명령어를 통해 `venv`를 활성화합니다.

```bash
source .venv/bin/activate
```

#### Python 모듈 설치

아래 명령어를 통해 도구를 실행하는데 필요한 모듈을 설치 합니다.

```bash
pip3 install -r requirements.txt
```


### 설정 파일 작성

GitHub REST API에는 Rating limit이 적용되어 있고, Personal Access Token (PAT) 활용을 통해 시간단 5000회 까지 호출하도록 만들 수 있습니다. 

참고 - [Creating a personal access token (classic)](https://docs.github.com/ko/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic))

`template-auth.json`을 복사하여 `auth.json` 생성한 후 알맞게 수정하시기 바랍니다.
```json
{
  "username": "your-github-username",
  "personal-access-token": "your-github-personal-access-token"
}

```

`template-config.json`을 복사하여 `config.json` 생성한 후 알맞게 수정하시기 바랍니다.

```json
{
  "org-name": "your-organization-name",
  "since": "2023-01-01",
  "until": "2023-12-31",
  "repositories": [
    "repo1",
    "repo2",
    "repo3"
  ]
}
```

(optional) 조직내의 모든 저장소 리스트를 확인하는 스크립트를 만들어 두었습니다.
`repositories`를 채우실때 도움이 될 것 같습니다.

```bash
python3 get_org_repos.py
```

### 실행 및 결과 확인

위 준비 사항을 끝마치셨으면 이제 도구를 실행해 주기만 하면 됩니다.

아래 명령어를 통해 조직내의 지정된 저장소의 유의미한 성과를 추출할 수 있습니다.

```bash
python3 orgs.py
```

성과를 추출하는데 시간이 조금 소요되며, 결과가 `.results/` 경로에 `csv` 형식으로 출력됩니다.
(파일명 예: `(cloud-barista)repos-statistics-rawdata-20231208-223421.csv`)

파일을 열어 결과를 확인합니다.

![image](https://github.com/yunkon-kim/github-influence-factors-counter/assets/7975459/217b4a6e-a4ce-457a-a9b4-05c6509ad48c)
