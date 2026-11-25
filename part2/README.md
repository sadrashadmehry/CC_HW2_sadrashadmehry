# Part 2 — lab queue

Runtime: Python 3.12, standard library only. The supplied tests are unchanged.
Local verification used Python 3.13 on Windows: 24 passed (13 supplied + 11 extra).
Docker runtime verification remains pending user capture.

## Tests

The assignment's development commands from this directory are:

```powershell
python -m pip install -r requirements-dev.txt
pytest
```

A local .venv is already prepared. To avoid this machine's shared-temp permissions issue, use:

```powershell
whoami
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.venv/pytest-capture
```

For the required before-implementation failure capture, run the untouched starter (not the implemented repo copy):

```powershell
cd C:\Sadra\AK\S07\cloud\assignments\hw02\codes\part2
whoami
& ..\..\repo\part2\.venv\Scripts\python.exe -m pytest -q --tb=line --basetemp=..\..\repo\part2\.venv\pytest-starter-capture
```

Expected original starter: 12 failed, 1 passed. Expected repo implementation: 24 passed.
Save native screenshots as tests-before.png and tests-after.png under repo/screenshots/mine.
Raw agent runs are saved outside the repo in hw02/evidence/part2-before.txt and part2-after.txt.

## Docker

```powershell
cd C:\Sadra\AK\S07\cloud\assignments\hw02\repo\part2
whoami
docker build --progress=plain -t lab-queue:local .
docker run -d --name cc-queue-51 -p 127.0.0.1:8000:8000 lab-queue:local
curl.exe -i http://localhost:8000/health
docker ps --filter name=cc-queue-51
```

Expected health: HTTP 200, body exactly ok, Content-Length 2. This is a standalone container, not Compose. Its data is intentionally not persistent after removal; persistence is section 5.2.

## API

- GET /health -> 200, plain text ok.
- POST /join with JSON {"name":"Ali"} -> 200, queue length after append; invalid JSON/name -> 400 without changing the queue.
- POST /next -> 200, first name; missing/empty queue -> 404, plain text empty.
- Names: trimmed, 1–40 characters, no line breaks. Duplicate names are allowed.
- UTF-8 plain text responses include byte-accurate Content-Length.
- PORT defaults 8000; DATA_DIR defaults /data. main binds 0.0.0.0; serve honors its host argument.
- Local queue file paths are supplied by the caller. Removal writes a same-directory temporary file and replaces the queue only when writing succeeds.
- shortcut: no shared process lock yet; add the shared lock and record the three-replica race before/after in section 5.3. Do not use this version for multiple replicas.

For manual testing, import postman/lab-queue.postman_collection.json into Postman; baseUrl defaults to http://localhost:8000. The static site in site/index.html is separate from the API and keeps __VERSION__ in Git.

When finished with the section 5.1 container:

```powershell
docker stop cc-queue-51
docker rm cc-queue-51
```

Section 5.2 is complete per user confirmation. Current configuration is the unlocked section 5.3 baseline below: three app replicas behind proxy. Earlier section 5.2 commands document the earlier single-instance stage. Locking and CI/Pages are not implemented yet.


## Section 5.2 — Compose and persistence

compose.yaml builds app from the local Dockerfile. PORT=8000 and DATA_DIR=/data are passed via environment. The host port is read from APP_PORT in the ignored .env; .env.example supplies the safe example. Publish only on localhost. The named queue-data volume mounts at /data. Compose config validation passed; runtime screenshots remain pending.

### Start (from repo/part2)

```powershell
whoami
docker compose up --build -d
docker compose ps
```

If port 8000 is still occupied by the section 5.1 container, stop it with docker stop cc-queue-51 first. Do not stop unrelated containers. If a different APP_PORT is needed, ask Codex to update .env and update only Postman's baseUrl to match. A fresh named volume starts empty; restarting Compose does not reset an existing queue.

### Postman — fig7

Import postman/lab-queue.postman_collection.json. Collection variable baseUrl is http://localhost:8000 (match .env if changed). From an empty queue:

1. health -> 200, ok.
2. join body {"name":"Ali"} -> 200, 1.
3. join body {"name":"Sara"} -> 200, 2.
4. join body {"name":"Reza"} -> 200, 3.
5. next -> 200, Ali. Leave Sara and Reza queued for the persistence test.

Capture health, join and next as fig7-a-health.png, fig7-b-join.png, fig7-c-next.png, with Postman account identity visible when available. Requests are sequential; do not run the collection repeatedly between the before/after persistence captures.

### Volume and running service — fig8

```powershell
whoami
docker ps -a
docker inspect $(docker compose ps -q app) --format '{{range .Mounts}}{{println .Type .Name .Destination}}{{end}}'
docker volume inspect part2_queue-data --format '{{.Name}} driver={{.Driver}}'
docker stats --no-stream $(docker compose ps -q app)
```

