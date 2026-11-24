# Run from this folder in PowerShell

```powershell
python .\test_app.py
docker build --progress=plain -t full .
docker run --rm full
docker build --progress=plain -f Dockerfile.slim -t slim .
docker run --rm slim
docker images full
docker images slim
```

Confirmed identity: sadra shadmehry, 40231062. Update app.py and test_app.py if needed, then rebuild both images.

Only sections 4.1 and 4.2 through page 6 are implemented. The full Dockerfile intentionally retains the assignment's original instruction order for the later section 4.3 cache experiment. `.dockerignore` keeps tests, secrets and unrelated files outside both images.

The GHCR push/pull steps on page 7 remain for later. No Git repository, commit, push, credentials, Compose, or CI configuration is created here.

