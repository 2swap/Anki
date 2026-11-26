"""The Go deck's notes, transcribed from Sensei's Library diagrams.

to_move: who moves first in the position. player: the side the person plays on
the "play out" card (always the side whose result the lines show correctly).
Lines only contain moves that the source endorses for `player`; the other side's
moves may include the mistakes the source discusses.
"""
from sensei import *

S = seq
X, O = 'X', 'O'


def mv(c, s):
    return [('X' if c == 'B' else 'O', pt(s))]


# ============================ L group ============================
LG = 'L-group'
note(title='L group', base=(LG, 1), to_move=X, player=O,
     status='Dead, even if Black plays first.',
     prompt='Black tries to live. Kill as White.',
     notes='"The L group is dead." Every black attempt fails: White answers each 1-2 point or descent with the vital point or a hane, '
           'leaving Black a bulky five or a single eye.',
     lines=[Line(S(LG, k), end='Dead.') for k in (4, 5, 2, 3, 6, 7, 8)] +
           [Line(S(LG, 4, at={5: 'W6', 6: 'B5'}), end='Dead.')])

# ============================ L+1 groups ============================
L1 = 'L+1 group'
note(title='L+1 group (leg on the short side), Black to play', base=(L1, 1), to_move=X, player=X,
     status='Unsettled: Black to play lives.',
     prompt='Black to play and live.',
     notes='The 1-2 point lives. Other defences can end in ko or seki.',
     lines=[Line(S(L1, 2), end='Alive.')])
note(title='L+1 group (leg on the short side), White to play', base=(L1, 1), to_move=O, player=O,
     status='Unsettled: White to play kills.',
     prompt='White to play and kill.',
     notes='The hane reduces Black to the L group, which is dead. The 2-2 attachment also kills (after it, '
           'the two eye-stealing points are miai), but attacking from the outside first is usually better.',
     lines=[Line(S(L1, 6), end='Dead: an L group.'), Line(S(L1, 7), end='Dead: the two remaining points are miai.')])
note(title='L+1 group (short-side leg) with a hane on top', base=(L1, 9), to_move=O, player=O,
     status='Dead if White plays first: hane, then the 2-2 placement.',
     prompt='White to play and kill.',
     notes='The throw-in that kills the plain L+1 group fails here: Black jumps to the 2-1 point and lives. '
           'Instead White hanes on the left, places at 2-2, and finishes with a throw-in. '
           'The White stone at the 2-7 point matters.',
     lines=[Line(S(L1, 11), end='Dead.')])
note(title='L+1 group (leg on the long side), Black to play', base=(L1, 19), to_move=X, player=X,
     status='Unsettled: Black to play lives.',
     prompt='Black to play and live.',
     notes='The 2-2 point is the vital point. The 1-2 point also lives but gives up endgame value, '
           'and the 1-3 point lives smaller still (4 points instead of 6).',
     lines=[Line(S(L1, 20), end='Alive.'),
            Line(mv('B', 'ab'), end='Alive, but White may later threaten it.'),
            Line(S(L1, 22), end='Alive, but White\'s hane on top is sente.')])
note(title='L+1 group (leg on the long side), White to play', base=(L1, 19), to_move=O, player=O,
     status='Unsettled: White to play kills.',
     prompt='White to play and kill.',
     notes='The hane on the left side kills by reducing Black to an L group, which is dead.',
     lines=[Line(S(L1, 23), end='Dead: Black is reduced to an L group.')])
note(title='L+1 group (long-side leg) with a hane on the left', base=(L1, 24), to_move=O, player=O,
     status='Dead if White plays first: the 2-2 placement.',
     prompt='White to play and kill.',
     notes='The throw-in from the side no longer works, because Black captures three stones for an eye. '
           'White goes straight to the 2-2 point instead.',
     lines=[Line(S(L1, 26), end='Dead.')])
note(title='L+1 group (long-side leg) with hanes on both sides', base=(L1, 27), to_move=O, player=O,
     status='Ko if White plays first.',
     prompt='White to play: get a ko.',
     notes='With both hane stones, the best White can do is the 2-2 attachment, which leads to a ko.',
     lines=[Line(S(L1, 28), end='Ko.')])
note(title='L+1 group with a weak leg, Black to play', base=(L1, 29), to_move=X, player=X,
     status='Unsettled: Black lives at the 2-2 point.',
     prompt='Black to play and live.',
     notes='The same point is vital for both sides: White kills there, Black lives there.',
     lines=[Line(mv('B', 'bb'), end='Alive.')])
note(title='L+1 group with a weak leg, White to play', base=(L1, 29), to_move=O, player=O,
     status='Unsettled: White kills at the 2-2 point.',
     prompt='White to play and kill.',
     notes='The same point is vital for both sides: White kills there, Black lives there.',
     lines=[Line(mv('W', 'bb'), end='Dead.')])

# ============================ J groups ============================
JG = 'J group'
note(title='J group, White to play', base=(JG, 1), to_move=O, player=O,
     status='Unsettled: White to play kills.',
     prompt='White to play and kill.',
     notes='Hane, placement on the vital point, descent, throw-in: a complete display of the killing techniques. '
           'The hane and placement can be played in either order. Known in China as the big pig\'s snout. '
           'Without the White stone below on the left edge, Black could escape and get a ko.',
     lines=[Line(S(JG, 2), end='Dead.'), Line(S(JG, 5), end='Dead.')])
note(title='J group, Black to play', base=(JG, 1), to_move=X, player=X,
     status='Unsettled: Black to play lives.',
     prompt='Black to play and live.',
     notes='Black lives best on the 1-2 point (the point White would use for the placement), with six points.',
     lines=[Line(mv('B', 'ab'), end='Alive with six points.')])
note(title='J group with a push', base=(JG, 6), to_move=O, player=O,
     status='Dead if White plays first. No ko.',
     prompt='White to play and kill.',
     notes='Descent, hane, then the placement: Black has no chance for a ko. (Gokyo Shumyo, section 2, problem 9.)',
     lines=[Line(S(JG, 6), end='Dead.')])
note(title='J group with an extra hane', base=(JG, 7), to_move=O, player=X,
     status='Alive, even if White plays first. No ko.',
     prompt='White attacks. Black to live.',
     notes='Against White\'s hane on top and descent on the left, Black lives. Black must not answer on the corner side '
           'of the hane, or Black dies as the J group without the hane does.',
     lines=[Line(S(JG, 8), end='Alive.')])
note(title='Straight J group', base=(JG, 11), to_move=O, player=O,
     status='Ko if White plays first (White captures first).',
     prompt='White to play: get the best result.',
     notes='Descending to the edge instead of the hanging connection improves Black\'s corner: White\'s best is a ko. '
           'The 2-1 hane then the 1-2 placement is the representative way; the 2-2 point first is a mistake, '
           'and Black lives with two eyes.',
     lines=[Line(S(JG, 11), end='Ko, White makes the first capture.')])
