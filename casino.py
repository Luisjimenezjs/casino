"""Cassino, the Hungarian two-player version, with a 52-card French deck.

Every card is a string of rank then suit, and every card has a numeric value:
A is 1, the pips are themselves, J is 11, Q is 12, K is 13.

A move plays one or more cards from the hand. It either takes cards from the
table, in which case the two sides must add up to the same total, or it takes
nothing and the single card played stays on the table.

Two rules shape the turn order:

* Sweep. Taking the last card off the table is worth a point, and it leaves
  the next player facing bare felt.
* The double move. A player who moves with nothing on the table moves again,
  because the card they put down cannot be taken by them.

A round is three cards each. When both hands run out, whoever took cards most
recently draws first and leads the next round; when the talon runs out too,
that same player takes whatever is still lying on the table.
"""

from typing import NamedTuple, Optional

RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
SUITS = "SHDC"
DECK = tuple(rank + suit for suit in SUITS for rank in RANKS)

HAND = 3          # cards dealt to each player per round
TABLE = 4         # cards dealt face up at the start of a deal

MOST_CARDS = 27   # a majority of the 52 cards, worth 3
MOST_SPADES = 7   # a majority of the 13 spades, worth 2


def value(card):
    """The card's value: A is 1, J is 11, Q is 12, K is 13."""
    return RANKS.index(card[:-1]) + 1


class Move(NamedTuple):
    """What a player plays, and what it takes.

    Placing a card without taking anything is Move(frozenset({"7H"}), frozenset()).
    """

    hand: frozenset
    table: frozenset


class State(NamedTuple):
    """A position in a deal. Every field is immutable; play returns a new one."""

    hands: tuple                            # a pair of tuples, one per player
    table: tuple                            # the cards face up
    talon: tuple                            # the stock, next card first
    piles: tuple                            # a pair of tuples, the cards taken
    sweeps: tuple                           # a pair, points earned from sweeps
    player: int                             # whose turn it is, 0 or 1
    last_capturer: Optional[int] = None     # who took cards most recently


# --- the deal ---------------------------------------------------------------

def new_deal(deck, first=0):
    """Deal from deck: three cards to first, three to the other player, four up."""
    deck = tuple(deck)
    hands = [None, None]
    hands[first] = deck[:HAND]
    hands[1 - first] = deck[HAND:2 * HAND]
    return State(
        hands=tuple(hands),
        table=deck[2 * HAND:2 * HAND + TABLE],
        talon=deck[2 * HAND + TABLE:],
        piles=((), ()),
        sweeps=(0, 0),
        player=first,
    )


# --- legal moves ------------------------------------------------------------

def legal_moves(state):
    """Every legal Move for the player to move."""
    hand = state.hands[state.player]
    moves = [Move(frozenset({card}), frozenset()) for card in hand]

    for played in _subsets(hand):
        total = sum(value(card) for card in played)
        for taken in _adding_up_to(state.table, total):
            moves.append(Move(frozenset(played), frozenset(taken)))

    return moves


def _subsets(cards):
    """Every non-empty subset of cards, as tuples."""
    out = []
    for mask in range(1, 1 << len(cards)):
        out.append(tuple(c for i, c in enumerate(cards) if mask >> i & 1))
    return out


def _adding_up_to(cards, total):
    """Every non-empty subset of cards whose values add up to total."""
    values = [value(card) for card in cards]

    # rest[i] is everything from i on, so a branch that cannot reach the total
    # is abandoned instead of walked to the end.
    rest = [0] * (len(values) + 1)
    for i in reversed(range(len(values))):
        rest[i] = rest[i + 1] + values[i]

    out, chosen = [], []

    def walk(i, left):
        if left == 0:
            if chosen:
                out.append(tuple(chosen))
            return
        if i == len(values) or left < 0 or left > rest[i]:
            return
        chosen.append(cards[i])
        walk(i + 1, left - values[i])
        chosen.pop()
        walk(i + 1, left)

    walk(0, total)
    return out


# --- playing ----------------------------------------------------------------

def play(state, move):
    """The state after the move, including whatever the rules do next.

    Raises ValueError if the move is not legal.
    """
    player = state.player
    _check(state, move)

    hands = list(state.hands)
    piles = list(state.piles)
    sweeps = list(state.sweeps)
    talon = state.talon
    last = state.last_capturer

    # Keep the dealt order rather than the order of the frozensets, so that a
    # state built from the same deck is always the same state.
    played = tuple(c for c in state.hands[player] if c in move.hand)
    hands[player] = tuple(c for c in state.hands[player] if c not in move.hand)

    if move.table:
        taken = tuple(c for c in state.table if c in move.table)
        table = tuple(c for c in state.table if c not in move.table)
        piles[player] = piles[player] + played + taken
        last = player
        if not table:
            sweeps[player] += 1
    else:
        table = state.table + played

    # A player who moved with nothing on the table moves again.
    bare = not state.table

    if hands[0] or hands[1]:
        nxt = player if bare and hands[player] else 1 - player
        if not hands[nxt]:
            nxt = 1 - nxt
    elif talon:
        # A new round: whoever took cards last draws first and leads.
        leader = last if last is not None else 1 - player
        hands[leader] = talon[:HAND]
        hands[1 - leader] = talon[HAND:2 * HAND]
        talon = talon[2 * HAND:]
        nxt = leader
    else:
        # The deal is over: what is still on the table goes to whoever took last.
        winner = last if last is not None else player
        piles[winner] = piles[winner] + table
        table = ()
        nxt = 1 - player

    return State(
        hands=tuple(hands),
        table=table,
        talon=talon,
        piles=tuple(piles),
        sweeps=tuple(sweeps),
        player=nxt,
        last_capturer=last,
    )


def _check(state, move):
    """Raise ValueError unless the move is one the player to move may make."""
    hand = set(state.hands[state.player])

    if not move.hand:
        raise ValueError("a move must play at least one card")
    if not move.hand <= hand:
        raise ValueError(f"not in hand: {sorted(move.hand - hand)}")
    if not move.table <= set(state.table):
        raise ValueError(f"not on the table: {sorted(move.table - set(state.table))}")

    if move.table:
        played = sum(value(c) for c in move.hand)
        taken = sum(value(c) for c in move.table)
        if played != taken:
            raise ValueError(f"{played} played does not take {taken}")
    elif len(move.hand) > 1:
        raise ValueError("only one card at a time can be placed on the table")


# --- the end of the deal ----------------------------------------------------

def deal_over(state):
    """True once every card has been taken."""
    return not (state.hands[0] or state.hands[1] or state.table or state.talon)


def score(state):
    """The points each player earned in the finished deal."""
    return tuple(_points(state, player) for player in (0, 1))


def _points(state, player):
    pile = state.piles[player]
    points = state.sweeps[player]
    if len(pile) >= MOST_CARDS:
        points += 3
    if sum(card.endswith("S") for card in pile) >= MOST_SPADES:
        points += 2
    points += sum(card.startswith("A") for card in pile)
    if "10D" in pile:
        points += 2
    if "2S" in pile:
        points += 1
    return points
