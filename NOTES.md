# Notes

What the checks found, what playing found, and what I asked the agent to change.

## What I asked for

1. Make `tests/test_casino.py` pass, without touching it.
2. Build a table in the browser to play a whole deal against the computer.

## What the checks found

### The computer was reading my hand

The first version of the computer player picked where to discard by asking
"what is the best capture my opponent could make after this?" — and it answered
that question by looking at the actual cards in my hand. It was cheating.

Changed to an estimate built only from what has already been shown: my own
hand, the table, and both piles. Every value from 1 to 13 is weighed by how
many cards of that value are still unaccounted for. That is the counting a
human player can also do.

Checked by swapping the opponent's hand for different cards in every position
of 150 deals: the computer's move never changes. Before the fix it changed in
20 positions.

### A second, narrower leak in the same place

Even after that fix, one branch still looked at the hand that moves next. That
is fine when the bare-table double move means the next hand is the computer's
own, but not when a new round has just been dealt off the talon — there it was
reading cards nobody had seen yet. Now only the double-move case looks ahead.

### The two copies of the rules agree

The browser cannot run `casino.py` without a build step, so `index.html` has
its own port of the rules. They are checked against each other: the same 120
deals, played with the same fixed choice of move, end with identical piles,
sweeps and scores on both sides.

### Not a bug: stale card elements

A script written to play the page automatically never managed to capture
anything. The cause was in the script, not the game — the table redraws its
cards after every click, so the script was clicking elements that had already
been replaced. A real player clicks whatever is on screen, so this never
affects actual play.

## What playing found

Not filled in yet — play a whole deal and add one line per thing that looks
wrong, then tell the agent.

- 
