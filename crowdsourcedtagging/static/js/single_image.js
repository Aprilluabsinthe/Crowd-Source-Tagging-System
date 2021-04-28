// reference from https://www.thirdrocktechkno.com/blog/drawing-a-square-or-rectangle-over-html5-canvas-using-fabricjs/
var Rectangle = (function () {
    function Rectangle(canvas) {
        var instance = this;
        this.canvas = canvas;
        this.className= 'RectangleTag';
        this.isDrawing = false;
        this.bindEvents();
    }

	Rectangle.prototype.bindEvents = function() {
        var instance = this;
        instance.canvas.on('mouse:down', function(o) {
            instance.onMouseDown(o);
        });
        instance.canvas.on('mouse:move', function(o) {
            instance.onMouseMove(o);
        });
        instance.canvas.on('mouse:up', function(o) {
            instance.onMouseUp(o);
        });
        instance.canvas.on('object:moving', function(o) {
            instance.disable();
        })
    }

    Rectangle.prototype.onMouseDown = function (o) {
        var instance = this;
        instance.enable();

        var pointer = instance.canvas.getPointer(o.e);
        origX = pointer.x;
        origY = pointer.y;

    	var rect = new fabric.Rect({
            left: origX,
            top: origY,
            originX: 'left',
            originY: 'top',
            width: pointer.x-origX,
            height: pointer.y-origY,
            transparentCorners: true,
            hasBorders: false,
            hasControls: false
        });

  	    instance.canvas.add(rect).setActiveObject(rect);
    };

    Rectangle.prototype.onMouseMove = function (o) {
        var instance = this;
      
        if(!instance.isEnable()){ return; }

        var pointer = instance.canvas.getPointer(o.e);
        var activeObj = instance.canvas.getActiveObject();

        console.log("mouse move rectange width:" + activeObj.width + " height: " + activeObj.height);

        activeObj.stroke= 'black',
        activeObj.strokeWidth= 3;
        activeObj.fill = 'transparent';

        if(origX > pointer.x){
            activeObj.set({ left: Math.abs(pointer.x) }); 
        }
        if(origY > pointer.y){
            activeObj.set({ top: Math.abs(pointer.y) });
        }

        activeObj.set({ width: Math.abs(origX - pointer.x) });
        activeObj.set({ height: Math.abs(origY - pointer.y) });

        activeObj.setCoords();
        instance.canvas.renderAll();

    };

    Rectangle.prototype.onMouseUp = function (o) {
        var instance = this;
        instance.disable();
    };

    Rectangle.prototype.isEnable = function(){
        return this.isDrawing;
    }

    Rectangle.prototype.enable = function(){
        this.isDrawing = true;
    }

    Rectangle.prototype.disable = function(){
        this.isDrawing = false;
    }

    return Rectangle;
}());

let img = new Image()
img.src = document.getElementById("id_tag_img").src
console.log(img.height)
document.getElementById("canvas").height = img.height * (document.getElementById("canvas").width / img.width)
var canvas = new fabric.Canvas('canvas');
loadImg(true);
// loadNextPrev();

function loadImg(loadTag) {
    fabric.Image.fromURL(document.getElementById("id_tag_img").src, function(img) {
        canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas), {
            scaleX: canvas.width / img.width,
            scaleY: canvas.width / img.width
        });
    });
    let user_image_task_tag;
    if (loadTag) {
        user_image_task_tag = document.getElementById("id_user_image_task_tag").value;
        if (user_image_task_tag !== "NULL") {
            canvas.loadFromJSON(JSON.parse(user_image_task_tag), canvas.renderAll.bind(canvas));
            updateBadge();
        }
    }
}
  
var rectangle = new Rectangle(canvas);

function clearCanvas() {
    canvas.clear();
    loadImg(false);
}

function saveCanvas() {
    var json = canvas.toJSON();
    delete json.backgroundImage;
    console.log(json)
    
    var request = new XMLHttpRequest()
    request.onreadystatechange = function() {
        if (request.readyState !== 4) return
        let response = JSON.parse(request.responseText)
        updatePage(response.message);
    }

    request.open("POST", "/crowdsourcedtagging/image_tag", true);
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    request.send( "image_task_id=" + document.getElementById("id_image_task_id").value + 
                "&image_task_tag=" + JSON.stringify(json) + 
                "&csrfmiddlewaretoken=" + getCSRFToken());
}

function updateBadge() {
    let json = canvas.toJSON();
    if (json.objects.length !== 0) {
        document.getElementById("tagged").style = "display: initial";
    }
}

function updatePage(message) {
    document.getElementById("toast-content").innerText = message
    $('#toast').toast({delay: 2000});
    $("#toast").toast('show');
    updateBadge();
}

function getCSRFToken() {
    let cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim()
        if (c.startsWith("csrftoken=")) {
            return c.substring("csrftoken=".length, c.length)
        }
    }
    return "unknown"
}