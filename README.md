# RHCP Randomizer

A tiny Python terminal companion for **Red Hot Chili Peppers**.

Every run picks a random track from the band's MusicBrainz recording catalog and displays an original one-line rock thought. The local metadata cache is created on first run, so normal launches are instant.

## Run

Requires Python 3.10+ and no third-party packages.

```bash
python rhcp.py
```

On the first launch, the app downloads track metadata from MusicBrainz and saves it to `rhcp_discography.json`.

## Commands

```bash
python rhcp.py             # random track + original line
python rhcp.py --update    # refresh local catalog
python rhcp.py --list      # list cached track titles
python rhcp.py --no-color  # plain terminal output
```

## Notes

- Uses MusicBrainz for recording metadata; no API key is required.
- MusicBrainz requests are rate-limited, so catalog refresh may take a little time.
- This project does not scrape, distribute, or store copyrighted song lyrics.
- The displayed one-liners are original text written for this utility.

Music metadata: [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API).
