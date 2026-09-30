# Danish evidence review

The supplied synthetic workflow supports evidence review and an approval or rejection decision. Compare `index.html?content=short` with `index.html?content=long` (the original long content is also the default). These are two supplied sample titles, not permission to abbreviate the long title. Preserve all Danish copy, counts, meaning, test hooks and behavior; do not invent capabilities or records.

Only `index.html` and `styles.css` may change. Keep `app.js`, this contract, and unrelated work unchanged. Approval clears the rejection error. Rejection without a reason shows the existing error; providing a reason clears it. Alt+A and Alt+R retain their existing behavior. Keep the source link and a visible label for the reason field.

Start from this directory using `python -B -m http.server 8000 --bind 127.0.0.1`, replacing an occupied port. Inspect both content URLs at 1280 by 720 and 375 by 812 before and after changes, including keyboard focus and rejection paths. No dependencies, services or external resources are required. Stop the owned server afterward; do not alter staging or create a report file.