note(title='Straight J group with an outside liberty', base=(JG, 16), to_move=O, player=O,
     status='Still ko if White plays first.',
     prompt='White to play: get the best result.',
     notes='The second ko method (starting at the 1-3 point) fails with an outside liberty: Black sacrifices two stones and lives. '
           'The good method, hane then placement, still makes a ko.',
     lines=[Line(S(JG, 16), end='Ko.')])
note(title='Straight J group with an extra hane', base=(JG, 19), to_move=O, player=O,
     status='Ko if White plays first and Black has no outside liberties.',
     prompt='White to play: get the best result.',
     notes='The hane at the 3-1 point is wrong: Black\'s 1-3 point is a tesuji for life. With no outside liberties, '
           'the 1-3 point leads to a ko. With an outside liberty, Black is unconditionally alive.',
     lines=[Line(S(JG, 19), end='Ko.')])
note(title='Straight J group with an extra hane and an outside liberty', base=(JG, 20), to_move=O, player=X,
     status='Alive, even if White plays first.',
     prompt='White attacks. Black to live.',
     notes='With an outside liberty this shape is unconditionally alive. White can still capture two stones, '
           'then Black takes back at the 1-2 point.',
     lines=[Line(S(JG, 20), end='Alive (Black recaptures at the 1-2 point).')])

# ============================ Short J groups ============================
SJ = 'Short J Group'
note(title='Short J group', base=(SJ, 2), to_move=O, player=X,
     status='Alive, even if White plays first.',
     prompt='White attacks. Black to live.',
     notes='Black needs the right answer to each attack. The hane then descent on the left is White\'s strongest try: '
           'Black must throw in at the corner and lives by oshitsubushi. Answering the descent with the 1-4 point is a mistake '
           'that gives White a ko.',
     lines=[Line(S(SJ, 5), end='Alive (oshitsubushi).'), Line(S(SJ, 6), end='Alive (oshitsubushi).'),
            Line(S(SJ, 2), end='Alive, about 4 points.'), Line(S(SJ, 3), end='Alive: the remaining points are miai.'),
            Line(S(SJ, 4), end='Alive, but only 2 points.')])
note(title='Straight short J group', base=(SJ, 8), to_move=O, player=O,
     status='Dead if White plays first.',
     prompt='White to play and kill.',
     notes='The 1-2 placement is the eye-stealing tesuji, aiming at a snapback.',
     lines=[Line(S(SJ, 8), end='Dead.')])
note(title='Short J group with a White stone on top, Black to play', base=(SJ, 10), to_move=X, player=X,
     status='Unsettled: Black must defend.',
     prompt='Black to play and live.',
     notes='With the White stone on the top edge, Black must add a move at the 5-2 point. Otherwise White kills with the 2-2 point.',
     lines=[Line(lt(SJ, 10, 'Bb'), end='Alive.')])
note(title='Short J group with a White stone on top, White to play', base=(SJ, 10), to_move=O, player=O,
     status='Unsettled: White to play kills.',
     prompt='White to play and kill.',
     notes='The 2-2 point and the 1-2 hane reduce the corner to one eye. Black can capture the stone on the top, '
           'but it is only a false eye.',
     lines=[Line(S(SJ, 11), end='Dead: the eye on top is false.')])

# ============================ Hovercraft ============================
HC = 'Hovercraft'
note(title='Hovercraft', base=(HC, 1), to_move=O, player=X,
     status='Alive.',
     prompt='White hanes. Black to live.',
     notes='Often formed by a 3-3 invasion. Against the hane on the left, making the L+2 group saves all six stones '
           '(though White\'s other descent on top becomes sente).',
     lines=[Line(S(HC, 6), end='Alive: an L+2 group.')])
note(title='Hovercraft with a White descent, White to play', base=(HC, 7), to_move=O, player=O,
     status='Unsettled: White to play kills.',
     prompt='White to play and kill.',
     notes='The descent on the left edge changes the status from alive to unsettled. White kills with the 2-4 point and '
           'reaches a bent four in the corner.',
     lines=[Line(S(HC, 8), end='Dead: bent four in the corner.')])
note(title='Hovercraft with a White descent, Black to play', base=(HC, 7), to_move=X, player=X,
     status='Unsettled: Black to play lives.',
     prompt='Black to play and live.',
     notes='Black saves the corner by connecting at the 2-4 point.',
     lines=[Line(lt(HC, 7, 'Ba'), end='Alive.')])
JE = 'Joseki-related life-and-death example 2'
note(title='3-3 invasion corner after two Black moves on top', base=(JE, 3), to_move=X, player=X,
     status='Dead if Black plays first: cut, then the 1-2 placement.',
     prompt='Black to play and kill.',
     notes='A common 3-3 invasion shape. After Black\'s two stones on the top right, White\'s corner is no longer alive '
           'without another move. The cut and the placement kill.',
     sources=[JE, 'Trick play example 5'],
     lines=[Line(S(JE, 4), end='Dead.'), Line(S(JE, 5), end='Dead.')])

# ============================ Rectangular six ============================
RS = 'Rectangular six in the corner'
note(title='Rectangular six, no outside liberties, Black to play', base=(RS, 1), to_move=X, player=X,
     status='Unsettled: Black lives at the 2-2 or 1-2 point.',
     prompt='Black to play and live.',
     notes='Either point lives with 5 points of territory.',
     lines=[Line(lt(RS, 1, 'Ba'), end='Alive.'), Line(lt(RS, 1, 'Bb'), end='Alive.')])
note(title='Rectangular six, no outside liberties, White to play', base=(RS, 1), to_move=O, player=O,
     status='Unsettled: White kills unconditionally.',
     prompt='White to play and kill.',
     notes='After the 2-2 placement and the 2-1 point, Black cannot play either remaining point because of a shortage of liberties.',
     lines=[Line(S(RS, 2), end='Dead.')])
note(title='Rectangular six, one outside liberty', base=(RS, 3), to_move=O, player=O,
     status='Approach ko if White plays first.',
     prompt='White to play: get the best result.',
     notes='The 1-2 point is vital. Black\'s throw-in at the corner is necessary (otherwise White gets a bent four). '
           'White must win the ko twice; Black only once. The 2-2 placement fails because Black is not in atari.',
     lines=[Line(S(RS, 4), end='Approach ko.')])
note(title='Rectangular six, two outside liberties', base=(RS, 7), to_move=O, player=X,
     status='Alive, even if White plays first.',
     prompt='White attacks. Black to live.',
     notes='The one-liberty attack no longer works: Black plays oshitsubushi at the 2-3 point, and White cannot connect at the corner.',
     lines=[Line(S(RS, 8), end='Alive (oshitsubushi).')])
note(title='Weak rectangular six, Black to play', base=(RS, 12), to_move=X, player=X,
     status='Alive if Black plays first.',
     prompt='Black to play and live.',
     notes='The White stone at the corner of the shape creates a weakness. Black lives at the 1-2 point.',
     lines=[Line(mv('B', 'ab'), end='Alive.')])
