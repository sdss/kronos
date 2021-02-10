function renderCloudCam(dataset){
    var image = new Image();
    image.src = "https://irsc.apo.nmsu.edu/tonight/current.gif";
    // image.src = "../static/images/cP105500.gif";
    // console.log(image)
    var cnvs = document.getElementById("myCanvas");

    var ctx = cnvs.getContext('2d');

    var x_0 = 290;
    var y_0 = 240;

    image.onload = function () {
        ctx.drawImage(image,
             cnvs.width / 2 - image.width / 2,
             cnvs.height / 2 - image.height / 2
        );
        // var c = "#73db04";
        function updateField(row){
            row.alt = Math.abs(row.alt);
            var altaz = altAzToXY(row.alt, row.az);
            var show = row.selected || row.expanded
            if(!show){
                // console.log("skipping", row.id, row);
                return
            }
            // console.log("plotting", row.id, row);
            drawField(ctx, x_0+altaz[0], y_0+altaz[1], row.color);
            if(row.selected){
                drawOutline(ctx, x_0+altaz[0], y_0+altaz[1], "#000000");
            }
            else{
                drawOutline(ctx, x_0+altaz[0], y_0+altaz[1], row.color);
            }
        }
        // drawField(ctx, x_0, y_0)
        for(i=0;i<dataset.length;i++){
            dataset[i].redraw = updateField;
            updateField(dataset[i])
        }
      }
    return ctx
}

function testViz(viz){
    for (i=0;i<viz.allRows.length;i++){
        console.log(i)
        console.log(viz.allRows[i])
    }
}

function drawOutline(ctx, x, y, c){
    c = typeof c !== 'undefined' ? c : '#000000';
    ctx.beginPath();
    ctx.arc(x, y, 8, 0, 2 * Math.PI, false); // false is counter clockwise, may change this
    ctx.lineWidth = 2;
    ctx.strokeStyle = c;
    ctx.stroke();
}

function drawField(ctx, x, y, c){
    c = typeof c !== 'undefined' ? c : '#8B0000';
    ctx.beginPath();
    ctx.arc(x, y, 8, 0, 2 * Math.PI, false); // false is counter clockwise, may change this
    ctx.fillStyle = c;
    ctx.fill();
}

function altAzToXY(alt, az){
    // assumes input in degrees
    var phi = radians(az - 90);
    var r = (90 - alt)*292/90;
    // console.log("alt %f az %f phi %f r %f", alt, az, phi, r)
    var x = r*Math.cos(phi);
    var y = r*Math.sin(phi);
    return [x, y];
}
