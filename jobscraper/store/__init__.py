"""Persistence subsystem (local SQLite).

* ``SeenStore`` — dedup: remembers which postings were already seen so the bot
  only notifies on genuinely new listings.
* ``StartupStore`` — Scout phase: persists discovered startups and contacts.
"""
