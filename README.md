# squawk-gitlab-ci-docker

## Usage

You can use the following job. It assumes:
- Your migrations are in the `migrations` folder
- Your postgresql version is 16
- You have a `main` branch
- You have defined the env var `COMMENT_GITLAB_TOKEN` in your GitLab project settings (With reporter role and API scope)

> You can adapt the job to your needs if you have a different setup.

```yaml
lint psql:
  image: alphayax/squawk-gitlab-ci-docker
  stage: test
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'   # Run on MR
  script:
    - FILES=$(git diff --name-only origin/main -- "migrations/*.sql")
    - |
      if [ -z "$FILES" ]; then
        echo "No migration files detected, skipping squawk."
        exit 0
      fi
    - git diff --name-status origin/main -- "migrations/*.sql"
    - git diff --name-only origin/main -- "migrations/*.sql" | xargs squawk --pg-version 16 --reporter json > db-report.json || true
    - python3 /json2glnote.py
```
