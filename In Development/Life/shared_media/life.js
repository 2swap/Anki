/* life.js -- renders a small local slice of tree_of_life.json around one clade,
   for the "Life - Clade" note type.

   lifeRenderLocal(canvasId, clade, mode, reveal)
     mode "clade"    : show parent > (siblings incl. target) > children;
                       the target is blanked to "?" until reveal.
     mode "children"  : show parent > target > children; children blanked until reveal.
     mode "parent"    : show parent > target > children; parent blanked until reveal.
     mode "context"   : show parent > siblings > children; nothing blanked.

   The <canvas> carries data-src="tree_of_life.json" so Anki keeps the media file.
*/
(function (global) {
  var cache = null;
  var MAX_ROWS = 10;

  function loadTree(src) {
    if (cache) return Promise.resolve(cache);
    return fetch(src)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (d) { cache = d; return d; });
  }

  function childrenOf(tree, name) {
    var out = [];
    for (var k in tree) {
      if (Object.prototype.hasOwnProperty.call(tree, k) && tree[k] && tree[k].parent === name) {
        out.push(k);
      }
    }
    out.sort();
    return out;
  }

  function truncate(list, mustKeep) {
    if (list.length <= MAX_ROWS) return { items: list.slice(), more: 0 };
    var items = list.slice(0, MAX_ROWS - 1);
    if (mustKeep && items.indexOf(mustKeep) === -1) items[items.length - 1] = mustKeep;
    return { items: items, more: list.length - items.length };
  }

  function sizeCanvas(canvas, cssW, cssH) {
    var dpr = global.devicePixelRatio || 1;
    canvas.style.width = cssW + "px";
    canvas.style.height = cssH + "px";
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    var ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return ctx;
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function draw(canvas, tree, clade, mode, reveal) {
    var known = Object.prototype.hasOwnProperty.call(tree, clade);
    var parent = known ? tree[clade].parent : null;
    var allSiblings = parent ? childrenOf(tree, parent) : [clade];
    if (allSiblings.indexOf(clade) === -1) allSiblings = [clade].concat(allSiblings);
    var children = known ? childrenOf(tree, clade) : [];

    var wide = (mode === "clade" || mode === "context");
    var siblings = wide ? allSiblings : [clade];

    var cols = [];
    if (parent) cols.push({ key: "par", items: [parent], more: 0 });
    var sibT = truncate(siblings, clade);
    cols.push({ key: "sib", items: sibT.items, more: sibT.more });
    if (children.length) {
      var chT = truncate(children, null);
      cols.push({ key: "chd", items: chT.items, more: chT.more });
    }

    var parentW = canvas.parentNode ? canvas.parentNode.clientWidth : 600;
    var cssW = Math.max(320, Math.min(640, parentW - 4));
    var rowH = 36;
    var maxItems = 1;
    cols.forEach(function (c) { maxItems = Math.max(maxItems, c.items.length + (c.more ? 1 : 0)); });
    var cssH = Math.max(150, maxItems * rowH + 40);
    var ctx = sizeCanvas(canvas, cssW, cssH);
    ctx.clearRect(0, 0, cssW, cssH);

    var colX = cols.map(function (_, i) {
      return cols.length === 1 ? cssW / 2 : 70 + i * ((cssW - 140) / (cols.length - 1));
    });

    var pos = {};
    var layout = [];
    cols.forEach(function (col, ci) {
      var n = col.items.length + (col.more ? 1 : 0);
      var startY = (cssH - (n - 1) * rowH) / 2;
      col.items.forEach(function (name, ri) {
        var p = { x: colX[ci], y: startY + ri * rowH, name: name, key: col.key };
        layout.push(p);
        if (!(name in pos)) pos[name] = p;
      });
      if (col.more) {
        layout.push({ x: colX[ci], y: startY + col.items.length * rowH, name: "+" + col.more + " more", ghost: true });
      }
    });

    ctx.strokeStyle = "rgba(150,150,150,0.45)";
    ctx.lineWidth = 1;
    function edge(a, b) {
      if (!pos[a] || !pos[b]) return;
      ctx.beginPath();
      ctx.moveTo(pos[a].x, pos[a].y);
      ctx.lineTo(pos[b].x, pos[b].y);
      ctx.stroke();
    }
    if (parent) siblings.forEach(function (s) { edge(parent, s); });
    children.forEach(function (c) { edge(clade, c); });

    function hidden(p) {
      if (reveal) return false;
      if (mode === "clade") return p.key === "sib" && p.name === clade;
      if (mode === "children") return p.key === "chd";
      if (mode === "parent") return p.key === "par";
      return false;
    }

    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    layout.forEach(function (p) {
      var isTarget = p.key === "sib" && p.name === clade;
      var blank = hidden(p);
      var label = blank ? "?" : p.name;

      if (p.ghost) {
        ctx.fillStyle = "#777";
        ctx.font = "12px Arial";
        ctx.fillText(label, p.x, p.y);
        return;
      }

      ctx.font = "14px Arial";
      var w = ctx.measureText(label).width + 22;
      var h = 26;
      roundRect(ctx, p.x - w / 2, p.y - h / 2, w, h, 6);
      var emphasize = isTarget || blank;
      if (emphasize) {
        ctx.fillStyle = blank ? "#37474f" : "#2e7d32";
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#8ab4f8";
        ctx.stroke();
        ctx.fillStyle = blank ? "#8ab4f8" : "#ffffff";
      } else {
        ctx.fillStyle = "#1b1b1b";
        ctx.fill();
        ctx.lineWidth = 1;
        ctx.strokeStyle = "#444";
        ctx.stroke();
        ctx.fillStyle = "#e0e0e0";
      }
      ctx.fillText(label, p.x, p.y);
    });

    if (!known) {
      ctx.fillStyle = "#cc6666";
      ctx.font = "13px Arial";
      ctx.textAlign = "left";
      ctx.fillText('"' + clade + '" not found in tree_of_life.json', 10, cssH - 12);
    }
  }

  global.lifeRenderLocal = function (canvasId, clade, mode, reveal) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    var src = canvas.getAttribute("data-src") || "tree_of_life.json";
    loadTree(src)
      .then(function (tree) { draw(canvas, tree, clade, mode || "clade", !!reveal); })
      .catch(function (e) {
        var ctx = canvas.getContext("2d");
        ctx.fillStyle = "#cc6666";
        ctx.font = "14px Arial";
        ctx.fillText("tree_of_life.json failed to load: " + e.message, 10, 24);
      });
  };
})(window);
