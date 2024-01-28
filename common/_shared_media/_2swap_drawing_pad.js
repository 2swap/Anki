var flag = false,
    prevX = 0,
    currX = 0,
    prevY = 0,
    currY = 0,
    dot_flag = false;

var canvas = document.getElementById('can');
var ctx = canvas.getContext("2d");

// Function to set canvas dimensions based on the viewport size
function setCanvasSize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

// Call the function to set initial dimensions and update them when the window resizes
setCanvasSize();
window.addEventListener('resize', setCanvasSize);

function draw() {
    ctx.beginPath();
    ctx.moveTo(prevX, prevY);
    ctx.lineTo(currX, currY);
    ctx.strokeStyle = "white";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.closePath();
    var p = canvas.parentElement.parentElement;
}

function findxy(res, e) {
    if (res == 'down') {
        prevX = currX;
        prevY = currY;
        currX = e.clientX;
        currY = e.clientY;

        flag = true;
        dot_flag = true;
        if (dot_flag) {
            ctx.beginPath();
            ctx.fillStyle = x;
            ctx.fillRect(currX, currY, 2, 2);
            ctx.closePath();
            dot_flag = false;
        }
    }
    if (res == 'up' || res == "out") {
        flag = false;
    }
    if (res == 'move') {
        if (flag) {
            prevX = currX;
            prevY = currY;
            currX = e.clientX - canvas.offsetLeft;
            currY = e.clientY - canvas.offsetTop;
            draw();
        }
    }
}

document.addEventListener("mousemove", function (e) {
    findxy('move', e)
}, false);
document.addEventListener("mousedown", function (e) {
    findxy('down', e)
}, false);
document.addEventListener("mouseup", function (e) {
    findxy('up', e)
}, false);
document.addEventListener("mouseout", function (e) {
    findxy('out', e)
}, false);    
document.addEventListener("ontouchmove", function (e) {
    findxy('move', e)
}, false);
document.addEventListener("ontouchstart", function (e) {
    findxy('down', e)
}, false);
document.addEventListener("ontouchend", function (e) {
    findxy('up', e)
}, false);
document.addEventListener("ontouchout", function (e) {
    findxy('out', e)
}, false);
draw();
