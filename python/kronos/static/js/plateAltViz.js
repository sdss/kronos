//57130 manga
//57121 error, none type has no label
//56850  friday
function ms2hours(ms){
    // convert milliseconds to decimal hours
    return ms/3600000;
}

function radians(x){
    return x*Math.PI/180;
}

function degrees(x){
    return x*180/Math.PI;
}

function getAlt(ha, dec){
    // code translated from RO.AzAltFromHADec
    // phi is angle between zenith @ apo and a given ha, dec
    // note using a dot b = cos phi
    if(observatory == "APO"){
        var siteLatRad = radians(90-32.789278) // degrees to radians
    }
    else{
        var siteLatRad = radians(90+29.0146) // degrees to radians
    };
    var haRad = radians(ha);
    var decRad = radians(90-dec);
    // convert ha/dec to cartesian
    var z = Math.sin(siteLatRad)*Math.sin(decRad)*Math.cos(haRad) + Math.cos(apoLatRad)*Math.cos(decRad);
    return 90 - degrees(Math.acos(z));
}

function jsDate(datetime){
    // return a JavascriptDate object from utc jsonified datetime obj containing date/time info
    // console.log(datetime);
    // return newDate = new Date(datetime);
    // console.log(newDate)
    return new Date(
        datetime.year,
        datetime.month,
        datetime.day,
        datetime.hour,
        datetime.minute,
        datetime.second,
        datetime.ms
    );
    // return newDate
}

function Layout(divClass, plateVizObj){
    this.setScales = function(){
        // create various d3 scales for drawing things
        // in the correct location.
        this.margin = 30;
        this.totalHeight = 300; //height of survey schedule bar
        this.rowHeight = this.totalHeight - 2*this.margin;
        this.totalWidth = $(divClass).width();
        var plateXMin = this.margin;
        var plateXMax = this.totalWidth - this.margin;
        var plateYMin = this.margin;
        var plateYMax = plateYMin + this.rowHeight; //this.totalHeight - this.margin;
        var minAltitude = 30;
        var maxAltitude = 90;

        this.timeScale = d3.time.scale() // UTC scale
            .domain([jsDate(plateVizObj.timeScale[0]), jsDate(plateVizObj.timeScale[1])])
            .rangeRound([plateXMin, plateXMax]);
        this.timeAxis = d3.svg.axis()
            .scale(this.timeScale)
            .orient("top")
            .ticks(d3.time.hour, 1)
            .tickFormat(d3.time.format("%H:%M"));

        this.altitudeScale = d3.scale.linear()
            .domain([minAltitude, maxAltitude])
            // .range([plateYMin, plateYMax]);
            .range([plateYMax, plateYMin]);
        this.altitudeAxis = d3.svg.axis()
            .scale(this.altitudeScale)
            .orient("left")
            .tickValues(d3.range(minAltitude, maxAltitude, 5)); // 5 degree marks

    }
}

