// Function to dynamically inject a script
var injectScript = (src) => {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
};

(async () => {
    var typedCities = [];
    var cardType = document.getElementById("card_type").innerHTML;
    var typeElement = document.getElementById("type_input");
    var textElement = document.getElementById("txt");
    var backElement = document.getElementById("back");
    var onBack = !!backElement;
    if (onBack) {
        backElement.remove();
        typeElement.remove();
    }

    var cardData = document.getElementById("card_data").innerHTML;
    var nameField = (cardData.startsWith("(")) ? "Bekasi::Indonesia_Kabupaten" : cardData;
    var splitName = nameField.split("::");
    var featureName = splitName[0];
    var countryName = splitName[1];
    countryjson = {"type":"FeatureCollection","features":[]};

    if(cardType == "Click_The_Feature"){
        typeElement.value = featureName;
    }

    await injectScript('geog_' + countryName + '.js');

    var feature = -1;
    var isCityQuestion = false;
    var hasDeterminedZoom = false;

    for (var i = 0; i < countryjson.features.length; i++) {
        if (countryjson.features[i].properties.name == featureName || countryjson.features[i].properties.name_en == featureName) {
            feature = countryjson.features[i];
            isCityQuestion = feature.type == "Point";
            break;
        }
    }

    // Function to play audio for a feature
    var playAudio = function (str) {
        var audioElement = document.getElementById("audio");
        var prefix = "https://github.com/2swap/Anki/raw/main/Geography/Decks/" + countryName + "/geogaudio_";
        var encodey = encodeURIComponent(str);
        audioElement.src = prefix + encodey + ".mp3";
        audioElement.autoplay = true;
    }

    // Function to play feature audio when on back
    var playFeatureAudio = function () {
        if (!onBack && cardType == "Name_The_Feature") return;
        playAudio(feature.properties.name);
    }

    playFeatureAudio();

    document.addEventListener("mousedown", playFeatureAudio);
    document.addEventListener("touchstart", playFeatureAudio);

    var canvas = document.getElementById("canvas");
    var ctx = canvas.getContext("2d");
    var crowdedness = 0;

    var computeZoom = function(){
        if (isCityQuestion) {
            drawFeatures();
            crowdedness -= zoom.m;
            distToClosest = Math.sqrt(1 / crowdedness);
            zoom.z = .1 * distToClosest;
        } else {
            drawMultiPolygon(feature);
        }
        if(cardType == "Click_The_Feature"){
            var delta = zoom.z/2;
            zoom.y = Math.floor(zoom.y/delta) * delta;
            zoom.x = Math.floor(zoom.x/delta) * delta;
            zoom.z *= 2.;
        }
        hasDeterminedZoom = true;
    }

    // Main render function
    var render = function () {
        if(!hasDeterminedZoom) computeZoom();
        //Wipe the canvas
        var parentDims = canvas.parentElement.getBoundingClientRect();
        canvas.width = parentDims.width;
        canvas.height = parentDims.height;

        drawMap();
        drawFeatures();
    }

    var maps = ['political.svg', 'coastline.jpg', 'earth.jpg', 'night.jpg'];
    var mapNo = 0;
    var images = [];
    for (var i = 0; i < maps.length; i++) {
        images[i] = new Image;
        if (i == mapNo) images[i].onload = render;
        images[i].src = "geog_" + maps[i];
    }

    var zoom = { x: 1, y: 1, m:0, z:.5};
    if(isCityQuestion) {
        zoom.x = lonToX(feature.geometry.coordinates[0]);
        zoom.y = latToY(feature.geometry.coordinates[1]);
    }

    // Function to draw shapes on the map
    function drawFeatures() {
        ctx.textAlign = "center"
        for (var i in countryjson.features) {
            var shape = countryjson.features[i];
            var prevzoom = zoom.z;
            if(shape.geometry.type == "Point") drawTriplePoint(shape);
            else if(shape.geometry.type == "LineString") drawLineString(shape);
            else drawMultiPolygon(shape);
            zoom.z = prevzoom;
        }
    }

    function latToY(lat) {
        return -lat / 180 + .5;
    }

    function lonToX(lon) {
        return lon / 360 + .5;
    }

    function bound(val, min, max) {
        return Math.min(Math.max(val, min), max);
    }

    // Function to draw a point on the map three times (for wrap-around effect)
    function drawTriplePoint(f) {
        // Ensure the object is a Point
        if (f.geometry.type !== "Point") {
            textElement.innerHTML = "Object is not a Point";
            return;
        }
        var highlight = f == feature;
        if(cardType == "Click_The_Feature") highlight &= onBack;
        var coords = f.geometry.coordinates;
        drawPoint(coords[0], coords[1], highlight, f.properties.capitaltype);
        drawPoint(coords[0] - 360, coords[1], highlight, f.properties.capitaltype);
        drawPoint(coords[0] + 360, coords[1], highlight, f.properties.capitaltype);

        if ((onBack || typedCities.includes(f.properties.name_en) || typedCities.includes(f.properties.name)) && Math.hypot(coords[0] - feature.geometry.coordinates[0], coords[1] - feature.geometry.coordinates[1]) < zoom.z * 300) {
            if (highlight) {
                ctx.fillStyle = "#f66";
                ctx.font = "24px Trebuchet MS";
                var x = latOrLongToPixel(lonToX(coords[0]), true);
                var y = latOrLongToPixel(latToY(coords[1]), false);
                ctx.fillText(feature.properties.name, x, y + 34);
                ctx.font = "16px Trebuchet MS";
                var writeStateName = feature.properties.state !== "" && typeof feature.properties.state !== "undefined";
                var text = writeStateName ? feature.properties.state : feature.properties.country;
                ctx.fillText(text, x, y+54);
            } else {
                ctx.font = "16px Trebuchet MS";
                var x = latOrLongToPixel(lonToX(coords[0]), true);
                var y = latOrLongToPixel(latToY(coords[1]), false);
                ctx.fillText(f.properties.name, x, y + 18);
            }
        }
    }

    // Function to draw a single point on the map
    function drawPoint(lon, lat, red, capitaltype) {
        ctx.lineWidth = 3;
        ctx.fillStyle = ctx.strokeStyle = red ? "#f66" : "#0aa";
        var shift = bound(1 / zoom.z, 2, 8);
        var x = latOrLongToPixel(lonToX(lon), true);
        var y = latOrLongToPixel(latToY(lat), false);
        ctx.beginPath();
        if (capitaltype == "national") {
            ctx.arc(x, y, shift * .75, 0, 2 * Math.PI, false);
            ctx.stroke();
        } else if (capitaltype == "state") {
            ctx.arc(x, y, shift * .5, 0, 2 * Math.PI, false);
            ctx.stroke();
        } else {
            ctx.arc(x, y, shift / 2, 0, 2 * Math.PI, false);
            ctx.fill();
        }
        // Calculate the distance and adjust crowdedness
        var dx = (canvas.width / 2 - x) * zoom.z / 4;
        var dy = (canvas.height / 2 - y) * zoom.z / 4;
        var c = 1 / (dx * dx + dy * dy);
        if (Math.hypot(dy, dx) != 0) {
            crowdedness += c;
            zoom.m = Math.max(c, zoom.m);
        }
    }

    // Function to draw a geographical shape on the map
    function drawMultiPolygon(obj) {
        var fill = (obj === feature) && (cardType == "Name_The_Feature" || onBack);
        var multi = obj.geometry.type == "MultiPolygon";

        //Convert single-polygons to multis
        var multiShape = obj.geometry.coordinates;
        if (!multi) multiShape = [multiShape];

        ctx.lineWidth = fill ? .5 : .2;
        ctx.fillStyle = "red";
        ctx.strokeStyle = fill ? "red" : "black";
        var init = false;
        var maxx = -1000, maxy = -1000, minx = 1000, miny = 1000;
        for (var i in multiShape) {
            var shape = multiShape[i][0];
            ctx.beginPath();
            for (var j in shape) {
                var point = shape[j];
                var lon = point[0];
                var lat = point[1];
                var x = latOrLongToPixel(lonToX(lon), true);
                var y = latOrLongToPixel(latToY(lat), false);
                maxx = Math.max(maxx, lonToX(lon));
                maxy = Math.max(maxy, latToY(lat));
                minx = Math.min(minx, lonToX(lon));
                miny = Math.min(miny, latToY(lat));
                init ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
                init = true;
            }
            ctx.stroke();
            if (fill) {
                ctx.globalAlpha = .25;
                ctx.fill();
                ctx.globalAlpha = 1;
            }
        }
        var centerX = (maxx + minx) / 2;
        var centerY = (maxy + miny) / 2;
        if (obj === feature && !hasDeterminedZoom) {
            zoom.x = centerX;
            zoom.y = centerY;
            zoom.z = Math.max(maxx - minx, maxy - miny) * 2;
        }
        if(onBack || typedCities.includes(obj.properties.name)){
            ctx.fillStyle = "#f66";
            ctx.font = (obj === feature ? 18 : 14) + "px Trebuchet MS";
            ctx.fillText(obj.properties.name, latOrLongToPixel(centerX, true), latOrLongToPixel(centerY, false) + 5);
        }
    }

    // Function to draw a GeoJSON LineString on the map
    function drawLineString(obj) {
        // Ensure the object is a LineString
        if (obj.geometry.type !== "LineString") {
            textElement.innerHTML = "Object is not a LineString";
            return;
        }

        ctx.lineWidth = 2; // Adjust line width as needed
        ctx.strokeStyle = "red"; // Line color

        var coordinates = obj.geometry.coordinates;
        ctx.beginPath();

        // Loop through each coordinate in the LineString
        for (var i = 0; i < coordinates.length; i++) {
            var lon = coordinates[i][0];
            var lat = coordinates[i][1];
            var x = latOrLongToPixel(lonToX(lon), true);
            var y = latOrLongToPixel(latToY(lat), false);

            if (i === 0) {
                ctx.moveTo(x, y); // Move to the starting point without drawing a line
            } else {
                ctx.lineTo(x, y); // Draw a line to the next point
            }
        }

        ctx.stroke(); // Apply the line to the canvas
    }

    // Function to draw the entire map
    function drawMap() {
        var image = images[mapNo];
        for (let i = -1; i <= 1; i++) {
            const tlx = latOrLongToPixel(0 + i, true);
            const tly = latOrLongToPixel(0, false);
            const brx = latOrLongToPixel(1 + i, true);
            const bry = latOrLongToPixel(1, false);
            ctx.drawImage(image, tlx, tly, brx - tlx, bry - tly);
        }
    }

    // Function to calculate position on canvas
    function latOrLongToPixel(point, isX) {
        const zoomCoordinate = isX ? zoom.x : zoom.y;
        const canvasDimension = isX ? canvas.width : canvas.height;
        const size = isX ? 600 : 300;
        return ((point - zoomCoordinate) * 1 / zoom.z) * size + 0.5 * canvasDimension;
    }

    // Sanitize input string for comparison
    function sanitizeString(str) {
        // Remove diacritics and lower the case
        str = str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
        // Remove remaining nonalphanumeric chars
        str = str.replace(/[^a-z]/g, "");
        return str.length == 0 ? Math.random() : str;
    }

    // Event listener for typing input
    typeElement.focus();
    typeElement.addEventListener("keyup", function () {
        var currentInput = this.value;
        for (i in countryjson.features) {
            var geo = countryjson.features[i];
            if (sanitizeString(geo.properties.name) === sanitizeString(currentInput) || sanitizeString(geo.properties.name_en) === sanitizeString(currentInput)) {
                if(!typedCities.includes(geo.properties.name)){
                    playAudio(geo.properties.name);
                    typedCities.push(geo.properties.name);
                    this.value = "";
                    render();
                }
            }
        }
    });
    typeElement.addEventListener("keydown", function () {
        if (event.key == "Alt") {mapNo = (mapNo+1)%maps.length; render();}
        if (event.key == "Enter") typeElement.blur();
    });

    document.addEventListener("wheel", function(event) {
        // Prevent the default scrolling behavior
        event.preventDefault();

        zoom.z *= event.deltaY > 0 ? 2 : .5;
        render();
    });

})();