note(title='Weak rectangular six, White to play', base=(RS, 12), to_move=O, player=O,
     status='Ko if White plays first (White takes first).',
     prompt='White to play: get the best result.',
     notes='The weak connection lets White make a ko with the 1-2 point.',
     lines=[Line(S(RS, 12), end='Ko.')])
RL = 'Rectangular six with leg in the corner'
note(title='Rectangular six with a leg, White to play', base=(RL, 1), to_move=O, player=O,
     status='Ko if White plays first.',
     prompt='White to play: get the best result.',
     notes='Between the walkie-talkie seven and the rectangular six. The 1-3 point is the right start; '
           'the 2-2 placement lets Black live with correct play.',
     lines=[Line(S(RL, 2), end='Ko.')])
note(title='Rectangular six with a leg, Black to play', base=(RL, 1), to_move=X, player=X,
     status='Alive if Black plays first.',
     prompt='Black to play and live.',
     notes='Black plays the 2-2 or 1-2 point; then only the hane-connect endgame remains.',
     lines=[Line(lt(RL, 1, 'Bb'), end='Alive.'), Line(lt(RL, 1, 'Bc'), end='Alive.')])

# ============================ Corner shapes (overview page) ============================
CS = 'Corner shapes'
note(title='Tripod group with an extra leg', base=(CS, 7), to_move=O, player=O,
     status='Ko if White plays first.',
     prompt='White to play: get a ko.',
     notes='Bigger than the tripod group but weaker. Formed when a tripod group exchanges the hane on top.',
     lines=[Line(lt(CS, 7, 'Wa', 'Bb', 'Wc'), end='Ko.')])
note(title='Short J group with an extra leg', base=(CS, 11), to_move=O, player=O,
     status='Ko if White plays first.',
     prompt='White to play: get a ko.',
     notes='Also called the little pig\'s snout. Like the tripod with an extra leg, the extra stone makes it weaker.',
     lines=[Line(lt(CS, 11, 'Wa'), end='Ko.')])
note(title='Weak carpenter\'s square (White at the corner), Black to play', base=(CS, 14), to_move=X, player=X,
     status='Unsettled: Black lives only at the vital point.',
     prompt='Black to play and live.',
     notes='Without the connection at the corner of the shape, Black must take the 2-2 point. White kills with almost any move.',
     lines=[Line(lt(CS, 14, 'Ba'), end='Alive.')])
note(title='Five stones on the second line, White to play', base=(CS, 15), to_move=O, player=O,
     status='Unsettled: White lives at the 5-1 point.',
     prompt='White to play and live.',
     notes='Five stones on the second line in the corner live or die by sente. Shorter groups are dead, longer ones alive.',
     lines=[Line(lt(CS, 15, 'Wa'), end='Alive.')])
note(title='Five stones on the second line, Black to play', base=(CS, 15), to_move=X, player=X,
     status='Unsettled: Black kills at the 5-1 point.',
     prompt='Black to play and kill.',
     notes='Five stones on the second line in the corner live or die by sente. Shorter groups are dead, longer ones alive.',
     lines=[Line(lt(CS, 15, 'Ba'), end='Dead.')])
note(title='Bent five on the second line, White to play', base=(CS, 16), to_move=O, player=O,
     status='Unsettled: White lives at the 5-1 point.',
     prompt='White to play and live.',
     notes='The same point is vital for both sides.',
     lines=[Line(lt(CS, 16, 'Wa'), end='Alive.')])
note(title='Bent five on the second line, Black to play', base=(CS, 16), to_move=X, player=X,
     status='Unsettled: Black kills at the 5-1 point.',
     prompt='Black to play and kill.',
     notes='The same point is vital for both sides.',
     lines=[Line(lt(CS, 16, 'Ba'), end='Dead.')])
note(title='Bent five on the second line (corner hook)', base=(CS, 17), to_move=O, player=O,
     status='Unsettled: White must live at the 1-1 point.',
     prompt='White to play and live.',
     notes='Other moves let Black kill. Black kills with the 1-1 point or either first-line hane.',
     lines=[Line(lt(CS, 17, 'Wa'), end='Alive.')])
note(title='Bent four in the corner, Black to play', base=(CS, 20), to_move=X, player=X,
     status='Black lives unconditionally at the vital point.',
     prompt='Black to play and live.',
     notes='The 1-2 point is vital for both sides.',
     lines=[Line(lt(CS, 20, 'Ba'), end='Alive.')])
note(title='Bent four in the corner, White to play', base=(CS, 20), to_move=O, player=O,
     status='Ko (if Black has fewer than two outside liberties).',
     prompt='White to play: get a ko.',
     notes='Under Japanese rules a group that can be reduced to a bent four in the corner, surrounded by live groups, is dead.',
     lines=[Line(lt(CS, 20, 'Wa'), end='Ko.')])
note(title='Bulky five in the corner, Black to play', base=(CS, 24), to_move=X, player=X,
     status='Unsettled: Black lives at the vital point.',
     prompt='Black to play and live.',
     notes='No different from the ordinary bulky five. The 1-1 point is a mistake: it makes a twisted four in the corner.',
     lines=[Line(lt(CS, 24, 'Ba'), end='Alive.')])
note(title='Bulky five in the corner, White to play', base=(CS, 24), to_move=O, player=O,
     status='Unsettled: White kills at the vital point.',
     prompt='White to play and kill.',
     notes='No different from the ordinary bulky five.',
     lines=[Line(lt(CS, 24, 'Wa'), end='Dead.')])
note(title='Gun six', base=(CS, 27), to_move=O, player=O,
     status='Seki if White plays first (no outside liberties).',
     prompt='White to play: make seki.',
     notes='Any of the three points next to the corner gives seki.',
     lines=[Line(mv('W', 'ba'), end='Seki.'), Line(mv('W', 'ab'), end='Seki.'), Line(mv('W', 'bb'), end='Seki.')])
note(title='Claw hammer six', base=(CS, 28), to_move=O, player=O,
     status='Seki if White plays first (no outside liberties).',
     prompt='White to play: make seki.',
     notes='After the third move, Black playing the remaining point inside would be self-atari.',
     lines=[Line(lt(CS, 28, 'Wa', 'Bb', 'Wc'), end='Seki.')])
note(title='Big P, White to play', base=(CS, 29), to_move=O, player=O,
     status='Seki or ko for Black if White plays first.',
     prompt='White to play: spoil the corner.',
     notes='It looks like six points of territory, but after White\'s 1-2 point Black gets only seki or ko.',
     lines=[Line(lt(CS, 29, 'Wa'), end='Black can only get seki or ko.')])
note(title='Big P, Black to play', base=(CS, 29), to_move=X, player=X,
     status='Black secures 5 points of territory.',
     prompt='Black to play: secure the corner.',
     notes='The 1-2 point is preferred because it leaves no ko threats; the two other points inside also work.',
     lines=[Line(lt(CS, 29, 'Ba'), end='Alive, no ko threats left.'), Line(mv('B', 'bb'), end='Alive.'), Line(mv('B', 'ac'), end='Alive.')])
