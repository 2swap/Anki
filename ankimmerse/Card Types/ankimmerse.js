
var textElement = document.getElementById("text");
var translationElement = document.getElementById("translation");
var typeElement = document.getElementById("type_input");
var debugElement = document.getElementById("debug");
var audioElement = document.querySelector(".soundLink, .replaybutton");
var isTranslationCard = !!document.getElementById("translationcard");

// Create an <audio> element
var audioElement = document.createElement("audio");
audioElement.setAttribute("controls", "");
audioElement.style.display = "none";
audioElement.setAttribute("autoplay", "true");

// Set the source of the <audio> element
var filename = "{{Audio}}".startsWith("(")?"_2swap_Sdio.mp3":"{{Audio}}";
var sourceElement = document.createElement("source");
sourceElement.setAttribute("src", filename);
audioElement.appendChild(sourceElement);


function debug(str){
    debugElement.innerHTML += str;
}

function isAudioPlaying() {
    return !audioElement.paused;
}

function replayAudio() {
    if(isAudioPlaying()) return;
    audioElement.currentTime = 0;
    audioElement.play();
}

function generateIndexedSentences(native, english, wordMap) {
    var nativeWithIndices = native;
    var englishWithIndices = english;
    var i = 0;

    var escapeRegExp = (text) => text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&');

    for (var [key, value] of Object.entries(wordMap)) {
        var keyRegex = new RegExp(`(?<!\\w)${escapeRegExp(key)}(?!\\w)`, 'gi');
        var valueRegex = new RegExp(`(?<!\\w)${escapeRegExp(value)}(?!\\w)`, 'gi');

        nativeWithIndices = nativeWithIndices.replace(keyRegex, (match) => `|${i}:${match}`);
        englishWithIndices = englishWithIndices.replace(valueRegex, (match) => `|${i}:${match}`);
        i++;
    }

    return [nativeWithIndices, englishWithIndices];
}

function normalizeUserInput(input) {
    return input.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[。？！―･ー… .,\/#!$%\^&\*;:{}=\-_`~()\?]/g,"").trim().toLowerCase();
}

var inAnkiEditor = `{{Text}}`.startsWith("(");
var textOriginal = inAnkiEditor ? "Cada lunes, visito a mi hermano en la ciudad." : `{{Text}}`;
var textNorm = normalizeUserInput(textOriginal);
var translationOriginal = inAnkiEditor ? "Every Monday, I visit my brother in the city." : `{{Translation}}`;
var wordMap = inAnkiEditor ? {"Cada": "Every","lunes": "Monday","visito": "I visit","mi": "my","hermano": "brother","en":"in","la": "the","ciudad": "city"} : JSON.parse(`{{WordMap}}`);
var [textMapping, translationMapping] = generateIndexedSentences(textOriginal, translationOriginal, wordMap);

var guessedIndices = [];

function indexToColor(index) {
    var hash = parseInt(index) * 123456789;
    var r = (hash & 0xFF0000) >> 16;
    var g = (hash & 0x00FF00) >> 8;
    var b = hash & 0x0000FF;
    return `rgb(255, ${r % 255}, ${g % 255})`;
}

function generateCensoredString(mapping) {
    if(isTranslationCard)
        return generateCensoredStringTranslationCard(mapping);
    return generateCensoredStringListeningCard(mapping);
}

function generateCensoredStringTranslationCard(mapping) {
    var ret = "";
    wordMap.forEach(word => {
        let index = segment.substring(0, colonIndex);
        let text = segment.substring(colonIndex + 1);
        var color = guessedIndices.includes(index) ? "white" : "black";
        ret += `<span style="color:white">${text}</span> <span style="color:${color}">${text}</span><br/>`;
    });
    return ret;
}

function generateCensoredStringListeningCard(mapping) {
    var ret = "";
    mapping.split('|').forEach(segment => {
        let colonIndex = segment.indexOf(':');
        let index = segment.substring(0, colonIndex);
        let text = segment.substring(colonIndex + 1);
        var color = guessedIndices.includes(index) ? indexToColor(index) : "black";
        ret += `<span style="color:${color}">${text}</span>`;
    });
    return ret;
}

function updateShownText() {
    textElement.innerHTML = generateCensoredString(textMapping);
    translationElement.innerHTML = generateCensoredString(translationMapping);
}
updateShownText(); // Initial display update

document.getElementById("type_input").addEventListener('input', function(event) {
    if (!isAudioPlaying()) replayAudio();
    var inputValue = normalizeUserInput(event.target.value);
    let matched = false;

    textMapping.split('|').forEach(segment => {
        let colonIndex = segment.indexOf(':');
        let index = segment.substring(0, colonIndex);
        let text = normalizeUserInput(segment.substring(colonIndex + 1)).split(" ")[0];

        if (text.length > 0 && inputValue.includes(text) && textNorm.includes(inputValue) && !guessedIndices.includes(index)) {
            matched = true;
            guessedIndices.push(index);
        }
    });

    if (matched) {
        updateShownText();
      　this.value = '';
    }
});

// Clear all existing timeouts
var id = window.setTimeout(function() {}, 0);
while (id--) {
    window.clearTimeout(id); // will do nothing if no timeout with id is present
}

if(document.getElementById("back")){
    document.getElementById('type_input').remove();
    guessedIndices = textMapping.split('|').map(segment => segment.substring(0, segment.indexOf(':')));
    updateShownText();
    audioElement.pause();
    document.getElementById("subs2srs_pic").style.display = "block";
    setTimeout(function() {document.getElementById("subs2srs_pic").innerHTML = `{{Pic2}}`;}, 1800);
} else {
    document.getElementById('type_input').focus();
}

typeElement.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        typeElement.blur();
        audioElement.pause();
    }
});

document.addEventListener("keydown", function (event) {
    if (event.key === "Shift") {
        replayAudio();
    }else if("1234".includes(event.key)||event.key == Enter){
        audioElement.pause();
        textElement.focus();
    }
});

document.addEventListener("click", function (event) {
    replayAudio();
});