function generateViz(plateVizObj, targetDiv){
    // This thing generates the visualization
    // Inputs: plateVizObj, jsonified dict (vizWindow.export())
    // targetDiv, the name of the div class in which to put the vizualization

    //initialization
    var duration = 400;
    var layout = new Layout(targetDiv, plateVizObj);
    // create the svg! everything will be appended to this object
    // create the chart area, a div with class chart must be in the html, could change this to just have d3 add the div itself...
    var initDate = Date.now();
    var tickNowTimer = null;
    var altNowTimer = null;

    function getElapsedMS(){
        // elapsed milliseconds
        return Date.now() - initDate;
    }

    function getAltNow(){
        //haInit, stale ha value to be adjusted for time elapsed
        var elapsedHours = ms2hours(getElapsedMS());
        var adjustedHA = plateVizObj.trueHA + 15*(elapsedHours);
        return String(getAlt(adjustedHA, plateVizObj.dec).toFixed(2));

    }

    function updateAlt(){
        // var currAlt = getAltNow()
        d3.select(".altNow")
            .html(getAltNow)
    }

    function drawSVG(){
        layout.setScales();
        var svgBase = d3.select(targetDiv)
            .append("svg"); //will be built upon

        var svg = svgBase
            .attr("width", layout.totalWidth)
            .attr("height", layout.totalHeight);
        // begin drawing!

        function getX(d){
            startDate = jsDate(d.utRange[0]);
            return layout.timeScale(startDate);
        }
        function getWidth(d){
            startDate = jsDate(d.utRange[0]);
            endDate = jsDate(d.utRange[1]);
            return layout.timeScale(endDate) - layout.timeScale(startDate);
        }

        function makeVerticalIndicator(yPos, xPos, color, width, opacity, className, heightFrac){
            var y2 = yPos + layout.rowHeight*heightFrac;
            svg.append("line")
                .attr("class", className)
                .attr("x1", xPos)
                .attr("y1", yPos)
                .attr("x2", xPos)
                .attr("y2", y2)
                .attr("stroke", color)
                .attr("stroke-width", width)
                .attr("opacity", opacity)
                .attr("fill", "none");
        }

        function makeTickNow(){
            svg.selectAll(".tickNow").remove();
            var elapsedMS = getElapsedMS();
            var freshDate = null;
            if(plateVizObj.currentTime != null){
                freshDate = new Date(
                    plateVizObj.currentTime.year,
                    plateVizObj.currentTime.month,
                    plateVizObj.currentTime.day,
                    plateVizObj.currentTime.hour,
                    plateVizObj.currentTime.minute,
                    plateVizObj.currentTime.second,
                    elapsedMS
                );
            }
            // don't place ticks on header rows
            var freshHA = null;
            var tickNowX = null;
            if(plateVizObj.currentHA != null){
                // account for elapsed ms (15 deg/hour)
                var elapsedHours = ms2hours(elapsedMS);
                freshHA = plateVizObj.currentHA + 15*elapsedHours;
            }
            // console.log("elapsed hours "+String(elapsedHours));
            if(freshDate != null){
                tickNowX = layout.timeScale(freshDate);
            }
            if(tickNowX != null){
                makeVerticalIndicator(layout.margin, tickNowX, "red", 2, 1, "tickNow", 1);
            }
        }

        function makeTickOverlays(minutes, color, heightFrac){
            // this could be added to main svg data binding

            // overlay stripes on each bar, indicating scale-ticks.
            // also add red current time/ha tick
            // inputs isUTC: boolean, if true, make UTC ticks, else make HA ticks

            // clean up any (potentially existing ticks before making new ones)
            // this is helpful for UTC/HA switching back and forth.
            var i,j; //iter
            var scaledIntervals = [];
            var startTime = jsDate(plateVizObj.timeScale[0]);
            var endTime = jsDate(plateVizObj.timeScale[1]);
            // 15 minute time intervals
            var timeIntervals = d3.time.minute.range(startTime, endTime, minutes); // every 15 minutes
            // turn em into pixel values
            for(i=0;i<timeIntervals.length;i++){
                scaledIntervals.push(layout.timeScale(timeIntervals[i]));
                for(j=0;j<scaledIntervals.length;j++){
                    makeVerticalIndicator(layout.margin, scaledIntervals[j], color, 0.8, 1, "tickOverlay", heightFrac);
                }
            }
        }

        function makeAxis(){
            // add the time axis, align the bottom edge with the bottom edge of the zeroth row
            var xaxis = layout.timeAxis;
            var yaxis = layout.altitudeAxis;
            svg.append("g")
                .attr("class", "xaxis")
                .attr('transform', 'translate(0,' + layout.margin + ')')
                .call(xaxis);

            svg.append("g")
                .attr("class", "yaxis")
                .attr('transform', 'translate(' + layout.margin + ', 0)')
                .call(yaxis);
        }

        function drawRow(){
            var tableFill = "white";
            var tableTxtFill = "black";
            var tableScale = layout.tableScale;
            // draw the viz windows
            var vizRects = svg.selectAll(".vizRects")
                .data(plateVizObj.vizWindows)
                .enter()
                .append("rect")
                .attr("class", "vizRects")
                .attr("y", layout.margin)
                .attr("height", layout.rowHeight)
                .attr("x", getX)
                .attr("width", getWidth)
                .attr("fill", function(d){return d.fill})
                .attr("opacity", function(d){return d.opacity})
                .attr("stroke", "none")
                .attr("rx", function(d){return d.rx})
                .attr("ry", function(d){return d.ry});
        }

        function drawAltitude(){
            // svg.selectAll(".altPts").remove();
            svg.selectAll(".altPts")
                .data(plateVizObj.altitudePoints)
                .enter()
                .append("circle")
                .attr("class", "altPts")
                .attr("r", 4)
                .attr("cx", function(d) {return layout.timeScale(jsDate(d.x));})
                .attr("cy", function(d) {return layout.altitudeScale(d.y);})
                .attr("fill", "black");

            var lineFunction = d3.svg.line()
                .x(function(d) { return layout.timeScale(jsDate(d.x)); })
                .y(function(d) { return layout.altitudeScale(d.y); })
                .interpolate("monotone");

            svg.append("path")
                .attr("d", lineFunction(plateVizObj.altitudePath))
                .attr("stroke", "black")
                .attr("opacity", 0.75)
                .attr("stroke-width", 2)
                .attr("fill", "none");

        }

        drawRow();
        svg.selectAll(".tickOverlay").remove();
        makeTickOverlays(15, "white", 0.25/2.0);
        makeTickOverlays(30, "white", 0.5/2.0);
        makeTickOverlays(60, "white", 1.0/2.0);
        makeAxis();
        makeTickNow();
        drawAltitude();
        // start tick timer
        // first clear any potentially existing one
        if(tickNowTimer != null){
            clearInterval(tickNowTimer);
        }
        tickNowTimer = setInterval(makeTickNow, 5000); // every 5 seconds
        if(altNowTimer != null){
            clearInterval(altNowTimer)
        }
        altNowTimer = setInterval(updateAlt, 500);
        //d3.timer.flush();
        // d3.timer(makeTickNow); // could look into using setInterval instead
    }

    function redrawSVG(){
        var i //iter
        if(altNowTimer != null){
            clearInterval(altNowTimer);
        }
        d3.select(targetDiv).select("svg").remove();
        drawSVG();
    }

    drawSVG();
    // start timer for real time red bar, update once a second (every 1000 ms)
    $( window ).on("resize", redrawSVG);
}
