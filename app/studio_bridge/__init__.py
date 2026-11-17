"""Studio write bridge: local, authenticated, localhost-only.

The read-only production API (api/main.py) stays untouched.  This module adds
the minimal set of mutations the dashboard needs to drive the engine:

* start a strong-pipeline production run for a topic
* approve a parked review storyboard (the gate stays fully enforced)
* resume a parked run after approval

It is bound to 127.0.0.1 and requires the same Bearer key the dashboard
already uses for the read API (SHORTS_STUDIO_API_KEY from the environment or
~/.config/nextdecode/api.env).  It never handles publishing and it never
bypasses the evidence, rights, storyboard or QA gates.
"""
