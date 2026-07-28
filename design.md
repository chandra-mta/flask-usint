# Design

This document contains minor clarifying information for the design intentions of the Usint application.
Intentions can range from minor features of communicating revision information clearly, to
large-scale needs of the applications functionality.

## Minor Features

### Warnings v.s flashed messages

**Impact: Low**

Several different confirmations pages, such as the ocatdatapage/index.html template. include both a section
for warning lines, and a section to display flashed messages.

Warning lines are for informing the user of important information about the observation in terms of our multi-team scheduling workflow.
Such as whether the observation is on the OR list or has already been observed.

Flashed messages are for cautioning the user about an action they are performing on the app for a revision.
Such as an obsid not being found in the OCAT database (typo in obsid).

These are categories for information display. Breaking this design principle will not harm functionality.