# Screenshot index

- fig1-inspection.png: saved Docker image list, history, layer hashes and exposed port.
- fig2-a-sonic-browser-8080.png: actual browser rendering of Sonic on port 8080 after animation completes (fresh image shows its installation page).
- fig2-logs.png: saved startup logs.
- fig3-a-sonic-browser-8081.png: actual browser rendering of the second instance on port 8081.
- fig3-running.png: both running containers and HTTP 200 responses while both were up.
- fig3-cleanup.png: stopping/removing the two exercise containers, listing remaining containers, and retaining the Sonic image.

Command-output images are explicitly labeled browser renderings of real saved logs, not native terminal-window screenshots. Raw logs are in ../evidence/. For strict submission requirements, capture the corresponding commands in your terminal too. No success screenshots are supplied for commands that failed.

Build evidence: fig4-full-build.png and fig4-full-run.png show the successful full build and four-line output. fig5-slim-build.png and fig5-slim-run.png show the slim build and output; fig5-size-comparison.png shows the measured reduction. GHCR push/pull is deferred.
