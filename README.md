# Cassino

The **Hungarian two-player version** of Cassino, with a 52-card French deck —
in the browser, you against the computer.

## Play

```sh
start index.html
```

On macOS use `open index.html`, on Linux `xdg-open index.html`. There is no
server and no build step: the command just hands the file to your browser.

Click cards in your hand and on the table, then **Take** — what you play and
what you take must add up to the same total. **Place** puts a single card down
instead. The running totals next to the buttons turn gold when they match.

## Run the tests

```sh
uv run pytest
```

Without `uv`: `python -m pip install pytest`, then `python -m pytest`.

## The rules, as implemented

Every card has a numeric value: A is 1, the pips are themselves, J is 11,
Q is 12, K is 13.

- A move plays one or more cards from hand. It either takes cards from the
  table, in which case the two sides must add up to the same total, or it takes
  nothing and the single card played stays face up.
- **Sweep.** Taking the last card off the table is worth a point.
- **The double move.** A player who moves with nothing on the table moves
  again, because the card they put down cannot be taken by them.
- A round is three cards each. When both hands run out, whoever took cards most
  recently draws first and leads the next round.
- When the talon runs out too, that same player takes whatever is still lying
  on the table. Nobody scores a sweep for it.

Scoring, per deal: 3 for most cards, 2 for most spades, 1 per ace, 2 for the
10 of diamonds, 1 for the 2 of spades, plus a point per sweep. A tie on cards
scores nothing for either player, so a deal is worth 12 points plus sweeps, or
9 plus sweeps when the cards split 26–26.

## What is here

| File | What it is |
|---|---|
| `casino.py` | The rules, as the interface the tests use. |
| `index.html` | The table: markup, styles, a JS port of the same rules, and the computer player. |
| `tests/` | The test suite the module has to pass. |

The browser cannot run `casino.py` without a build step, so `index.html`
carries its own copy of the rules. The two are kept honest against each other:
the same 120 deals, played by the same fixed choice of move, end with the same
piles, sweeps and scores in both.

Cards are drawn in CSS rather than fetched, so the page works with no network.
The corner shows the rank and suit, and the small grey number in the corner
opposite is the card's value, which is what you actually add up.

### The computer

It takes the most valuable capture on offer, counting the 10 of diamonds, the
2 of spades, aces, spades and sweeps. With nothing to take, it places the card
that leaves the least on offer, weighing each value by how many cards of that
value it has not yet seen.

It plays from its own hand only. A test swaps the opponent's hand for other
cards in every position of 150 deals and checks that its move never changes.
