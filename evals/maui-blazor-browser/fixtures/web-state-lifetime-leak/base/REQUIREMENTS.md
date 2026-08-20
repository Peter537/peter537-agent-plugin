# State ownership

Each interactive Web circuit represents a different signed-in user. Draft state must never cross circuits. The native host may use one state instance because it has one local user, but that lifetime is not evidence for the Web host.
