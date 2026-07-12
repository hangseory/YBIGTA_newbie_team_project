# YBIGTA Newbie Team Project 협업 방법

저장소:

```text
https://github.com/hanseory/YBIGTA_newbie_team_project
```

## 1. 처음 한 번만

```bash
git clone https://github.com/hanseory/YBIGTA_newbie_team_project.git
cd YBIGTA_newbie_team_project
```

## 2. 작업 시작할 때

항상 최신 `main`을 받은 뒤 자기 브랜치를 만든다.

```bash
git switch main
git pull origin main
git switch -c honggildong-data-cleaning
```

브랜치 이름은 알아보기 쉽게 정하면 된다.

```text
honggildong-data-cleaning
honggildong-model
honggildong-readme
```

현재 브랜치 확인:

```bash
git branch
```

`*`가 붙은 브랜치가 현재 브랜치다.

## 3. 작업 후 커밋

```bash
git status
git add .
git commit -m "데이터 정리 코드 추가"
```

## 4. push 전에 최신 main 반영

다른 팀원의 코드가 먼저 합쳐졌을 수 있으므로 바로 push하지 않는다.

```bash
git fetch origin
git merge origin/main
```

충돌이 없다면 자기 브랜치를 GitHub에 올린다.

```bash
git push -u origin honggildong-data-cleaning
```

두 번째 push부터는:

```bash
git push
```

## 5. GitHub에서 합치기

`main`에 직접 push하지 말고 Pull Request를 만든다.

```text
GitHub 저장소
→ Pull requests
→ New pull request
→ base: main
→ compare: honggildong-data-cleaning
→ Create pull request
```

Pull Request에서 팀원들과 의견을 조율하고, 수정이 필요하면 같은 브랜치에서 다시:

```bash
git add .
git commit -m "리뷰 의견 반영"
git push
```

검토가 끝나면 GitHub에서 `Merge pull request`를 누른다.

## 6. merge가 끝난 후

```bash
git switch main
git pull origin main
git branch -d honggildong-data-cleaning
```

## 전체 순서

```bash
git switch main
git pull origin main
git switch -c honggildong-data-cleaning

# 파일 작업

git add .
git commit -m "데이터 정리 코드 추가"

git fetch origin
git merge origin/main
git push -u origin honggildong-data-cleaning
```

그다음 GitHub에서:

```text
Pull Request 생성
→ 팀원들과 검토
→ Merge
```
