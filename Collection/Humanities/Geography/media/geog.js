// Dynamically inject a script; resolves when it has loaded.
var injectScript = (src) => new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.async = true;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
});

(async () => {
    // Anki desktop keeps one page for the whole review session and only swaps
    // the card HTML, so every earlier card's document listeners (and its
    // detached <audio>) are still alive. Abort the previous card before
    // starting this one; every listener below is registered with `sig`.
    if (window.__geogAbort) window.__geogAbort.abort();
    const abort = new AbortController();
    window.__geogAbort = abort;
    const sig = abort.signal;

    // ---------------------------------------------------------------- setup
    // This note type has a single card template ("Name the Feature"): a flat
    // map (Web Mercator, repeating left and right) is framed on the target
    // feature (no label), you recall its name, and the back reveals the name +
    // plays its audio. Everything - basemap, outlines, dots, labels - is drawn
    // with plain 2D canvas calls on the card's one canvas.
    const textElement = document.getElementById("txt");
    const backElement = document.getElementById("back");
    const onBack = !!backElement;
    if (onBack) backElement.remove();

    const cardData = document.getElementById("card_data").innerHTML;
    const nameField = cardData.startsWith("(") ? "Bekasi::Indonesia_Kabupaten" : cardData;
    const splitName = nameField.split("::");
    const featureName = splitName[0];
    const countryName = splitName[1];
    // Each country's data is loaded once per page: Anki desktop keeps the page
    // across cards, so later cards (and the flip to the back) reuse it.
    window.__geogData = window.__geogData || {};
    try {
        if (!window.__geogData[countryName]) {
            window.countryjson = { type: "FeatureCollection", features: [] };
            // AnkiConnect's storeMediaFile lowercases every media filename, so the
            // data files land as geog_<lowercase>.js even though the folder/suffix
            // (and the GitHub audio path below) keep their original case.
            await injectScript('geog_' + countryName.toLowerCase() + '.js');
            window.__geogData[countryName] = window.countryjson;
        }
    } catch (e) {
        if (textElement) textElement.textContent = "Geography card: failed to load resources.";
        return;
    }
    // A newer card (or this card's back) started while we were loading: it
    // owns the page now, so this instance must not draw anything.
    if (sig.aborted) return;

    const features = window.__geogData[countryName].features || [];
    // A region sharing its name with a city in the same file has " [region]"
    // appended to its note name (see make_tsv.py); otherwise prefer the city.
    const REGION_MARK = " [region]";
    const wantRegion = featureName.endsWith(REGION_MARK);
    const bareName = wantRegion ? featureName.slice(0, -REGION_MARK.length) : featureName;
    let feature = null;
    for (const f of features) {
        if (f.properties.name !== bareName && f.properties.name_en !== bareName) continue;
        const isPoint = f.geometry.type === "Point";
        if (wantRegion ? isPoint : (feature && !isPoint)) continue;
        if (!feature || (!wantRegion && isPoint && feature.geometry.type !== "Point")) feature = f;
    }
    if (!feature && textElement) {
        // Should not happen (the TSV is generated from these same names), but if
        // the target is missing don't leave a silently mis-centred map.
        textElement.textContent = featureName + (onBack ? "" : " — not found in data");
    }

    // ---------------------------------------------------------------- audio
    // Streamed straight from GitHub, not Anki media. Played once when the back
    // appears; a later click/tap only retries if the webview blocked that
    // autoplay (it never restarts audio that already played).
    const audioElement = document.getElementById("audio");
    let audioStarted = false;
    audioElement.addEventListener("playing", () => { audioStarted = true; }, { signal: sig });
    sig.addEventListener("abort", () => { audioElement.pause(); });
    function playFeatureAudio() {
        if (!feature || !onBack || audioStarted) return; // front must not give the name away
        // Local Anki media, named by make_tsv.py's audio_media_name(): the data
        // file suffix + the place's name with file-unsafe characters replaced,
        // lowercased like Anki stores it.
        const file = ("geogaudio_" + countryName + "_"
            + feature.properties.name.replace(/[\\/:*?"<>|]/g, "_") + ".mp3").toLowerCase().normalize("NFC");
        const src = encodeURIComponent(file);
        if (audioElement.getAttribute("src") !== src) audioElement.src = src;
        const p = audioElement.play();
        if (p && p.catch) p.catch(() => {}); // blocked or missing mp3: retried on the next gesture
    }
    playFeatureAudio();

    // ------------------------------------------------------------- the canvas
    const canvas = document.getElementById("canvas");
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    canvas.style.touchAction = "none";
    canvas.style.background = "#05070d";
    const ctx = canvas.getContext("2d");
    const DPR = Math.min(2, window.devicePixelRatio || 1);

    // ----------------------------------------------------------- projection
    // Web Mercator in degrees: x = longitude, y = mercator(latitude) scaled so
    // that, like x, it spans -180..180 (the map is cut at ±85.05° latitude).
    // The view is a centre (lon0, y0) and a zoom k in screen px per degree of
    // longitude; the world repeats every 360° left and right.
    const D2R = Math.PI / 180;
    const MAX_LAT = 85.0511;
    function mercY(lat) {
        lat = Math.max(-MAX_LAT, Math.min(MAX_LAT, lat));
        return Math.log(Math.tan(Math.PI / 4 + lat * D2R / 2)) / D2R;
    }
    function invMercY(y) { return (2 * Math.atan(Math.exp(y * D2R)) - Math.PI / 2) / D2R; }

    let W = 0, H = 0;               // canvas size in CSS px
    // Screen-size scaling, from the canvas's short side m (CSS px). Sizes below
    // were tuned at two ends: labels on a 4K desktop at 1x (m ~ 2000), dots on
    // a phone (m ~ 420). Labels scale with sqrt(m), dots with m^0.6 (a desk
    // screen is viewed from further away): labels shrink from desktop
    // size on smaller screens, dots grow from phone size on bigger ones.
    let labelScale = 1, dotScale = 1;
    function updateScales() {
        const m = Math.max(1, Math.min(W, H));
        labelScale = Math.max(0.4, Math.min(1, Math.sqrt(m / 2000)));
        dotScale = Math.max(1, Math.min(3, Math.pow(m / 420, 0.6)));
    }
    let lon0 = 0, y0 = 0, k = 4;    // view centre + zoom
    const K_MAX = 100000; // about 1 km across the screen; the imagery is blurry long before that
    function kMin() { return Math.max(H, 1) / 360; } // whole world's height fits
    function sx(x) { return W / 2 + (x - lon0) * k; }
    function sy(y) { return H / 2 - (y - y0) * k; }
    function clampView() {
        k = Math.max(kMin(), Math.min(K_MAX, k));
        const half = H / 2 / k;     // keep the map filling the canvas vertically
        y0 = Math.max(-180 + half, Math.min(180 - half, y0));
        lon0 = ((lon0 + 180) % 360 + 360) % 360 - 180;
    }
    // Which 360° copies (m) of something spanning longitudes a..b are in view.
    function copies(a, b) {
        const L = lon0 - W / 2 / k, R = lon0 + W / 2 / k;
        const out = [];
        for (let m = Math.ceil((L - b) / 360); m <= Math.floor((R - a) / 360); m++) out.push(m);
        return out;
    }
    function yVisible(yTop, yBottom) { // mercator y, yTop > yBottom
        return sy(yTop) < H && sy(yBottom) > 0;
    }

    // ------------------------------------------------------------ features
    function ringsOf(g) {
        if (g.type === "MultiPolygon") return g.coordinates.map((p) => p[0]);
        if (g.type === "Polygon") return [g.coordinates[0]];
        if (g.type === "LineString") return [g.coordinates];
        return [];
    }

    // Per feature, computed once: each ring as flat [x, y, x, y, ...] in map
    // degrees, with longitudes unwrapped so a ring crossing the antimeridian
    // stays continuous (e.g. 179 -> 181, not 179 -> -179); its bounding box;
    // and the label anchor.
    const geo = new Map();
    function geoOf(f) {
        let g = geo.get(f);
        if (g) return g;
        g = { rings: [], x0: Infinity, x1: -Infinity, y0: Infinity, y1: -Infinity };
        if (f.geometry.type === "Point") {
            const c = f.geometry.coordinates;
            g.ax = c[0]; g.ay = mercY(c[1]);
            g.x0 = g.x1 = g.ax; g.y0 = g.y1 = g.ay;
        } else {
            let sx_ = 0, sy_ = 0, n = 0, ref = null;
            for (const ring of ringsOf(f.geometry)) {
                const a = new Float64Array(ring.length * 2);
                // Pieces of a region split at the antimeridian (e.g. Chukotka at
                // ±180°) are shifted by 360° to sit next to the first piece.
                let prev = ref === null ? null : ring[0][0] + 360 * Math.round((ref - ring[0][0]) / 360);
                for (let i = 0; i < ring.length; i++) {
                    let lon = ring[i][0];
                    if (prev !== null) lon += 360 * Math.round((prev - lon) / 360);
                    if (ref === null) ref = lon;
                    prev = lon;
                    const y = mercY(ring[i][1]);
                    a[2 * i] = lon; a[2 * i + 1] = y;
                    g.x0 = Math.min(g.x0, lon); g.x1 = Math.max(g.x1, lon);
                    g.y0 = Math.min(g.y0, y); g.y1 = Math.max(g.y1, y);
                    sx_ += lon; sy_ += y; n++;
                }
                g.rings.push(a);
            }
            g.ax = n ? sx_ / n : 0; g.ay = n ? sy_ / n : 0;
        }
        geo.set(f, g);
        return g;
    }
    function boxVisible(g, m) {
        return sx(g.x1 + 360 * m) > -2 && sx(g.x0 + 360 * m) < W + 2 && yVisible(g.y1, g.y0);
    }

    // Add one ring (shifted by m copies) to the current path; points under a
    // pixel from the last one drawn are skipped.
    function traceRing(a, m, close) {
        const n = a.length / 2, off = 360 * m;
        let lx = 0, ly = 0;
        for (let i = 0; i < n; i++) {
            const x = sx(a[2 * i] + off), y = sy(a[2 * i + 1]);
            if (i === 0) ctx.moveTo(x, y);
            else if (i === n - 1 || Math.abs(x - lx) + Math.abs(y - ly) >= 1) ctx.lineTo(x, y);
            else continue;
            lx = x; ly = y;
        }
        if (close) ctx.closePath();
    }
    function traceFeature(f, close) {
        const g = geoOf(f);
        for (const m of copies(g.x0, g.x1)) {
            if (!boxVisible(g, m)) continue;
            for (const a of g.rings) traceRing(a, m, close);
        }
    }

    // ------------------------------------------------------------- basemap
    // NASA Blue Marble (equirectangular): the whole-world image when zoomed
    // out; zoomed in further than it can show sharply, 10° tiles cut from the
    // full 21600 x 10800 image (build_tiles.py) are drawn over it. Images are
    // kept on the page for the whole review session. Equirectangular rows are
    // drawn as thin horizontal strips, each stretched onto its mercator rows.
    const TILE_DEG = 10, BASE_W = 4096;
    const TILES_ABOVE = 1.3 * BASE_W / 360; // px per degree where tiles take over
    window.__geogImgs = window.__geogImgs || new Map(); // src -> Image (loaded or loading)
    window.__geogRedraw = null;
    function image(src) {
        let img = window.__geogImgs.get(src);
        if (!img) {
            img = new Image();
            img.onload = () => { if (window.__geogRedraw) window.__geogRedraw(); };
            img.src = src;
            window.__geogImgs.set(src, img);
        }
        return img.complete && img.naturalWidth ? img : null;
    }
    // Draw the part of `img` covering lon lonW..lonW+dLon, lat latN..latS.
    function drawEquirect(img, lonW, dLon, latN, latS, strip) {
        const iw = img.naturalWidth, ih = img.naturalHeight;
        for (const m of copies(lonW, lonW + dLon)) {
            const x = sx(lonW + 360 * m), w = dLon * k;
            for (let lat = Math.min(latN, MAX_LAT); lat > Math.max(latS, -MAX_LAT); lat -= strip) {
                const lat2 = Math.max(lat - strip, latS, -MAX_LAT);
                const yT = mercY(lat), yB = mercY(lat2);
                if (!yVisible(yT, yB)) continue;
                const top = sy(yT), bot = sy(yB);
                ctx.drawImage(img,
                    0, (latN - lat) / (latN - latS) * ih, iw, (lat - lat2) / (latN - latS) * ih,
                    x, top, w, bot - top + 0.5); // +0.5 px hides seams between strips
            }
        }
    }
    function drawBasemap() {
        const base = image("geog_bluemarble.jpg");
        if (base) drawEquirect(base, -180, 360, 90, -90, 2);
        if (k < TILES_ABOVE) return;
        const L = lon0 - W / 2 / k, R = lon0 + W / 2 / k;
        const latTop = invMercY(y0 + H / 2 / k), latBot = invMercY(y0 - H / 2 / k);
        for (let row = Math.floor((90 - latTop) / TILE_DEG); row <= Math.floor((90 - latBot) / TILE_DEG); row++) {
            if (row < 0 || row > 17) continue;
            for (let c = Math.floor((L + 180) / TILE_DEG); c <= Math.floor((R + 180) / TILE_DEG); c++) {
                const col = ((c % 36) + 36) % 36;
                const img = image("geog_bm_" + col + "_" + row + ".jpg");
                if (img) drawEquirect(img, -180 + col * TILE_DEG, TILE_DEG, 90 - row * TILE_DEG, 80 - row * TILE_DEG, 1);
            }
        }
    }

    // ---------------------------------------------------------------- labels
    // Arabic-script names (Egypt, Levant, Gulf, Pakistan, ...) fall through to
    // a bundled Noto Sans Arabic instead of whatever the system has.
    const LABEL_FONT = "'Trebuchet MS', 'Noto Sans Arabic', sans-serif";
    async function loadLabelFont() {
        for (const ff of document.fonts) {
            if (ff.family.replace(/["']/g, "") === "Noto Sans Arabic" && ff.status === "loaded") return;
        }
        try {
            const ff = new FontFace("Noto Sans Arabic", "url(_noto_sans_arabic.woff2)");
            document.fonts.add(await ff.load());
        } catch (e) { /* missing font: the system fallback still renders */ }
    }

    // Label draw order where labels overlap (drawn last = on top): other
    // cities, regions/rivers, state capitals, national capitals, the answer.
    function labelPrio(f) {
        if (f === feature) return 0;
        if (f.geometry.type !== "Point") return 4;
        const ct = f.properties.capitaltype;
        return ct === "national" ? 2 : ct === "state" ? 3 : 5;
    }
    const labelOrder = features.slice().sort((a, b) => labelPrio(b) - labelPrio(a));

    // Each label is rasterised once (outlined text is slow to draw) and then
    // copied onto the map every frame.
    const labelCache = new Map();
    function labelImage(text, size, color) {
        size = Math.round(size * labelScale * 2) / 2; // half-px steps keep the cache small
        const key = text + "\u0000" + size + color;
        let c = labelCache.get(key);
        if (c) return c;
        const font = size + "px " + LABEL_FONT, outline = size * 0.14, pad = Math.ceil(outline);
        const m = document.createElement("canvas").getContext("2d");
        m.font = font;
        const w = Math.ceil(m.measureText(text).width) + 2 * pad, h = Math.ceil(size * 1.3) + 2 * pad;
        c = document.createElement("canvas");
        c.width = Math.ceil(w * DPR); c.height = Math.ceil(h * DPR);
        const x = c.getContext("2d");
        x.scale(DPR, DPR);
        x.font = font;
        x.textAlign = "center";
        x.textBaseline = "middle";
        x.lineJoin = "round";
        x.lineWidth = outline;
        x.strokeStyle = "rgba(0,0,0,0.9)";
        x.strokeText(text, w / 2, h / 2);
        x.fillStyle = color;
        x.fillText(text, w / 2, h / 2);
        c.cssW = w; c.cssH = h;
        labelCache.set(key, c);
        return c;
    }
    // Centred on x; vertically: "above" / "below" sit just off y (a city's
    // label clears its dot), "center" is centred on y (a region's label).
    // Returns the label's bottom edge.
    function drawLabel(text, x, y, size, color, pos) {
        const c = labelImage(text, size, color), gap = size * labelScale * 0.15;
        const top = pos === "below" ? y + gap : pos === "center" ? y - c.cssH / 2 : y - gap - c.cssH;
        ctx.drawImage(c, x - c.cssW / 2, top, c.cssW, c.cssH);
        return top + c.cssH;
    }

    // ------------------------------------------------------------------ draw
    function draw() {
        ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
        ctx.fillStyle = "#05070d";
        ctx.fillRect(0, 0, W, H);
        drawBasemap();

        ctx.lineJoin = "round";
        ctx.lineCap = "round";
        // Front shows only the target (that is the question); every other
        // outline, dot and label is context and is drawn on the back only.
        const shown = onBack ? features : (feature ? [feature] : []);

        // context region outlines, then rivers: one path each
        for (const river of [false, true]) {
            ctx.beginPath();
            for (const f of shown) {
                const t = f.geometry.type;
                if (f === feature || t === "Point" || (t === "LineString") !== river) continue;
                traceFeature(f, false);
            }
            ctx.lineWidth = river ? 2.2 : 1.6;
            ctx.strokeStyle = river ? "rgba(255,95,95,0.65)" : "rgba(215,215,225,0.6)";
            ctx.stroke();
        }

        // the target region: fill + outline
        if (feature && feature.geometry.type !== "Point") {
            const line = feature.geometry.type === "LineString";
            if (!line) {
                ctx.beginPath();
                traceFeature(feature, true);
                ctx.fillStyle = "rgba(255,64,64,0.30)";
                ctx.fill();
            }
            ctx.beginPath();
            traceFeature(feature, !line);
            ctx.lineWidth = line ? 4 : 3.5;
            ctx.strokeStyle = "#ff4040";
            ctx.stroke();
        }

        // city dots (the target's last, on top)
        ctx.lineWidth = dotScale;
        ctx.strokeStyle = "rgba(0,0,0,0.5)";
        const dot = (f, r, color) => {
            const g = geoOf(f);
            for (const m of copies(g.ax, g.ax)) {
                if (!boxVisible(g, m)) continue;
                ctx.beginPath();
                ctx.arc(sx(g.ax + 360 * m), sy(g.ay), r * dotScale, 0, 2 * Math.PI);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.stroke();
            }
        };
        for (const f of shown) {
            if (f.geometry.type !== "Point" || f === feature) continue;
            const ct = f.properties.capitaltype;
            dot(f, ct === "national" ? 4.1 : ct === "state" ? 2.9 : 1.9, "#2bd6d6");
        }
        if (feature && feature.geometry.type === "Point") dot(feature, 5.8, "#ff5555");

        // labels: back only, every feature
        if (!onBack) return;
        // A place with the same name as the answer (Batangas City for Batangas
        // province, ...) gets no white label of its own; the answer's red label
        // is drawn where that label would have been instead.
        const twin = feature && features.find((f) => f !== feature && f.properties.name === feature.properties.name);
        for (const f of labelOrder) {
            if (f === twin) continue;
            const g = geoOf(f === feature && twin ? twin : f);
            for (const m of copies(g.ax - 30, g.ax + 30)) { // ±30°: a label is wider than its point
                const x = sx(g.ax + 360 * m), y = sy(g.ay);
                if (x < -300 || x > W + 300 || y < -60 || y > H + 60) continue;
                // a city's label sits above its dot; a region's is centred on it
                const pos = (f === feature && twin ? twin : f).geometry.type === "Point" ? "above" : "center";
                if (f !== feature) {
                    drawLabel(f.properties.name, x, y, 29, "#ffffff", pos);
                    continue;
                }
                const bottom = drawLabel(f.properties.name, x, y, 44, "#ff9a9a", pos);
                // the province a city is in, when the data has it (never the country)
                const sub = f.properties.state;
                if (sub && sub !== f.properties.name) drawLabel(sub, x, pos === "center" ? bottom : y, 31, "#ffd0d0", "below");
            }
        }
    }

    // --------------------------------------------------------------- framing
    let framed = false;
    function frameTarget() {
        if (!feature) { lon0 = 0; y0 = mercY(20); k = W / 120; return; }
        const g = geoOf(feature);
        lon0 = (g.x0 + g.x1) / 2;
        y0 = (g.y0 + g.y1) / 2;
        if (feature.geometry.type === "Point") {
            // About 19° of longitude across the screen, but zoomed in further if
            // needed so the nearest other city is at least 1/12 of the screen
            // width away (map distance, so it matches what's drawn).
            k = W / 18.75;
            let nearest = Infinity;
            for (const f of features) {
                if (f === feature || f.geometry.type !== "Point") continue;
                const o = geoOf(f);
                let dx = Math.abs(o.ax - g.ax) % 360;
                dx = Math.min(dx, 360 - dx);
                const d = Math.hypot(dx, o.ay - g.ay);
                if (d > 0) nearest = Math.min(nearest, d);
            }
            if (nearest < Infinity) k = Math.max(k, W / 12 / nearest);
        } else {
            // the region's bounding box fills about 23% of the screen
            k = Math.min(0.23 * W / Math.max(g.x1 - g.x0, 1e-4), 0.23 * H / Math.max(g.y1 - g.y0, 1e-4));
        }
    }

    // ----------------------------------------------------------- render loop
    let pending = false, frameTimer = null, frameReq = 0;
    function render() {
        pending = false;
        cancelAnimationFrame(frameReq);
        clearTimeout(frameTimer);
        if (sig.aborted || !canvas.isConnected) return; // a newer card owns the page
        const w = canvas.clientWidth || 300;
        const h = canvas.clientHeight || 300;
        if (w !== W || h !== H) {
            W = w; H = h;
            updateScales();
            canvas.width = Math.round(w * DPR);
            canvas.height = Math.round(h * DPR);
            if (!framed) { frameTarget(); framed = true; }
        }
        clampView();
        draw();
    }
    // Draw on the next animation frame, or after 50 ms if that frame hasn't
    // come (Anki's webview has been seen to hold frames back until the next input).
    function requestRender() {
        if (pending) return;
        pending = true;
        frameReq = requestAnimationFrame(render);
        frameTimer = setTimeout(render, 50);
    }
    window.__geogRedraw = requestRender; // basemap images call this when they arrive
    // Desktop Anki has dropped frames drawn while it swaps the card in; redraw
    // a few more times after loading (a repeat frame is cheap and harmless).
    const settleTimers = [];
    function settle(delays) {
        for (const t of settleTimers.splice(0)) clearTimeout(t);
        for (const d of delays) settleTimers.push(setTimeout(requestRender, d));
    }
    sig.addEventListener("abort", () => settle([]));

    // ----------------------------------------------------------- interaction
    let dragging = false, moved = false, px = 0, py = 0;
    let pinching = false, pinchStart = 0, pinchK0 = 0;

    // zoom by `factor`, keeping the map point under screen (cx, cy) in place
    function zoomAt(factor, cx, cy) {
        const lonP = lon0 + (cx - W / 2) / k, yP = y0 - (cy - H / 2) / k;
        k = Math.max(kMin(), Math.min(K_MAX, k * factor));
        lon0 = lonP - (cx - W / 2) / k;
        y0 = yP + (cy - H / 2) / k;
        requestRender();
    }
    function canvasXY(clientX, clientY) {
        const r = canvas.getBoundingClientRect();
        return [clientX - r.left, clientY - r.top];
    }
    function dragTo(cx, cy, e) {
        const dx = cx - px, dy = cy - py;
        if (!moved && Math.abs(dx) + Math.abs(dy) > 3) moved = true;
        px = cx; py = cy;
        if (!moved) return;
        if (e && e.cancelable) e.preventDefault();
        const sel = window.getSelection && window.getSelection();
        if (sel && sel.removeAllRanges) sel.removeAllRanges();
        lon0 -= dx / k;
        y0 += dy / k;
        requestRender();
    }
    function touchSpread(t) {
        return Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
    }

    // --- mouse ---
    document.addEventListener("mousedown", (e) => {
        playFeatureAudio();
        dragging = true; moved = false;
        px = e.clientX; py = e.clientY;
    }, { signal: sig });
    document.addEventListener("mousemove", (e) => { if (dragging) dragTo(e.clientX, e.clientY, e); }, { signal: sig });
    document.addEventListener("mouseup", () => { dragging = false; }, { signal: sig });
    document.addEventListener("wheel", (e) => {
        if (e.cancelable) e.preventDefault();
        const [cx, cy] = canvasXY(e.clientX, e.clientY);
        zoomAt(e.deltaY > 0 ? 1 / 1.15 : 1.15, cx, cy);
    }, { passive: false, signal: sig });

    // --- touch: one finger pans, two fingers pinch-zoom around their midpoint ---
    document.addEventListener("touchstart", (e) => {
        playFeatureAudio();
        if (e.touches.length >= 2) {
            pinching = true; dragging = false;
            pinchStart = touchSpread(e.touches);
            pinchK0 = k;
        } else if (e.touches.length === 1) {
            dragging = true; moved = false;
            px = e.touches[0].clientX; py = e.touches[0].clientY;
        }
    }, { passive: true, signal: sig });
    document.addEventListener("touchmove", (e) => {
        if (pinching && e.touches.length >= 2) {
            if (e.cancelable) e.preventDefault();
            const spread = touchSpread(e.touches);
            if (spread > 0 && pinchStart > 0) {
                const [cx, cy] = canvasXY((e.touches[0].clientX + e.touches[1].clientX) / 2,
                                          (e.touches[0].clientY + e.touches[1].clientY) / 2);
                zoomAt(pinchK0 * (spread / pinchStart) / k, cx, cy);
            }
        } else if (dragging && e.touches.length === 1) {
            dragTo(e.touches[0].clientX, e.touches[0].clientY, e);
        }
    }, { passive: false, signal: sig });
    function endTouch(e) {
        if (e.touches.length < 2) pinching = false;
        if (e.touches.length === 1) {
            // a finger lifted after a pinch: keep panning from the one that remains
            dragging = true; moved = true;
            px = e.touches[0].clientX; py = e.touches[0].clientY;
        } else if (e.touches.length === 0) {
            dragging = false;
        }
    }
    document.addEventListener("touchend", endTouch, { signal: sig });
    document.addEventListener("touchcancel", endTouch, { signal: sig });

    // -------------------------------------------------------------------- go
    if (onBack) await loadLabelFont();
    if (sig.aborted) return;
    if (window.ResizeObserver) {
        const ro = new ResizeObserver(requestRender);
        ro.observe(canvas.parentElement || canvas);
        sig.addEventListener("abort", () => ro.disconnect());
    }
    window.addEventListener("resize", requestRender, { signal: sig });
    render(); // first frame now, not on a requested frame that might be held back
    settle([100, 300, 700, 1500]);
    // Anki's reviewer runs onShownHook once the card side is actually on screen.
    if (Array.isArray(window.onShownHook)) window.onShownHook.push(() => { if (!sig.aborted) { requestRender(); settle([100, 300]); } });
    document.addEventListener("visibilitychange", requestRender, { signal: sig });
})();
