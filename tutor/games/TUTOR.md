# Minigames

You can attach a small interactive minigame to a question. It runs in the page, under that question's prompt, in a sandboxed frame. It lets the student try an idea with their own hands: satisfy a rule, vary a parameter, step through a process.

## When

- Mainly to **introduce** an idea that's best learned by trying it, such as a puzzle whose rule is the definition: tricolor a knot, color a graph, find a permutation that solves a puzzle, sort with only swaps, wire gates to make XOR, drag a slider to see Hardy–Weinberg frequencies drift. Also after a miss, when hands-on practice would fix it better than a picture.
- Not for anything a sentence of feedback covers just as well, and not for vocabulary or facts.
- Use one when a thread has found a real gap or is introducing a new idea, at most about one per thread every 4 questions. Writing one takes you a while, and the other threads wait meanwhile, so write it after everything else (see "How").

## How

1. Grade, reply, and add the other threads' next questions first, as always.
2. Add the question the game belongs to, with `"game": true`. The page shows "Building a minigame…" under its prompt until the game arrives. The prompt asks about what the game reveals ("Try to tricolor both knots below. Which one has no tricoloring?"), and must still be answerable if the game fails.
3. Write `live/games/<question id>.html`. Nothing else is needed; the page finds it by id. Rewriting the file reloads the game.

**Read `games/examples/tricoloring.html` before writing your first game in a session.** It's a complete working example: copy its structure. Its knot engine builds a diagram (crossings, arcs, over/under) from any closed parametric space curve, so reuse it for any knot-diagram game.

## The file

The file is an HTML **fragment**: a `<style>`, the markup, and a `<script>`. No `<html>`, `<head>` or `<body>`; the server wraps it in a page that provides:

- **CSS variables** that follow light/dark mode: `--ink`, `--muted`, `--line`, `--accent`, `--good`, `--bad`, `--surface`. Use them (or `Game.colors`) for every color, never fixed black or white. The background is transparent.
- **Base styles** for `button` (`.active` for a selected one), `svg`, `.row` (a flex row) and `.status` (with `.good` / `.bad`).
- **`Game`**, a small helper object:
  - `Game.solved(detail)`: call when the student reaches the goal. `detail` is a short phrase saying what they did ("found a tricoloring of the trefoil"). Only the first call is sent, as `{"game_solved": {"id", "detail"}}`.
  - `Game.colors`: six distinct colors that read well in both modes.
  - `Game.svg(tag, attrs, parent)` and `Game.el(tag, attrs, text, parent)` create SVG and HTML elements.

Rules:

- Plain JavaScript, inline. No libraries, imports, fonts, images or requests: the frame's Content-Security-Policy blocks them all.
- The frame is sandboxed: no `alert`/`confirm`/`prompt`, no `localStorage` or cookies (they throw), no popups. Show messages in the page itself.
- The column is about 360–460 px wide. Draw in SVG with a fixed `viewBox` and `width: 100%`, so it scales. Keep the game under about 500 px tall; the frame resizes to fit its content.
- Under about 250 lines. One idea, one goal, with clear win and fail states shown in a status line. A one-line instruction above the board is fine. Don't explain the theory behind the game; that's for feedback.
- Clicking is the main input. Make click targets generous (e.g. a wide invisible stroke over thin lines).
- No randomness unless the game needs it, and then make every round solvable.

## Messages

- `{"game_solved": {"id", "detail"}}`: the student reached the goal. Nothing to post; take it into account when you grade that question, and note it in the subject's notes if it tells you something.
- `{"game_error": {"id", "error"}}`: the game threw an error in the student's browser (with a line number in your file when there is one). Fix the same file once. If the fixed version fails too, it's dropped and the page hides it; move on, and don't mention failures on the page.