note(title='Bulky seven in the corner', base=(CS, 31), to_move=X, player=X,
     status='Black secures 6 points at the vital point.',
     prompt='Black to play: secure the corner.',
     notes='If White plays first, it becomes seki or a ten-thousand-year ko.',
     lines=[Line(lt(CS, 31, 'Ba'), end='Six points of territory.')])
note(title='Walkie-talkie eight in the corner', base=(CS, 35), to_move=X, player=X,
     status='Black secures 7 points.',
     prompt='Black to play: secure the corner.',
     notes='If White plays first, she can make seki in gote. A Black stone in place of the White stone at the corner of the shape '
           'would make it alive with 8 points.',
     lines=[Line([('X', p)], end='Seven points of territory.') for p in sorted(
         q for q, lab in cells(CS, 35).items() if lab == 'a')])
note(title='Bulky nine in the corner', base=(CS, 37), to_move=O, player=O,
     status='Seki if White plays first.',
     prompt='White to play: make seki.',
     notes='',
     lines=[Line(lt(CS, 37, 'Wa'), end='Seki.')])
note(title='Four plus five', base=(CS, 38), to_move=O, player=X,
     status='Alive with territory: White cannot make seki.',
     prompt='White attacks. Black to answer.',
     notes='Against White\'s 1-4 point Black answers at the 2-3 point; against anything else, Black plays the 1-4 point.',
     lines=[Line(lt(CS, 38, 'Wa', 'Bb'), end='Alive with territory.')])
note(title='Bulky ten in the corner', base=(CS, 39), to_move=O, player=O,
     status='Seki or ko if White plays first.',
     prompt='White to play: spoil the corner.',
     notes='Even ten spaces in the corner are not alive with territory.',
     lines=[Line(lt(CS, 39, 'Wa'), end='Seki or ko.')])
note(title='Staircase ten', base=(CS, 40), to_move=O, player=O,
     status='Seki if White plays first.',
     prompt='White to play: make seki.',
     notes='After White\'s 2-2 point, the 1-3 and 3-1 points are miai.',
     lines=[Line(lt(CS, 40, 'Wa'), end='Seki: the two remaining points are miai.')])
note(title='Eleven spaces in the corner', base=(CS, 41), to_move=O, player=O,
     status='Not Black\'s area if White plays first.',
     prompt='White to play: spoil the corner.',
     notes='The 2-2 point is vital.',
     lines=[Line(mv('W', 'bb'), end='Black\'s corner is not area.')])
note(title='Twelve spaces in the corner', base=(CS, 42), to_move=O, player=X,
     status='Alive with territory.',
     prompt='White attacks. Black to answer.',
     notes='Closed corner shapes of twelve or more spaces, without cutting points or enemy stones inside, are alive with territory. '
           'The two central points are miai.',
     lines=[Line(lt(CS, 42, 'Wa', 'Bb'), end='Alive.'), Line(lt(CS, 42, 'Wb', 'Ba'), end='Alive.')])

# ============================ L+2 groups ============================
L2 = 'L+2 group'
note(title='L+2 group', base=(L2, 1), to_move=O, player=X,
     status='Alive.',
     prompt='White attacks. Black to live.',
     notes='Against a hane from the short side, defend at the 1-2 point; from the long side, at the 2-2 point. '
           'Answering the short-side hane at the 2-2 point only gives seki.',
     lines=[Line(S(L2, 2), end='Alive: two sure eyes.'), Line(S(L2, 4), end='Alive: two sure eyes.'),
            Line(S(L2, 8), end='Alive.'), Line(S(L2, 9), end='Alive.'),
            Line(S(L2, 10), end='Alive: the two remaining points are miai.'),
            Line(S(L2, 11), end='Alive: the two remaining points are miai.')])
note(title='L+2 group with a weak leg', base=(L2, 13), to_move=O, player=O,
     status='Ko (a two-stage ko) if White plays first.',
     prompt='White to play: get a ko.',
     notes='Black cannot atari at the 3-1 point because of a shortage of liberties.',
     lines=[Line(S(L2, 14), end='Two-stage ko.')])
note(title='L+2 group with a weak leg (missing corner stone)', base=(L2, 15), to_move=O, player=O,
     status='Ko if White plays first.',
     prompt='White to play: get a ko.',
     notes='Black\'s 1-2 and 2-1 replies are best. Black then plays forcing moves before fighting the ko.',
     lines=[Line(S(L2, 16), end='Ko.')])
LD = 'L+2 group with descent'
note(title='L+2 group with a short-side descent', base=(LD, 1), to_move=X, player=X,
     status='Two-stage ko if Black plays first.',
     prompt='Black to play: get the best result.',
     notes='The descent spoils the L+2 group. The 2-2 then 1-3 tesuji leads to a two-stage ko with correct play by White; '
           'White\'s atari on the inside is a mistake that dies. White\'s 1-3 answer gives a direct ko with Black taking first.',
     lines=[Line(S(LD, 2), S(LD, 4, first=4), checks=[(1, LD, 4)], end='Two-stage ko.'),
            Line(S(LD, 2), S(LD, 3, first=4), checks=[(1, LD, 3)], end='White is dead.'),
            Line(S(LD, 6), end='Direct ko, Black takes first.')])
J1 = 'J+1 group'
note(title='J+1 group', base=(J1, 1), to_move=X, player=O,
     status='Alive.',
     prompt='Black attacks. White to live.',
     notes='The J+1 group on its own is unconditionally alive, as long as White answers each attack.',
     lines=[Line(S(J1, 2), end='Alive.'), Line(S(J1, 3), end='Alive.'), Line(S(J1, 4), end='Alive.')])
note(title='J+1 group with a descent, Black to play', base=(J1, 8), to_move=X, player=X,
     status='Dead if Black plays first.',
     prompt='Black to play and kill.',
     notes='The throw-in then the placement turn the corner into a bent four in the corner.',
     lines=[Line(S(J1, 9), end='Dead: bent four in the corner.')])
note(title='J+1 group with a descent, White to play', base=(J1, 8), to_move=O, player=O,
     status='White must defend: the descent is sente.',
     prompt='White to play and live.',
     notes='White needs a move at the 1-2 point.',
     lines=[Line(lt(J1, 8, 'Wa'), end='Alive.')])

# ============================ Long L groups ============================
LL = 'Long L group'
note(title='Long L group, no outside liberties', base=(LL, 2), to_move=O, player=O,
     status='Ten-thousand-year ko if White plays first.',
     prompt='White to play: get the best result.',
     notes='White\'s best attack makes a ten-thousand-year ko. Black should not take the ko at the 1-4 point: '
           'that makes a direct ko instead, which is worse for Black.',
     lines=[Line(S(LL, 3), end='Ten-thousand-year ko.'),
            Line(S(LL, 3, at={6: 'a'}), end='Direct ko (Black\'s mistake).')])
note(title='Long L group with a hane on top', base=(LL, 5), to_move=O, player=O,
     status='Ten-thousand-year ko if White plays first.',
     prompt='White to play: get the best result.',
     notes='The usual 2-2 clamp fails: Black lives at the 2-3 point and White cannot bridge under. '
           'White starts from the 1-4 point instead.',
     lines=[Line(S(LL, 6), end='Ten-thousand-year ko.')])
