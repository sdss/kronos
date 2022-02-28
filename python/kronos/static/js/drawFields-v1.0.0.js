const x_0 = 290;
const y_0 = 240;

function renderCloudCam(dataset, backups){
    var image = new Image();
    image.src = "https://irsc.apo.nmsu.edu/tonight/current.gif";
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
            row.alt = row.alt;
            var altaz = altAzToXY_backwards(row.alt, row.az);
            var show = row.selected || row.expanded
            if(!show){
                // console.log("skipping", row.id, row);
                return
            }
            // console.log("plotting", row.trueHA, row.alt, row.az);
            // console.log(x_0, y_0, altaz[0], altaz[1]);
            drawField(ctx, x_0-altaz[0], y_0+altaz[1], row.color);
            if(row.selected){
                drawOutline(ctx, x_0-altaz[0], y_0+altaz[1], "#000000");
            }
            else{
                drawOutline(ctx, x_0-altaz[0], y_0+altaz[1], row.color);
            }
        }
        // drawField(ctx, x_0, y_0)
        for(i=0;i<dataset.length;i++){
            dataset[i].redraw = updateField;
            updateField(dataset[i])
        }

        for(i=0;i<backups.length;i++){
            let altAz = getAltAz(backups[i].trueHA, backups[i].dec);
            backups[i].alt = altAz[0];
            backups[i].az = altAz[1];
            backups[i].redraw = updateField;
            updateField(backups[i]);
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
    ctx.arc(x, y, 12, 0, 2 * Math.PI, false); // false is counter clockwise, may change this
    ctx.fillStyle = c;
    ctx.fill();
}

function drawSky(ctx, x, y, c){
    c = typeof c !== 'undefined' ? c : '#8B0000';
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, 2 * Math.PI, false); // false is counter clockwise, may change this
    ctx.fillStyle = c;
    ctx.fill();
}

function radians(x){
    return x*Math.PI/180;
}

function altAzToXY_backwards(alt, az){
    // assumes input in degrees
    var phi = radians(az - 90);
    var r = (90 - alt)*292/90;
    // console.log("alt %f az %f phi %f r %f", alt, az, phi, r);
    var x = r*Math.cos(phi);
    var y = r*Math.sin(phi);
    return [x, y];
}

function altAzToXY(alt, az){
    // assumes input in degrees
    var phi = radians(az - 90);
    var r = (90 - alt)*292/90;
    // console.log("alt %f az %f phi %f r %f", alt, az, phi, r);
    var x = r*Math.cos(phi);
    var y = r*Math.sin(phi);
    return [x, y];
}

function colorBar(ctx, reverse){
    ctx.font = '12px serif';
    for(var i = 0; i <= 255; i++) {
        ctx.beginPath();
        
        var color = 'rgb(100, ' + i + ', ' + i + ')';
        ctx.fillStyle = color;
        
        ctx.fillRect(590, i * 2, 20, 2);
        if (i % 30 == 0){
            ctx.fillStyle = "black";
            ctx.fillText(reverse(i).toFixed(1), 615, i * 2);
            ctx.beginPath();
            ctx.moveTo(610, i * 2);
            ctx.lineTo(615, i * 2);
            ctx.closePath();
            ctx.stroke();
        }
        ctx.save();
        ctx.translate(650, 290);
        ctx.rotate(-Math.PI/2);
        ctx.font = '14px serif';
        ctx.fillStyle = "black";
        // ctx.textAlign = "center";
        ctx.fillText("ΔV estimated", 0, 0);
        ctx.restore();
    }
}

function drawGrid(ctx){
    for(i=1; i<7; i++){
        var r = i*15/90*292
        ctx.beginPath();
        ctx.arc(290, 240, r, 0, 2 * Math.PI, false);
        ctx.lineWidth = 1;
        ctx.strokeStyle = "black";
        ctx.stroke();
    }
    ctx.beginPath();
    ctx.moveTo(0, 240);
    ctx.lineTo(580, 240);
    ctx.strokeStyle = "black";
    ctx.closePath();
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(290, 0);
    ctx.lineTo(290, 535);
    ctx.strokeStyle = "black";
    ctx.closePath();
    ctx.stroke(); 
}

function moon(ctx, alt, az){
    if(alt<0){
        // console.log("moon down", alt, az)
        return
    }
    var altaz = altAzToXY_backwards(alt, az);
    // console.log("moon ", alt, az, altaz)
    ctx.font = '24px serif';
    ctx.fillText("🌝", x_0-altaz[0], y_0+altaz[1]);
}

function field(ctx, alt, az){
    if(alt<0){
        return
    }
    var altaz = altAzToXY_backwards(alt, az);
    ctx.beginPath();
    ctx.arc(x_0-altaz[0], y_0+altaz[1], 8, 0, 2 * Math.PI, false);
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#000000';
    ctx.stroke();
}

function annotate(ctx, time, phase, falt, faz){
    ctx.font = '20px serif';
    ctx.fillStyle = "black";
    var text = time
    text += " ,    field (alt, az): " 
    text += "(" + falt.toFixed(1) + ", " + faz.toFixed(1) + ")"
    text += ",    phase: " + phase.toFixed(2);
    ctx.fillText(text, 20, 560);
}

function renderFieldBrightness(ks91){
    var cnvs = document.getElementById("brightCanvas");

    var ctx = cnvs.getContext('2d');

    ctx.clearRect(0, 0, cnvs.width, cnvs.height);

    var diff = ks91.dmax-ks91.dmin;
    var scale = 255/diff;
    function translate(d){
        var gb = Math.round((d-ks91.dmin)*scale);
        return 'rgb(100, ' + gb + ', ' + gb + ')';
    }
    function reverse(x){
        return x/scale+ks91.dmin;
    }

    function updateField(f){
        var altaz = altAzToXY_backwards(f.alt, f.az);
        color = translate(f.delta)

        // console.log("plotting", f.alt, color);
        drawSky(ctx, x_0-altaz[0], y_0+altaz[1], color);
    }

    colorBar(ctx, reverse);

    for(i=0;i<ks91.skies.length;i++){
        updateField(ks91.skies[i]);
    }
    field(ctx, ks91.falt, ks91.faz)
    drawGrid(ctx);
    moon(ctx, ks91.malt, ks91.maz);
    annotate(ctx, ks91.time, ks91.phase, ks91.falt, ks91.faz);
    return ctx
}

function reRenderFieldBrightness(time){
    for(j=0;j<allSkies.length;j++){
        if(allSkies[j].time == time){
            renderFieldBrightness(allSkies[j])
        }
    }
}
