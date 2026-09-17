"""
Compatibility shim for the deployed Render start command.

The app moved to `web/` in commit 3dbdf64 ("Reorganize project into functional
folders"), but the Render service's Start Command still names the old path:

    uvicorn Phase5.webapp.server:app --host 0.0.0.0 --port $PORT

That command has crash-looped on every deploy since, so Render kept serving the
last healthy build and the site stayed frozen on pre-3dbdf64 code. This package
makes the old import path resolve to the real app again, so deploys succeed
without dashboard access.

This is a redirect, not a second copy of the app - see Phase5/webapp/server.py.
Once the Start Command is updated to `uvicorn web.server:app`, delete this
whole Phase5/ directory; nothing else imports it.
"""