note(title='Long L group with an outside liberty', base=(LL, 8), to_move=O, player=X,
     status='Alive (at worst gote seki).',
     prompt='White attacks. Black to live.',
     notes='The key move is the 1-3 point, aiming at the 1-2 point. If White ataris, Black sacrifices another stone '
           'and takes back; the extra liberty makes the difference.',
     lines=[Line(S(LL, 9), S(LL, 10, first=5), checks=[(1, LL, 10)], end='Seki (as good as alive).'),
            Line(S(LL, 9), S(LL, 11, first=5, at={8: 'B6'}), S(LL, 12, first=9), checks=[(2, LL, 12)], end='Alive: White is caught in a connect-and-die.'),
            Line(S(LL, 9), S(LL, 11, first=5, at={8: 'B6'}), S(LL, 13, first=9), checks=[(2, LL, 13)], end='Alive.')])
note(title='Long L group after a White descent on top', base=(LL, 15), to_move=O, player=O,
     status='Dead if White plays first: Black must answer the descent.',
     prompt='White to play and kill.',
     notes='Black\'s attempt at a ko lacks liberties. The 2-2 point can also be played at the 2-3 point.',
     lines=[Line(S(LL, 16), end='Dead.')])
note(title='Long L group after a White descent on the left', base=(LL, 19), to_move=O, player=O,
     status='Dead if White plays first.',
     prompt='White to play and kill.',
     notes='Shortage of liberties again: Black cannot play the 1-3 point at the end.',
     lines=[Line(S(LL, 20), end='Dead.')])
TK = 'Ten Thousand Year Ko'
note(title='Ten-thousand-year ko', base=(TK, 1), to_move=O, player=X,
     status='Ten-thousand-year ko: whoever converts it lets the other side take first. Often seki.',
     prompt='White converts to a direct ko. Black to respond.',
     notes='White cannot fill the ko herself (she would die as a bulky five). If neither side fights, it is seki at the end. '
           'The ko usually favours the side with fewer stones in it.',
     lines=[Line(S(TK, 2), end='Direct ko, Black took first.')])

# ============================ Other shapes ============================
FS = 'Flying Saucer Shape'
note(title='Flying saucer shape', base=(FS, 1), to_move=X, player=O,
     status='Dead.',
     prompt='Black tries to live. Kill as White.',
     notes='Black is blocked on the second line at both ends, the weak points are occupied, and the blocking stones are '
           'connected. The circled liberties do not matter.',
     lines=[Line(S(FS, 2), end='Dead.'), Line(S(FS, 3), end='Dead.'), Line(S(FS, 4), end='Dead.'),
            Line(S(FS, 5), end='Dead.'), Line(S(FS, 6), end='Dead.'), Line(S(FS, 7), end='Dead.')])
CF = 'Comb Formation'
note(title='Broken comb formation in the corner, Black to play', base=(CF, 2), to_move=X, player=X,
     status='Alive if Black plays first.',
     prompt='Black to play and live.',
     notes='Also called the weak rectangular six in the corner. Black lives at the 2-1 point.',
     lines=[Line([('X', p) for c, p in S(CF, 2, upto=1)], end='Alive.')])
note(title='Broken comb formation in the corner, White to play', base=(CF, 2), to_move=O, player=O,
     status='Ko if White plays first.',
     prompt='White to play: get a ko.',
     notes='The cutting point gives White a ko.',
     lines=[Line(S(CF, 2), end='Ko.')])
CQ = "Carpenter's Square"
note(title='Carpenter\'s square, White to play', base=(CQ, 1), to_move=O, player=O,
     status='Ko if White plays first.',
     prompt='White to play: get a ko.',
     notes='The 2-2 placement is basic: it works even with outside liberties or a hane. Black must attach on the first line. '
           'The clamp also makes a ko (a throw-in ko with White taking first); Black\'s natural-looking 1-3 point there is a mistake. '
           'The 2-1 point is a trick play.',
     lines=[Line(S(CQ, 2), S(CQ, 3), checks=[(1, CQ, 3)], end='Ko.'),
            Line(S(CQ, 5), end='Throw-in ko, White takes first.'),
            Line(S(CQ, 6), end='Dead (unless Black can escape on the outside).')])
note(title='Carpenter\'s square, Black to play', base=(CQ, 1), to_move=X, player=X,
     status='Alive if Black plays first.',
     prompt='Black to play and live.',
     notes='Almost any move lives. The 2-2 point is usual: it makes both of White\'s hanes gote in the endgame.',
     lines=[Line(lt(CQ, 1, 'Ba'), end='Alive.')])
note(title='Carpenter\'s square, one outside liberty', base=(CQ, 8), to_move=O, player=O,
     status='Ko if White plays first.',
     prompt='White to play: get a ko.',
     notes='The basic method fails with an outside liberty: Black squeezes after the ko. White sets up the ko differently. '
           'Black\'s atari at the 1-3 point instead of the 2-3 point dies.',
     lines=[Line(S(CQ, 8), end='Ko.'),
            Line(S(CQ, 8, upto=3), S(CQ, 9), checks=[(1, CQ, 9)], end='Dead.')])
note(title='Carpenter\'s square with one hane', base=(CQ, 12), to_move=O, player=O,
     status='Ko if White plays first.',
     prompt='White to play: get a ko.',
     notes='White again plays the 2-2 point. If Black answers at the 1-2 point, White extends toward the hane: direct ko.',
     lines=[Line(S(CQ, 13), end='Ko.'), Line(S(CQ, 14), end='Direct ko.')])
note(title='Carpenter\'s square with one hane and one liberty', base=(CQ, 15), to_move=O, player=O,
     status='A very indirect ko if White plays first.',
     prompt='White to play: get the best result.',
     notes='From the book Life and Death. Neither player has a strong incentive to make the next move.',
     lines=[Line(S(CQ, 15), end='Indirect ko.')])

# ============================ Pages added later ============================
BF = 'Bent four in the corner'
note(title='Bent four in the corner, fewer than two outside liberties', base=(BF, 3), to_move=X, player=X,
     status='Ko (Black to play starts it at the vital point).',
     prompt='Black to play: get a ko.',
     notes='White cannot play oshitsubushi at the 1-3 point because it would be self-atari, so the group\'s fate is decided by a ko. '
           'With one outside liberty Black later finishes by making a bent three inside; with none, by capturing everything.',
     lines=[Line(S(BF, 4), end='Ko.')])
note(title='Bent four in the corner, two outside liberties', base=(BF, 7), to_move=X, player=O,
     status='Alive: White crushes the ko with oshitsubushi.',
     prompt='Black attacks. White to live.',
     notes='With two or more outside liberties White can play the atari on the inside, because Black cannot take back.',
     lines=[Line(S(BF, 7), S(BF, 8, first=5), checks=[(1, BF, 8)], end='Alive: White captures two stones.')])
