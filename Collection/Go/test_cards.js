// Usage: node test_cards.js media/_go.js Tsumego.tsv  (after python3 build.py)
// Drive _go.js against every note: random computer choices, random accepted answers.
const fs = require('fs');
const tsv = fs.readFileSync(process.argv[3], 'utf8').trim().split('\n').map(l => l.split('\t'));
const hdr = tsv[0];
let queue = [];
global.setTimeout = (f) => { queue.push(f); };
const flush = () => { let n = 0; while (queue.length) { queue.shift()(); if (++n > 10000) throw new Error('loop'); } };
function makeDom(f) {
  const els = {};
  const ctx = new Proxy({}, { get: (t, k) => (k in t ? t[k] : () => {}), set: (t, k, v) => { t[k] = v; return true; } });
  const mk = (extra) => Object.assign({ textContent: '', style: {}, children: [], appendChild(c) { this.children.push(c); },
                                        set innerHTML(v) { this.children = []; }, addEventListener() {} }, extra);
  for (const [id, key] of [['go-board', 'Board'], ['go-edges', 'Edges'], ['go-tomove', 'ToMove'], ['go-player', 'Player'],
                           ['go-prompt', 'Prompt'], ['go-solution', 'Solution']]) els[id] = mk({ textContent: f[key] });
  els['go-canvas'] = mk({ getContext: () => ctx, getBoundingClientRect: () => ({ left: 0, top: 0, width: 1, height: 1 }) });
  els['go-text'] = mk(); els['go-controls'] = mk();
  global.document = { getElementById: id => els[id], body: { style: {} },
                      createElement: () => mk({ addEventListener() {} }) };
  return els;
}
global.window = {};
eval(fs.readFileSync(process.argv[2], 'utf8'));
const GoCard = window.GoCard;
let bad = 0, runs = 0;
for (const row of tsv.slice(1)) {
  const f = Object.fromEntries(hdr.map((h, i) => [h, row[i]]));
  try {
    makeDom(f); GoCard.init('status'); flush();
    makeDom(f); GoCard.init('back'); flush();
    const seenEnds = new Set();
    for (let r = 0; r < 60; r++) {
      const els = makeDom(f);
      const api = GoCard.init('play'); flush();
      let steps = 0;
      while (!api.free()) {
        const kids = api.node().kids;
        if (!kids.length) throw new Error('stuck: no moves but not finished');
        if (r === 0) {
          const b = api.board(), want = new Set(kids.map(k => k.move));
          let wrong = null;
          for (let y = 0; y < b.length && !wrong; y++) for (let x = 0; x < b[0].length; x++) {
            const m = String.fromCharCode(97 + x) + String.fromCharCode(97 + y);
            if (b[y][x] === '.' && !want.has(m)) { wrong = m; break; }
          }
          if (wrong) { const before = api.node(); api.answer(wrong); flush();
            if (api.node() !== before || !/Not the move/.test(els['go-text'].textContent)) throw new Error('wrong move accepted: ' + wrong); }
        }
        const k = kids[Math.floor(Math.random() * kids.length)];
        api.answer(k.move); flush();
        if (++steps > 50) throw new Error('too long');
      }
      seenEnds.add(els['go-text'].textContent);
      runs++;
    }
    if (!seenEnds.size || [...seenEnds].some(t => !/Well done/.test(t))) throw new Error('bad end text ' + [...seenEnds]);
  } catch (e) { bad++; console.log('FAIL', f.Title, '-', e.message); }
}
console.log(`${tsv.length - 1} notes, ${runs} play-throughs, ${bad} failing`);
