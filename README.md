# Cloud Computing — HW2

Student: sadra shadmehry — 40231062.

- [Part 1: Docker and secrets](part1/README.md)
- [Part 2: queue, Compose and concurrency](part2/README.md)
- [Persian report notes](REPORT_NOTES_FA.md)
- [Screenshots](screenshots/mine/)
- [CI workflow](.github/workflows/ci.yml)

## Section 5.3 — before and after

| Version | Commit | What it preserves |
|---|---|---|
| Before locking | `e0518aa` | Three replicas, no shared lock, documented 10 ms race-demonstration delay |
| After locking | `6120f97` | Shared lock for join/take, delay removed, concurrent-next checker |

The before-fix user run returned 200 successful joins and recovered all 200 names, but duplicated/skipped tickets (`passed: false`). These commit IDs identify the source versions; the screenshots record runtime evidence. Later CI/test additions do not change those historical commits.

## Section 6.1 — CI and publication

Pushes to branches and pull requests targeting main run lint, test and build. Only pushes to main publish the image, create the release tag and deploy the static page.

| Job | Runs on | Depends on | Why |
|---|---|---|---|
| lint | Branch pushes and PRs | Nothing | Catch Python/Dockerfile issues before publication |
| test | Branch pushes and PRs | Nothing | Catch defects on experimental branches; run in parallel with lint |
| build | Branch pushes and PRs | lint, test | Build only checked code, without pushing |
| push | Push to main | build | Load the exact build artifact and publish version + latest |
| tag | Push to main | build, push | Create an annotated tag only after registry publication succeeds |
| pages | Push to main | build, tag | Publish the same version after the image and Git tag exist |

Version format: `v<commit-date>-<full-commit-SHA>`. The same commit yields the same version on a rerun. Existing annotated tags must resolve to that commit and are never force-moved. A completed release rerun pulls its existing versioned image rather than overwriting it; latest is updated to that image. For a new release, push loads the image archive produced by build rather than rebuilding on a fresh runner.

The site source retains `__VERSION__`. The render tool writes only a temporary publication copy, retaining the sentence from that commit. Git tags, image version tags and displayed Pages versions match. Pages hosts the static HTML only; it does not run the queue API or Compose.

Tag pushes do not start CI because the push event explicitly selects branches only. Publication also requires a push to refs/heads/main, so it is skipped for PRs and other branches, even with a PAT. Job permissions are limited: contents read by default, packages write for push, contents write for tag, pages write plus id-token write for pages. No token is passed into Docker builds or stored in an image. Main CI runs are serialized; Pages deployments additionally share the github-pages concurrency group (to be shared by manual rollback in section 6.2).

### One-time GitHub setup (user)

1. Keep this repository public.
2. Settings → Pages → Build and deployment → Source: GitHub Actions.
3. If Actions is disabled, enable it in the repository's Actions settings. No PAT secret is required: the workflow uses GITHUB_TOKEN.
4. After the first main publication, make the lab-queue container package public in its package settings. This is a different package from Part 1's cc-hello. The image source label links it to this repository.

Expected URLs after successful publication:

- Repository: https://github.com/sadrashadmehry/CC_HW2_sadrashadmehry
- Pages: https://sadrashadmehry.github.io/CC_HW2_sadrashadmehry/
- Image: `ghcr.io/sadrashadmehry/lab-queue:<version>` and `:latest`

### First branch/PR capture — fig10

From the repository root, create a work branch and commit the new implementation yourself. Review the staged changes before committing.

```powershell
git switch -c ci-setup
git add .github README.md REPORT_NOTES_FA.md part2
git diff --cached --stat
git commit -m "Add queue CI and versioned publication"
git push -u origin ci-setup
```

On GitHub, open a pull request from ci-setup to main. Capture the Actions run with lint, test and build successful and push, tag and pages skipped. Keep the repository, branch/PR and job statuses visible. This workflow itself is the branch change for the first PR.

### Main publication — fig11

After the PR checks pass, merge the PR yourself on GitHub. The main push runs all six jobs. Capture the workflow graph, annotated Git tag and GHCR lab-queue package showing the version and latest tags. Also capture the public page with the same version. Do not merge if the checks fail; send the failing job log to Codex for repair.

Sync locally after merging:

```powershell
git switch main
git pull --ff-only
git fetch --tags
```

Workflow execution, GHCR publication and Pages deployment are not verified until the user pushes and supplies the Actions results. Section 6.2 (manual rollback workflow) is next; it is not implemented yet.