note(title='Avoiding the bent four in the corner', base=(BF, 12), to_move=X, player=X,
     status='Alive with four points if Black plays the 5-1 point.',
     prompt='Black to play and live.',
     notes='Playing on the left side lives too, but costs two points; a move at the corner would make a bent four in the corner.',
     lines=[Line(S(BF, 12), end='Alive with four points.')])
for k, t in ((13, '1'), (14, '2'), (15, '3')):
    note(title=f'Bent four that is not in the corner {t}', base=(BF, k), to_move=O, player=X,
         status='Alive: the two remaining points are miai.',
         prompt='White attacks. Black to live.',
         notes='A bent four shape that happens to sit in the corner, but not the "bent four in the corner" of the proverb.',
         lines=[Line(lt(BF, k, 'Wa', 'Bb'), end='Alive.'), Line(lt(BF, k, 'Wb', 'Ba'), end='Alive.')])
BD = 'Bent four in the corner is dead'
note(title='Bent four in the corner is dead (first precursor)', base=(BD, 4), to_move=X, player=X,
     status='Dead under Japanese rules: Black can always win the ko.',
     prompt='Outside liberties filled, no White ko threats. Black to kill.',
     notes='White cannot play inside without dying, so Black waits until the end, fills the outside liberties, removes White\'s ko '
           'threats, reduces the eye to the L-shaped bent four, and starts the ko. White has no threat, so Black captures.',
     lines=[Line(S(BD, 5), S(BD, 6, first=3), [('O', None)], lt(BD, 6, 'Ba'), checks=[(1, BD, 6)], end='Dead.')])
note(title='Bent four in the corner is dead (second precursor)', base=(BD, 7), to_move=X, player=X,
     status='Dead under Japanese rules: Black can always win the ko.',
     prompt='Outside liberties filled, no White ko threats. Black to kill.',
     notes='Same procedure as the first precursor: fill the liberties, remove the threats, then start the ko.',
     lines=[Line(S(BD, 8), end='Ko started; White has no threat.')])
note(title='Bent four in the corner with an extra Black stone', base=(BD, 9), to_move=O, player=O,
     status='Alive (with two or more outside liberties).',
     prompt='White to play and live.',
     notes='The extra Black stone, or playing it too early, lets White capture and then live with oshitsubushi.',
     lines=[Line(S(BD, 10), S(BD, 11, first=2), checks=[(1, BD, 11)], end='Alive (oshitsubushi).')])
for k, (pg, tm, pl, st, pr, nt_) in enumerate([
        ('Bent four in the corner exercises _ Solution 1', X, X, 'Alive if Black plays the 2-1 point.', 'Black to play and live.',
         'A solid eye on the edge leaves the two other points miai. The 1-3 point instead lets White start a ko.'),
        ('Bent four in the corner exercises _ Solution 2', X, X, 'Alive if Black plays the 1-1 point.', 'Black to play and live.',
         'The corner point makes the two remaining points miai; White cannot start a ko because Black just captures.'),
        ('Bent four in the corner exercises _ Solution 3', O, O, 'Dead if White plays the 2-1 point.', 'White to play and kill.',
         'The vital point kills unconditionally. If Black tries to extend, White seals him in and reduces him to a bent four.'),
        ('Bent four in the corner exercises _ Solution 4', X, X, 'Alive if Black plays the 2-1 point.', 'Black to play and live.',
         'A certain eye first; if White blocks the second, Black extends along the side.')], 1):
    note(title=f'Bent four exercise {k}', base=(pg, 1), to_move=tm, player=pl, status=st, prompt=pr, notes=nt_,
         sources=[pg, 'Bent four in the corner exercises'],
         lines=[Line(S(pg, 1), end='Correct.')] + ([Line(S(pg, 2), end='Dead.')] if k == 3 else []))
BS = 'Bulky Seven'
note(title='Bulky seven on the side', base=(BS, 1), to_move=O, player=O,
     status='Dead if White plays first: the group is not solidly connected.',
     prompt='White to play and kill.',
     notes='White strikes the centre of the shape. From Kageyama\'s Lessons in the Fundamentals of Go. '
           'Playing first at the other point lets Black make a ko.',
     lines=[Line(S(BS, 1), end='Dead.'), Line(S(BS, 1, at={2: 'W3', 3: 'a'}), end='Dead.')])
BC = 'Bulky seven in the corner'
note(title='Bulky seven in the corner, White to play', base=(BC, 1), to_move=O, player=O,
     status='Seki or a ten-thousand-year ko if White plays first.',
     prompt='White to play: spoil the corner.',
     notes='Black can also make seki the other way, but must then add the last move or White kills. '
           'White\'s other first move is a mistake: Black can resolve the ko and White cannot.',
     lines=[Line(S(BC, 3), end='Ten-thousand-year ko.'), Line(S(BC, 4), end='Seki.'),
            Line(S(BC, 5), end='Dead (Black omitted the necessary move).')])
GS = 'Gun Six'
note(title='Gun six, Black to play', base=(GS, 1), to_move=X, player=X,
     status='Alive with 5 points.',
     prompt='Black to play and secure the corner.',
     notes='Either point next to the corner lives with 5 points. The 2-2 point also does, but leaves White a bigger ko threat.',
     lines=[Line(mv('B', 'ba'), end='Alive.'), Line(mv('B', 'ab'), end='Alive.'),
            Line(mv('B', 'bb'), end='Alive, but White keeps a ko threat.')])
note(title='Gun six with an outside liberty', base=(GS, 5), to_move=O, player=X,
     status='Alive with 5 points, even if White plays first.',
     prompt='White attacks. Black to live.',
     notes='The outside liberty lets Black atari; without it that atari would be self-atari.',
     lines=[Line(S(GS, 6), end='Alive.')])
GE = 'Gun Eight'
note(title='Gun eight, White to play', base=(GE, 1), to_move=O, player=O,
     status='Seki, or a ko if Black wants it (no outside liberties).',
     prompt='White to play: spoil the corner.',
     notes='After the 2-2 point Black threatens to atari, forcing White\'s descent. Seki is usual; Black can choose a two-stage ko, '
           'which favours White.',
     lines=[Line(S(GE, 2), S(GE, 3, first=4), checks=[(1, GE, 3)], end='Seki in sente.'),
            Line(S(GE, 7), end='Seki.'), Line(S(GE, 5), end='Two-stage ko.')])
note(title='Gun eight with an outside liberty', base=(GE, 9), to_move=O, player=X,
     status='Alive with 7 points.',
     prompt='White attacks. Black to live.',
     notes='The outside liberty lets Black atari at the end.',
     lines=[Line(S(GE, 10), end='Alive.')])
BE = 'Bulky Eight in the Corner'
note(title='Bulky eight in the corner, Black to play', base=(BE, 2), to_move=X, player=X,
     status='Alive if Black takes the vital point.',
     prompt='Black to play and live.',
     notes='',
     lines=[Line(S(BE, 2), end='Alive.')])
