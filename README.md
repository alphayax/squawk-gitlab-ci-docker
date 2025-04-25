# squawk-gitlab-ci-docker

A basic docker image to be run in Gitlab CI to lint your SQL 
migrations with [Squawk](https://github.com/sbdchd/squawk).

It will convert results to a GitLab note format so you can see the results in your merge request.

## Image contents
This image is based on debian:bullseye and contains:
- Squawk
- Git
- Python 3 (with requests)

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

## Results example

>## `migrations/20250424075437.sql`
>### line 3: 🔶 **Warning** – _prefer-big-int_
>- 💬 **Note**: Hitting the max 32 bit integer is possible and may break your application.
>- 💡 **Help**: Use 64bit integer values instead to prevent hitting this limit.
>### line 3: 🔶 **Warning** – _prefer-bigint-over-int_
>- 💬 **Note**: Hitting the max 32 bit integer is possible and may break your application.
>- 💡 **Help**: Use 64bit integer values instead to prevent hitting this limit.
>### line 3: 🔶 **Warning** – _prefer-identity_
>- 💬 **Note**: Serial types have confusing behaviors that make schema management difficult.
>- 💡 **Help**: Use identity columns instead for more features and better usability.
>## `migrations/20250424075936.sql`
>### line 1: 🔶 **Warning** – _prefer-robust-stmts_
>- 💡 **Help**: Consider wrapping in a transaction or adding a IF NOT EXISTS clause if the statement supports it.
>### line 3: 🔶 **Warning** – _prefer-text-field_
>- 💬 **Note**: Changing the size of a varchar field requires an ACCESS EXCLUSIVE lock.
>- 💡 **Help**: Use a text field with a check constraint.
>### line 3: 🔶 **Warning** – _prefer-robust-stmts_
> ...