# Explainer animations

You can attach a short Manim animation to a question. The server renders it in the background and the page shows it under that question, so it never slows down grading.

## When

- Mainly after a `"none"` or `"partial"` grade, to show the idea behind the correct answer. Occasionally, on the first question of a thread's new subject, to teach before asking.
- Only when a picture really helps: geometry, vectors, waves, circuits, orbits and tides, graphs and trees, sorting or memory layout, probabilities as areas. Not for definitions or vocabulary.
- At most about one explainer per thread every 4 questions.
- Always grade and add the thread's next question **first**. Write the explainer last.

## How

Write `live/explainers/<question id>.py`, where the id is the question the explainer belongs to (usually the one you just graded). Nothing else is needed; the page finds it by id.

```python
from manim import *

class Explainer(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        title = Text("Kepler III: T² ∝ a³", color=BLACK, font_size=36).to_edge(UP)
        ...
```

- Exactly one class, named `Explainer`, subclassing `Scene`. Import only from `manim` (and `math`, if needed).
- 10–20 seconds total. One idea, the same one the feedback states. No narration; at most a few short `Text` captions.
- Put the title on screen in the very first frame (`self.add(title)`, not `Write`), so the video isn't a blank white box before it plays.
- White background, dark text and strokes (`BLACK`, `BLUE`, `RED`, `GREEN`, `ORANGE`).
- The frame is about 14 × 8 units, centered at the origin. Keep everything inside it; use `font_size` 24–40.
- **No LaTeX is installed.** Never use `MathTex`, `Tex`, `DecimalNumber`, `Integer`, `Variable`, `add_coordinates`, or number labels on `NumberLine`/`Axes` (`include_numbers`). Write math as `Text` with Unicode (x², √, π, ∑, →, ≤).
- No file, network or random access. The sandbox blocks them anyway, and the render must be deterministic.

## Errors

If a render fails, the server sends `{"render_error": {"id", "log"}}` with the end of the Manim output. Fix the same file once (rewriting it triggers a new render). If it fails a second time it's dropped; move on. Don't mention failures on the page.
