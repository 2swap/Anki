/* Go life-and-death cards: board, rules, solution trees, free play.
 *
 * Used by both card types of the "Go Tsumego" note type. Each template holds the
 * note's fields in <script type="text/plain"> blocks and calls GoCard.init(mode):
 *   "status" - static board, asks for the status
 *   "play"   - the person plays the lines from the Solution tree; afterwards free play
 *   "back"   - the main line with move numbers, then free play (Undo / Reset)
 *
 * Solution grammar (moves are two letters within the crop, "aa" = top-left; ".." = pass):
 *   seq  := item*
 *   item := move ['{' comment '}'] | '(' seq ('|' seq)+ ')'
 * Moves alternate from ToMove. Where the player is to move, the alternatives are all
 * accepted answers; where the computer is, it picks one at random. A comment marks a
 * place where a line may end, and is shown when it does.
 */
window.GoCard = (function () {
    'use strict';

    function parseTree(s) {
        var i = 0;
        function seq(node) {
            while (i < s.length) {
                var c = s[i];
                if (c === '(') {
                    i++;
                    seq(node);
                    while (s[i] === '|') { i++; seq(node); }
                    i++; // ')'
                    return;
                }
                if (c === ')' || c === '|') return;
                var child = { kids: [], end: null };
                var move = s.substr(i, 2);
                i += 2;
                if (s[i] === '{') {
                    var j = s.indexOf('}', i);
                    child.end = s.slice(i + 1, j);
                    i = j + 1;
                }
                node.kids.push({ move: move, node: child });
                node = child;
            }
        }
        var root = { kids: [], end: null };
        seq(root);
        return root;
    }

    function field(id) {
        var el = document.getElementById(id);
        return el ? el.textContent.replace(/^\s+|\s+$/g, '') : '';
    }

    function init(mode) {
        var rows = field('go-board').replace(/\s+/g, '').split(',');
        var edges = field('go-edges').toUpperCase();
        var toMove = field('go-tomove').toUpperCase() === 'W' ? 'O' : 'X';
        var player = field('go-player').toUpperCase() === 'W' ? 'O' : 'X';
        var prompt = field('go-prompt');
        var tree = parseTree(field('go-solution').replace(/\s+(?![^{]*})/g, ''));
        var H = rows.length, W = rows[0].length;
        var opp = function (c) { return c === 'X' ? 'O' : 'X'; };
        var colourName = function (c) { return c === 'X' ? 'Black' : 'White'; };

        var canvas = document.getElementById('go-canvas');
        var text = document.getElementById('go-text');
        var controls = document.getElementById('go-controls');
        var ctx = canvas.getContext('2d');
        var S = 44, PAD = 26;
        canvas.width = (W - 1) * S + 2 * PAD;
        canvas.height = (H - 1) * S + 2 * PAD;

        // ---------------- position ----------------
        var board, numbers, ko, turn, moveNo, history, last;
        function reset() {
            board = rows.map(function (r) { return r.split(''); });
            numbers = rows.map(function (r) { return r.split('').map(function () { return 0; }); });
            ko = null; turn = toMove; moveNo = 1; history = []; last = null;
        }
        function snapshot() {
            return { board: board.map(function (r) { return r.slice(); }), numbers: numbers.map(function (r) { return r.slice(); }),
                     ko: ko, turn: turn, moveNo: moveNo, last: last };
        }
        function restore(s) { board = s.board; numbers = s.numbers; ko = s.ko; turn = s.turn; moveNo = s.moveNo; last = s.last; }

        var inside = function (x, y) { return x >= 0 && y >= 0 && x < W && y < H; };
        var openOutside = function (x, y) {
            return (x < 0 && edges.indexOf('L') < 0) || (x >= W && edges.indexOf('R') < 0) ||
                   (y < 0 && edges.indexOf('T') < 0) || (y >= H && edges.indexOf('B') < 0);
        };
        var nbrs = function (x, y) { return [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]; };
        function groupOf(x, y) {
            var c = board[y][x], seen = {}, stack = [[x, y]], stones = [], libs = 0;
            seen[x + ',' + y] = 1;
            while (stack.length) {
                var p = stack.pop();
                stones.push(p);
                nbrs(p[0], p[1]).forEach(function (q) {
                    if (!inside(q[0], q[1])) { if (openOutside(q[0], q[1])) libs++; return; }
                    var v = board[q[1]][q[0]], k = q[0] + ',' + q[1];
                    if (v === '.') libs++;
                    else if (v === c && !seen[k]) { seen[k] = 1; stack.push(q); }
                });
            }
            return { stones: stones, libs: libs };
        }
        // Play `c` at (x, y) (or pass when x is null). Returns false if illegal.
        function play(x, y, c, checkKo) {
            if (x === null) {
                history.push(snapshot());
                ko = null; turn = opp(c); last = null;
                return true;
            }
            if (!inside(x, y) || board[y][x] !== '.') return false;
            if (checkKo && ko && ko[0] === x && ko[1] === y) return false;
            var before = snapshot();
            board[y][x] = c;
            var caps = [];
            nbrs(x, y).forEach(function (q) {
                if (inside(q[0], q[1]) && board[q[1]][q[0]] === opp(c)) {
                    var g = groupOf(q[0], q[1]);
                    if (g.libs === 0) g.stones.forEach(function (s) { caps.push(s); board[s[1]][s[0]] = '.'; numbers[s[1]][s[0]] = 0; });
                }
            });
            var mine = groupOf(x, y);
            if (!caps.length && mine.libs === 0) { restore(before); return false; }
            ko = (caps.length === 1 && mine.stones.length === 1 && mine.libs === 1) ? caps[0] : null;
            numbers[y][x] = moveNo++;
            turn = opp(c);
            last = [x, y];
            history.push(before);
            return true;
        }
        var toXY = function (m) { return m === '..' ? [null, null] : [m.charCodeAt(0) - 97, m.charCodeAt(1) - 97]; };

        // ---------------- drawing ----------------
        var px = function (i) { return PAD + i * S; };
        var hover = null, showNumbers = true;
        function render() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#dcb35c';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = '#000';
            for (var x = 0; x < W; x++) {
                ctx.lineWidth = (x === 0 && edges.indexOf('L') >= 0) || (x === W - 1 && edges.indexOf('R') >= 0) ? 2 : 1;
                ctx.beginPath();
                ctx.moveTo(px(x), edges.indexOf('T') >= 0 ? px(0) : 0);
                ctx.lineTo(px(x), edges.indexOf('B') >= 0 ? px(H - 1) : canvas.height);
                ctx.stroke();
            }
            for (var y = 0; y < H; y++) {
                ctx.lineWidth = (y === 0 && edges.indexOf('T') >= 0) || (y === H - 1 && edges.indexOf('B') >= 0) ? 2 : 1;
                ctx.beginPath();
                ctx.moveTo(edges.indexOf('L') >= 0 ? px(0) : 0, px(y));
                ctx.lineTo(edges.indexOf('R') >= 0 ? px(W - 1) : canvas.width, px(y));
                ctx.stroke();
            }
            function stone(x, y, c, alpha) {
                ctx.globalAlpha = alpha;
                ctx.beginPath();
                ctx.arc(px(x), px(y), S / 2 - 1.5, 0, 2 * Math.PI);
                ctx.fillStyle = c === 'X' ? '#111' : '#f4f4f4';
                ctx.fill();
                ctx.lineWidth = 1;
                ctx.strokeStyle = '#000';
                ctx.stroke();
                ctx.globalAlpha = 1;
            }
            for (y = 0; y < H; y++) for (x = 0; x < W; x++) {
                var c = board[y][x];
                if (c === '.') continue;
                stone(x, y, c, 1);
                if (showNumbers && numbers[y][x]) {
                    ctx.fillStyle = c === 'X' ? '#fff' : '#000';
                    ctx.font = 'bold ' + (numbers[y][x] > 9 ? 17 : 20) + 'px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(numbers[y][x], px(x), px(y) + 1);
                } else if (last && last[0] === x && last[1] === y) {
                    ctx.beginPath();
                    ctx.arc(px(x), px(y), S / 6, 0, 2 * Math.PI);
                    ctx.strokeStyle = c === 'X' ? '#fff' : '#000';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }
            }
            if (hover && board[hover[1]][hover[0]] === '.') stone(hover[0], hover[1], turn, 0.4);
        }
        function flash(colour) {
            var el = document.body, prev = el.style.backgroundColor || '';
            el.style.transition = 'background-color 100ms';
            el.style.backgroundColor = colour;
            setTimeout(function () { el.style.backgroundColor = prev; }, 300);
        }
        function say(s) { if (text) text.textContent = s; }
        function pointFromEvent(e) {
            var rect = canvas.getBoundingClientRect();
            var x = Math.round(((e.clientX - rect.left) * canvas.width / rect.width - PAD) / S);
            var y = Math.round(((e.clientY - rect.top) * canvas.height / rect.height - PAD) / S);
            return inside(x, y) ? [x, y] : null;
        }

        // ---------------- controls ----------------
        var free = false, busy = false, node = tree, resetTo = null;
        function button(label, fn, cls) {
            var b = document.createElement('button');
            b.type = 'button';
            b.textContent = label;
            if (cls) b.className = cls;
            b.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); fn(); });
            controls.appendChild(b);
            return b;
        }
        var passBtn = null;
        function startFree(message) {
            free = true;
            controls.innerHTML = '';
            passBtn = button('Pass', function () { play(null, null, turn); say(colourName(opp(turn)) + ' passed. ' + colourName(turn) + ' to play.'); render(); });
            button('Undo', function () { if (history.length > (resetTo ? resetTo.depth : 0)) { restore(history.pop()); render(); say(colourName(turn) + ' to play.'); } });
            button('Reset', function () { if (resetTo) { restore(resetTo.state); history = resetTo.history.slice(); } render(); say(colourName(turn) + ' to play.'); });
            button('Numbers', function () { showNumbers = !showNumbers; render(); });
            var st = snapshot();
            resetTo = { state: st, history: history.slice(), depth: 0 };
            if (message !== undefined) say(message);
        }

        canvas.addEventListener('mousemove', function (e) {
            hover = (busy || mode === 'status' || (!free && !node.kids.length)) ? null : pointFromEvent(e);
            render();
        });
        canvas.addEventListener('mouseout', function () { hover = null; render(); });

        // ---------------- modes ----------------
        reset();
        if (mode === 'status') {
            say(colourName(toMove) + ' to play. What is the status?');
            render();
            return;
        }

        if (mode === 'back') {
            var n = tree;
            while (n.kids.length) {
                var k = n.kids[0], m = toXY(k.move);
                play(m[0], m[1], turn, false);
                n = k.node;
            }
            startFree(n.end ? 'Main line: ' + n.end + ' You can keep playing.' : 'Main line shown. You can keep playing.');
            resetTo.depth = 0;
            canvas.addEventListener('click', freeClick);
            render();
            return;
        }

        // mode === 'play'
        say(prompt || (colourName(player) + ' to play'));
        function finish(n) {
            flash('rgba(127,255,127,0.25)');
            startFree((n.end ? n.end + ' ' : '') + 'Well done! You can keep playing.');
            render();
        }
        // Advance through computer moves until it is the player's turn or the line ends.
        function computer() {
            if (turn === player) {
                if (!node.kids.length || node.end) { finish(node); return; }
                busy = false;
                passBtn && (passBtn.style.display = node.kids.some(function (k) { return k.move === '..'; }) ? '' : 'none');
                render();
                return;
            }
            var options = node.kids.slice();
            if (!options.length) { finish(node); return; }
            var stop = node.end && node !== tree;
            var pick = Math.floor(Math.random() * (options.length + (stop ? 1 : 0)));
            if (pick === options.length) { finish(node); return; }
            busy = true;
            setTimeout(function () {
                var k = options[pick], m = toXY(k.move);
                if (!play(m[0], m[1], turn, false)) throw new Error('illegal computer move ' + k.move);
                if (k.move === '..') say(colourName(opp(turn)) + ' plays elsewhere.');
                node = k.node;
                render();
                computer();
            }, 400);
        }
        function answer(move) {
            var k = node.kids.filter(function (a) { return a.move === move; })[0];
            if (!k) {
                flash('rgba(255,127,127,0.25)');
                say('Not the move from Sensei’s Library. Try again.');
                return;
            }
            var m = toXY(move);
            if (!play(m[0], m[1], turn, false)) throw new Error('illegal tree move ' + move);
            node = k.node;
            say('');
            render();
            computer();
        }
        function freeClick(e) {
            if (!free) return;
            var p = pointFromEvent(e);
            if (!p) return;
            if (play(p[0], p[1], turn, true)) { say(colourName(turn) + ' to play.'); hover = null; render(); }
        }
        canvas.addEventListener('click', function (e) {
            if (free) { freeClick(e); return; }
            if (busy) return;
            var p = pointFromEvent(e);
            if (!p || board[p[1]][p[0]] !== '.') return;
            answer(String.fromCharCode(97 + p[0]) + String.fromCharCode(97 + p[1]));
        });
        passBtn = button('Pass', function () { if (!free && !busy) answer('..'); });
        passBtn.style.display = 'none';
        render();
        busy = true;
        setTimeout(computer, 300);
        // for tests
        return { answer: answer, node: function () { return node; }, free: function () { return free; },
                 busy: function () { return busy; }, turn: function () { return turn; }, board: function () { return board; } };
    }

    return { init: init, parseTree: parseTree };
})();