note(title='Bulky eight in the corner, White to play', base=(BE, 2), to_move=O, player=O,
     status='Sente seki, or a ten-thousand-year ko.',
     prompt='White to play: spoil the corner.',
     notes='After the 2-2 point Black can play elsewhere. White can later make a ten-thousand-year ko, or leave it for seki.',
     lines=[Line(S(BE, 6), end='Ten-thousand-year ko (or White leaves it as seki).')])
note(title='Bulky eight without a descent', base=(BE, 12), to_move=O, player=O,
     status='Dead if White plays first.',
     prompt='White to play and kill.',
     notes='Missing the descent on the left, Black has a shortage of liberties.',
     lines=[Line(S(BE, 13), end='Dead.'), Line(S(BE, 14), end='Dead.')])
RE = 'Rectangular Eight in the Corner'
note(title='Rectangular eight in the corner, Black to play', base=(RE, 1), to_move=X, player=X,
     status='Alive: many moves live, the 2-3 point is best.',
     prompt='Black to play and live.',
     notes='The 2-3 point is least affected by White\'s ko threats, and is also White\'s key point.',
     lines=[Line(lt(RE, 1, 'B' + a), end='Alive.' if a == 'a' else 'Alive, but more exposed to ko threats.') for a in 'abcdefg'])
note(title='Rectangular eight in the corner, White to play', base=(RE, 2), to_move=O, player=O,
     status='Hyperactive: White\'s 2-3 point gives seki in sente (no outside liberties).',
     prompt='White to play: spoil the corner.',
     notes='Black\'s 1-2 point avoids a ko; the 1-4 point at the end is necessary. Other Black answers give a ten-thousand-year ko '
           'or an approach ko.',
     lines=[Line(S(RE, 3), end='Seki in sente.'), Line(S(RE, 4), end='Ten-thousand-year ko.'), Line(S(RE, 5), end='Approach ko.')])
note(title='Rectangular eight with an outside liberty', base=(RE, 8), to_move=O, player=X,
     status='Alive with 7 points.',
     prompt='White attacks. Black to live.',
     notes='Against White\'s 2-3 point, any of the three points around it works.',
     lines=[Line(S(RE, 9) + [('X', p)], end='Alive.') for p in sorted(q for q, lab in cells(RE, 9).items() if lab == '.(c)')])
SN = 'Square nine in the corner'
note(title='Square nine in the corner', base=(SN, 1), to_move=O, player=O,
     status='Sente seki if White plays first (no outside liberties).',
     prompt='White to play: make seki.',
     notes='Black\'s last move prevents a ten-thousand-year ko; if Black skips it, White kills with a bulky five.',
     lines=[Line(S(SN, 2), end='Seki.'), Line(S(SN, 2, at={6: 'b'}), end='Seki.'),
            Line(S(SN, 3), end='Dead (Black tenukied).'), Line(S(SN, 4), end='Seki.'),
            Line(S(SN, 5), end='Two-stage ko.')])
note(title='Square nine with one outside liberty', base=(SN, 9), to_move=O, player=O,
     status='Seki, but White must add a move in gote.',
     prompt='White to play: make seki.',
     notes='The same main line, then White fills the outside liberty.',
     lines=[Line(S(SN, 9), end='Seki (White ends in gote).')])
note(title='Square nine with two outside liberties', base=(SN, 10), to_move=O, player=X,
     status='Alive: the seki attempt fails.',
     prompt='White attacks. Black to live.',
     notes='White\'s moves are better kept as ko threats.',
     lines=[Line(S(SN, 10), end='Alive.')])
WT = 'Walkie Talkie Seven'
note(title='Walkie-talkie seven', base=(WT, 2), to_move=O, player=O,
     status='Seki or ko if White plays first (two or fewer outside liberties).',
     prompt='White to play: spoil the corner.',
     notes='After the vital point, Black can play elsewhere (White then chooses seki or a throw-in ko) or make a '
           'ten-thousand-year ko. Answering on the edge instead gives a direct ko, which is worse for Black.',
     lines=[Line(S(WT, 2), end='Black tenukis or makes a ten-thousand-year ko.'), Line(S(WT, 13), end='Direct ko.')])
TG = 'Tripod Group'
note(title='Tripod group', base=(TG, 2), to_move=O, player=X,
     status='Alive, if Black answers each attack correctly.',
     prompt='White attacks. Black to live.',
     notes='Block on the left: answer at the 1-3 point (making a short J group). Push on top: answer at the 2-2 point. '
           '1-3 placement: answer at the 2-2 point, and later the throw-in at the corner is the key.',
     lines=[Line(S(TG, 3), end='Alive (now a short J group).'),
            Line(S(TG, 11), end='Alive.'),
            Line(S(TG, 11), S(TG, 12), checks=[(1, TG, 12)], end='Alive.'),
            Line(S(TG, 11), S(TG, 13), checks=[(1, TG, 13)], end='Alive.'),
            Line(S(TG, 17), end='Alive.'),
            Line(S(TG, 17), S(TG, 18), S(TG, 19), checks=[(1, TG, 18), (2, TG, 19)], end='Alive (oshitsubushi).'),
            Line(S(TG, 17), S(TG, 18), S(TG, 20), checks=[(1, TG, 18), (2, TG, 20)], end='Alive (oshitsubushi).')])
note(title='Tripod group with a White stone on top', base=(TG, 26), to_move=O, player=O,
     status='Dead if White plays first.',
     prompt='White to play and kill.',
     notes='Surrounding stones matter: with this stone the block and the 2-2 point kill.',
     lines=[Line(S(TG, 26), end='Dead.')])
note(title='Tripod group with a White stone on the left', base=(TG, 27), to_move=O, player=O,
     status='Dead if White plays first.',
     prompt='White to play and kill.',
     notes='The push on top kills; the 1-4 point falsifies the eye on the side.',
     lines=[Line(S(TG, 27), end='Dead.')])
J3 = 'Joseki Related Life And Death Example 3 _ Solution'
note(title='Corner after a 3-3 invasion (joseki example 3)', base=(J3, 1), to_move=X, player=X,
     status='Black to play gets at least a ko; most White defences die.',
     prompt='Black to play: attack the corner.',
     notes='The 2-1 placement. White\'s best resistance leads to a ko.',
     sources=[J3, 'Joseki-related life-and-death example 3'],
     lines=[Line(S(J3, 1), end='Ko.'), Line(S(J3, 2), end='Dead.'), Line(S(J3, 3), end='Dead.'),
            Line(S(J3, 4), end='Dead.'), Line(S(J3, 5), end='Dead.')])
J5 = 'Joseki-related life-and-death example 5'
note(title='3-3 invasion under a 4-4 stone: White to live', base=(J5, 2), to_move=O, player=O,
     status='Alive if White plays the diagonal move under the block.',
     prompt='White to play and live.',
     notes='After the 3-3 invasion and Black\'s block, the diagonal move lives unconditionally. Turning at the 4-3 point is bad shape.',
     lines=[Line(S(J5, 3), end='Alive: the remaining points are miai.'), Line(S(J5, 4), end='Alive.'),
            Line(S(J5, 10, first=3), S(J5, 11), checks=[(1, J5, 11)], end='Alive.')])
