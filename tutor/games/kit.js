// Injected into every minigame frame before the tutor's code (see games/frame.html).
// Reports errors, completion and the frame's height to the worksheet page, and offers a
// few small helpers as `Game`.
(() => {
  const post = msg => parent.postMessage(Object.assign({ game: true }, msg), "*");

  let errors = 0;
  const reportError = (message, line) => {
    if (errors++ >= 3) return;   // the first few are enough to fix the game
    post({ type: "error", error: String(message).slice(0, 500) + (line ? ` (line ${line})` : "") });
  };
  addEventListener("error", e => reportError(e.message || "error", e.lineno));
  addEventListener("unhandledrejection", e => reportError(`unhandled rejection: ${e.reason}`));

  // The page sizes the frame to its content.
  const sendHeight = () => post({ type: "height", height: Math.ceil(document.documentElement.scrollHeight) });
  addEventListener("load", () => {
    sendHeight();
    new ResizeObserver(sendHeight).observe(document.body);
  });

  const SVG_NS = "http://www.w3.org/2000/svg";
  let solvedSent = false;

  window.Game = {
    // Call when the student completes the goal; detail says briefly what they did.
    // Only the first call per load is sent.
    solved(detail = "") {
      if (solvedSent) return;
      solvedSent = true;
      post({ type: "solved", detail: String(detail).slice(0, 300) });
    },

    // Distinct colors that read well in light and dark mode.
    colors: ["#e0533d", "#3a7bd5", "#2ea365", "#d99a1e", "#9b59b6", "#16a2b8"],

    // Game.svg("circle", {cx: 5, cy: 5, r: 3}, parent) creates an SVG element.
    svg(tag, attrs = {}, parent = null) {
      const el = document.createElementNS(SVG_NS, tag);
      for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
      if (parent) parent.appendChild(el);
      return el;
    },

    // Game.el("button", {class: "btn"}, "Reset", parent) creates an HTML element.
    el(tag, attrs = {}, text = "", parent = null) {
      const el = document.createElement(tag);
      for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
      if (text) el.textContent = text;
      if (parent) parent.appendChild(el);
      return el;
    },
  };
})();
