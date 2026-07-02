#!/usr/bin/env python
"""
Python script to scrape Mission Planning websites for specific observation data not located in the ocat
"""
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup

OBS_SS = Path("/data/mta4/obs_ss")
LONG_TERM_SCHEDULE_FILE = Path("/proj/web-icxc/htdocs/mp/lts/lts-current.html")
OBSID_RE = re.compile(r"target_param\.cgi\?(\d+)")


def parse_schedule_file(html_file):
    """
    The HTML files does not contain an actual table to display the schedule information, opting instead to use the <pre> tag.
    Thus we parse by enclosing link tags.
    """
    results = []
    with open(html_file, encoding='latin-1') as f:
        for line in f:
            #: Format changes at LTS change table. Stop before reaching this section.
            mc = re.search('LTS changes', line)
            if mc is not None:
                break

            m = OBSID_RE.search(line)
            if not m:
                continue

            obsid = int(m.group(1))

            soup = BeautifulSoup(line, "html.parser")
            text = soup.get_text(" ", strip=True)

            tokens = text.split()

            det_idx = next(
                i for i, tok in enumerate(tokens)
                if tok.startswith(("ACIS", "HRC"))
            )

            roll = tokens[det_idx - 2]
            roll_range = tokens[det_idx - 1]

            results.append(
                f"{obsid}:{roll}:{roll_range}"
            )
    return results

import sys

def find_planned_roll(html_file, outfile):
    results = parse_schedule_file(html_file)

    if hasattr(outfile, "write"):
        outfile.write("\n".join(results))
        outfile.write("\n")
    else:
        with open(outfile, "w") as out:
            out.write("\n".join(results))
            out.write("\n")
    
if __name__ == "__main__":
    find_planned_roll(LONG_TERM_SCHEDULE_FILE, sys.stdout)