note(title='3-3 invasion: White\'s bad shape', base=(J5, 5), pre=S(J5, 5), to_move=X, player=X,
     status='Black kills, or at best White gets a ko.',
     prompt='Black to play and kill.',
     notes='Black\'s hane at the head of two stones is too good. Locally White cannot make two eyes; only the clamp aji remains.',
     lines=[Line(S(J5, 6, first=4), end='Dead (clamp aji remains).'),
            Line(S(J5, 6, first=4, upto=4), S(J5, 7), checks=[(1, J5, 7)], end='Dead: a basic dead shape.'),
            Line(S(J5, 6, first=4, upto=4), S(J5, 8), checks=[(1, J5, 8)], end='Ko.')])
J9 = 'Joseki-related life-and-death example 9'
note(title='J group from a joseki (example 9)', base=(J9, 1), to_move=O, player=O,
     status='Ko if White plays first.',
     prompt='White to play: get the best result.',
     notes='Keep the J group in mind. Black\'s diagonal answer instead dies to the standard killing sequence.',
     lines=[Line(S(J9, 3), end='Ko.'), Line(S(J9, 4), end='Dead.'), Line(S(J9, 5), end='Dead.')])
CA = 'The comb formation is alive'
note(title='Comb formation on the side', base=(CA, 1), to_move=O, player=X,
     status='Alive: the two central points are miai.',
     prompt='White attacks. Black to live.',
     notes='Answer White\'s placement on the second line underneath it, and the first-line placement above it; then the two remaining '
           'points are miai. White\'s first-line blocks at either end are sente, so keep them as ko threats.',
     sources=[CA, 'Comb Formation'],
     lines=[Line(S(CA, 2), end='Alive.'), Line(S(CA, 2, at={3: 'B4', 4: 'W3'}), end='Alive.'),
            Line(S(CA, 3), end='Alive.'), Line(S(CA, 3, at={3: 'B4', 4: 'W3'}), end='Alive.'),
            Line(S(CA, 4), end='Alive.')])

CW = "Carpenter's Square - Wrong Attack"
note(title='Carpenter\'s square: the 2-1 trick', base=(CW, 1), pre=S(CW, 1), to_move=X, player=X,
     status='Alive: the descent at the 1-4 point guarantees life (seki at worst).',
     prompt='White played the 2-1 point. Black to live.',
     notes='The 2-1 point is a wrong attack, but the defence is hard to find. After the descent, White\'s 2-2 point gives seki, '
           'and White\'s 3-2 point is met by the 2-1 placement tesuji. In the main line Black must play the vital points '
           'and finally captures two White stones by connect-and-die. Descending on the other side fails.',
     sources=[CW, "Carpenter's Square"],
     lines=[Line(S(CW, 2), S(CW, 3, first=2), end='Seki.'),
            Line(S(CW, 2), S(CW, 4, first=2), S(CW, 5, first=4), end='Seki.'),
            Line(S(CW, 2), S(CW, 4, first=2), S(CW, 6, first=4), S(CW, 7, first=6), S(CW, 8), end='Alive: two White stones die by connect-and-die.')])
WC = "Weak Carpenter's Square"
note(title='Weak carpenter\'s square (corner vacant), White to play', base=(WC, 2), to_move=O, player=O,
     status='Dead if White plays first.',
     prompt='White to play and kill.',
     notes='After the 2-2 point White reduces Black to a squared four, a bulky five or a rectangular six in the corner.',
     lines=[Line(S(WC, 2), end='Dead: the remaining points are miai.'), Line(S(WC, 3), end='Dead: rectangular six in the corner.')])
note(title='Weak carpenter\'s square (White at the corner), White to play', base=(WC, 4), to_move=O, player=O,
     status='Dead if White plays first.',
     prompt='White to play and kill.',
     notes='With White on the corner of the shape there are many ways to kill after the 2-2 point. Black cannot take the last point '
           'because it is self-atari.',
     lines=[Line(S(WC, 4), end='Dead.'), Line(S(WC, 5), end='Dead: the remaining points are miai.')])
TL = 'Tripod Group with Extra Leg'
note(title='Tripod group with an extra leg (ko)', base=(TL, 1), to_move=O, player=O,
     status='Ko if White plays first (throw-in ko).',
     prompt='White to play: get a ko.',
     notes='The extra exchange on top costs Black a liberty, so oshitsubushi no longer works. The 2-1 point and the descent are the tesuji; '
           'Black takes the ko first, which is best for both. Black\'s throw-in at the corner instead lets White take first.',
     lines=[Line(S(TL, 2), end='Throw-in ko, Black takes first.'), Line(S(TL, 3), end='Ko, White takes first.')])
note(title='Tripod group with an extra leg (variant)', base=(TL, 13), to_move=O, player=X,
     status='Alive.',
     prompt='White attacks. Black to live.',
     notes='With the stones on the left side arranged this way, the group is unconditionally alive; White only gains a little '
           'in the endgame by capturing two and giving back one.',
     lines=[Line(S(TL, 14), end='Alive.')])


# ============================ Japanese names ============================
# Only names given on the Sensei's Library pages (kanji and romanization from
# the page; kana from that romanization). Audio: ElevenLabs TTS of the kana
# (Vocab/tts.py), stored as media/go_ja_<key>.mp3.
JAPANESE = {
    'kagigata': ('カギ型', 'かぎがた', 'kagi gata'),
    'sumi_no_hachimokukei': ('隅の八目形', 'すみのはちもくけい', 'sumi no hachimokukei'),
    'sumi_no_itaroku': ('隅の板六', 'すみのいたろく', 'sumi no itaroku'),
    'sumi_no_magari_yonmoku': ('隅の曲り四目', 'すみのまがりよんもく', 'sumi no magari yon moku'),
    'ichigou_masu': ('一合マス', 'いちごうます', 'ichigou masu'),
    'kushigata': ('クシ型', 'くしがた', 'kushi gata'),
    'mannenkou': ('万年コウ', 'まんねんこう', 'mannen-kō'),
}


def japanese_for(title):
    t = title.lower()
    if t == 'l group': return 'kagigata'
    if t.startswith('long l group'): return 'sumi_no_hachimokukei'
    if t.startswith('rectangular six,'): return 'sumi_no_itaroku'
    if t.startswith('bent four in the corner'): return 'sumi_no_magari_yonmoku'
    if t.startswith("carpenter's square"): return 'ichigou_masu'
    if t == 'comb formation on the side': return 'kushigata'
    if t == 'ten-thousand-year ko': return 'mannenkou'
    return None


for _nt in NOTES:
    _k = japanese_for(_nt['title'])
    if _k:
        kanji, kana, romaji = JAPANESE[_k]
        _nt['japanese'] = f'<ruby>{kanji}<rt>{kana}</rt></ruby> ({romaji}) [sound:go_ja_{_k}.mp3]'
