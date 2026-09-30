# Shipment permission presentation

This synthetic client-only fixture has two states: `index.html?state=allowed` and `index.html?state=denied`. Neither URL is a security boundary; there is no server, authentication, persistence or real shipment. Do not claim server authorization from these UI checks.

Improve clarity and responsive presentation in both states. Read-only operators must be able to read the full permission explanation and inspect evidence. They cannot open or confirm a quarantine decision through pointer or Alt+Q. Authorized operators can open the dialog, cancel without a decision, or confirm the demonstration decision. Preserve dialog labels, focus return, status messages, test hooks and evidence. Only `index.html` and `styles.css` may change; `app.js` and this contract are protected.

Start in this directory with `python -B -m http.server 8000 --bind 127.0.0.1`, replacing an occupied port. Inspect both URLs at 1280 by 720 and 375 by 812. Do not install tools, contact services, alter staging or save a report. Stop the owned server afterward and preserve unrelated work.