The default project name is part2, so the actual named volume is part2_queue-data. If COMPOSE_PROJECT_NAME is set externally, use the volume name shown by the mount inspection instead. Capture mounts, container listing and stats; split as fig8-a / fig8-b if necessary.

### Preserve queue while replacing app — fig9

```powershell
whoami
docker compose ps -q app
docker compose exec app python -c "from pathlib import Path; print(Path('/data/queue.txt').read_text(encoding='utf-8'))"
```

Capture fig9-a-before-recreate.png: the container ID and remaining Sara/Reza lines. Then:

```powershell
docker compose rm -s -f app
docker compose up -d app
docker compose ps -q app
docker compose exec app python -c "from pathlib import Path; print(Path('/data/queue.txt').read_text(encoding='utf-8'))"
```

Capture fig9-b-after-recreate.png: new container ID, identical remaining queue. Do not remove the named volume. In particular, do not use docker compose down -v.

### Rebuild after a code change

After the persistence screenshots, ask Codex to make the comment-only app change for section 5.2 step 4. Then run:

```powershell
whoami
docker compose up --build -d
docker compose ps
curl.exe -i http://localhost:8000/health
```

Save a supplementary rebuild screenshot, and check /data/queue.txt still contains the remaining names. Codex will make the code edit between captures; no manual code editing is needed.

Save captures in ../screenshots/mine. Keep .env out of Git. To stop the service while keeping its data, use docker compose down (without -v).


## Section 5.3 — unlocked baseline (capture before the lock fix)

The app service no longer publishes a host port or has a fixed container_name. Only Nginx publishes APP_PORT. All replicas share queue-data at /data. nginx.conf is mounted read-only. Nginx resolves app through Compose DNS at startup; a name resolving to three IPs becomes three upstream peers. Start app replicas first, then start/reload proxy after they exist. Reload after replacing/scaling app replicas. proxy_next_upstream off prevents replaying a mutating request against another upstream on a proxy error. Access logs include upstream addresses.

This stage intentionally has no shared lock. A documented 10 ms pause after append and before counting widens the race window. The supplied functional tests still pass; concurrent ticket numbers may duplicate. Remove that pause when adding the lock. take already uses atomic replacement to avoid data loss on write failure, but atomic replacement alone does not protect a read-modify-write operation across replicas.

### Save a baseline commit (user performs Git operations)

From repo/part2:

```powershell
git add .
git diff --cached --stat
git commit -m "Record unlocked three-replica queue baseline"
git rev-parse --short HEAD
```

Review staged changes before committing; do not commit archives or .env. Record the commit SHA for the report. No push is needed to run the experiment. Codex does not create commits or push.

### Start a separate test queue

The experiment consumes its queue. Project cc-hw2-race gives it a separate named volume cc-hw2-race_queue-data, preserving part2_queue-data from section 5.2. Never run concurrent_join against the original queue. A previously used cc-hw2-race project may have existing data; inspect it first.

```powershell
whoami
docker compose -p part2 down
docker compose -p cc-hw2-race up -d --build --scale app=3 app
docker compose -p cc-hw2-race up -d --scale app=3 proxy
docker compose -p cc-hw2-race exec proxy nginx -t
docker compose -p cc-hw2-race exec proxy nginx -s reload
docker compose -p cc-hw2-race ps
curl.exe -i http://localhost:8000/health
docker compose -p cc-hw2-race exec --index 1 app python -c "from pathlib import Path; p=Path('/data/queue.txt'); print(repr(p.read_text(encoding='utf-8')) if p.exists() else 'empty: no queue file yet')"
```

Do not use down -v. The old single-instance project must release APP_PORT before the race project starts. nginx -t must succeed; /health must return 200. The queue must be empty before the batch. These commands assume the prepared .env APP_PORT=8000.

### Run the supplied 200-request batch

```powershell
whoami
python tools/concurrent_join.py --url http://localhost:8000 --drain
```

Capture fig14-a-unlocked.png: successful count, duplicate/missing tickets, drained names and passed. A false result caused by duplicate tickets demonstrates the queue race. Connection/timeout errors alone do not establish a race; inspect health/proxy configuration first. If passed is true, inspect that the queue is empty and run again. Do not retry individual timed-out join/next calls; reset the separate test queue before repeating a faulty batch.

### Prove three backends received traffic

```powershell
whoami
docker inspect $(docker compose -p cc-hw2-race ps -q app) --format '{{.Name}} {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
docker compose -p cc-hw2-race logs --tail 35 proxy
```

Capture fig14-b-three-backends.png with three replica IPs and matching upstream addresses in actual access logs. Merely listing three containers does not prove load balancing. Use more log lines if needed.

Stop here and send the baseline output and commit SHA. Codex will then add shared file locking, remove the deliberate pause, add concurrent next checks, and repeat the same test on an empty queue. Do not present this unlocked stage as the completed 5.3 solution.
