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
    // var apoLatRad = radians(90-32.789278); // degrees to radians
    // var haRad = radians(ha);
    // var decRad = radians(90-dec);
    // // convert ha/dec to cartesian
    // var z = Math.sin(apoLatRad)*Math.sin(decRad)*Math.cos(haRad) + Math.cos(apoLatRad)*Math.cos(decRad);
    // return 90 - degrees(Math.acos(z));
    return getAltAz(ha, dec)[0]
}

function getAltAz(ha, dec){
    if(observatory == "APO"){
        var lat = radians(90-32.789278) // degrees to radians
    }
    else{
        var lat = radians(90+29.0146) // degrees to radians
    };
    var haRad = radians(ha);
    var decRad = radians(dec);
    // convert ha/dec to cartesian
    var sinalt = Math.sin(lat)*Math.sin(decRad) + Math.cos(lat)*Math.cos(decRad)*Math.cos(haRad);
    var alt = Math.asin(sinalt);
    var cosaz = (Math.sin(decRad)-Math.sin(alt)*Math.sin(lat))/(Math.cos(alt)*Math.cos(lat));
    if(Math.sin(haRad) < 0){
        var az = degrees(Math.acos(cosaz))
    }
    else{
        var az = 360 - degrees(Math.acos(cosaz))
    }
    return [degrees(alt), az];
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

function Layout(divClass, vizObj, isSurveyPlanning){
    this.showOnlySelected = false;
    this.rowHeight = 35; //height of survey schedule bar
    if (isSurveyPlanning){
        this.tableWidth = 500;
    }
    else{
        this.tableWidth = 300; // width of info bar/table
    }
    this.rowBuffer = 3; // buffer table and viz bar
    this.margin = 30; // empty space around edge
    var indent = 10; // indent for expanded rows
    // this.setScales();

    this.setScales = function(){
        // create various d3 scales for drawing things
        // in the correct location.
        this.totalWidth = $(divClass).width();
        var plateBarMin = this.margin + this.tableWidth + this.rowBuffer;
        var plateBarMax = this.totalWidth - this.margin;
        var tableMin = this.margin;
        var tableMax = this.margin + this.tableWidth

        this.timeScale = d3.time.scale() // UTC scale
            .domain([jsDate(vizObj.timeScale[0]), jsDate(vizObj.timeScale[1])])
            .rangeRound([plateBarMin, plateBarMax]);
        this.timeAxis = d3.svg.axis()
            .scale(this.timeScale)
            .orient("top")
            .ticks(d3.time.hour, 1)
            .tickFormat(d3.time.format("%H:%M"));

        this.hourAngleScale = d3.scale.linear()
            .domain([vizObj.haScale[0], vizObj.haScale[1]])
            .range([plateBarMin, plateBarMax]);
        this.hourAngleAxis = d3.svg.axis()
            .scale(this.hourAngleScale)
            .orient("top")
            .tickValues(d3.range(vizObj.haScale[0], vizObj.haScale[1]+15, 15));

        this.tableScale = d3.scale.ordinal() // for creating the table next to the bars
            .domain(d3.range(vizObj.nTableItems))
            .rangeRoundBands([tableMin, tableMax], 0, 0.2); // no padding between drawing boxes, 5 outside
        if(vizObj.hasChild){
            this.childTableScale = d3.scale.ordinal() // for creating the indented table next to the bars
                // .domain(d3.range(vizObj.tableItems.length)) // keeps child spacing equal to parents spacing
                .domain(d3.range(vizObj.nChildTableItems))
                .rangeRoundBands([tableMin+indent, tableMax], 0, 0.2); // no padding between draw
        }
    }

    this.setRows = function(dataset){
        // sets y value for each item in dataset
        var y = this.margin;
        var i,j; //iter
        var childBuffer = [];
        for(i=0;i<dataset.length;i++){
            var showChildren = dataset[i].expanded;
            var hideRow = this.showOnlySelected && !dataset[i].selected && !dataset[i].isHeader;
            if(hideRow){
                dataset[i].yValue = this.margin;
            }
            else{
                dataset[i].yValue = y;
                y = y + this.rowBuffer + this.rowHeight;
            }
            // note that children preceed parent in dataset
            // if(dataset[i].isChild){
            //     // place it in the buffer until its parent is reached
            //     // the state of the parent determines the y location of the child
            //     childBuffer.push(dataset[i]);
            // }

            // else{
            //     var showChildren = dataset[i].expanded;
            //     var hideRow = this.showOnlySelected && !dataset[i].selected && !dataset[i].isHeader;
            //     if(hideRow){
            //         dataset[i].yValue = this.margin;
            //     }
            //     else{
            //         dataset[i].yValue = y;
            //         y = y + this.rowBuffer + this.rowHeight;
            //     }
            //     //is anything in the buffer?
            //     if(childBuffer.length > 0){
            //         // console.log(childBuffer)
            //         //children in buffer need y values to be set, what is the parent's state?
            //         if(dataset[i].childViz.plateRows.length != childBuffer.length){
            //             // paranioa make sure the numbers match up, could add more tests.
            //             alert("Bug in JS, please tell Conor so he can search and destroy!");
            //         }
            //         // this is the only place we decide where to show children
            //         // can control vis of children here
            //         if(showChildren && !hideRow){
            //             //children are displayed
            //             for(j=0;j<childBuffer.length;j++){
            //                 childBuffer[j].yValue = y;
            //                 y = y + this.rowBuffer + this.rowHeight // increment y
            //                 // show on cloudcam as well
            //                 childBuffer[j].current = true
            //             }
            //         }
            //         else{
            //             // not expanded children not displayed, give them same y value
            //             // as parent.  Because they are drawn first (and the parent overtop)
            //             // they will not be visible.
            //             for(j=0;j<childBuffer.length;j++){
            //                 childBuffer[j].yValue = dataset[i].yValue; // same y as parent
            //                 // don't show on cloudcam
            //                 childBuffer[j].current = false
            //             }
            //         }
            //         // clear the child buffer
            //         childBuffer = [];
            //     }
            // }
        }
        this.totalHeight = y + this.margin;
    }
}

function generateViz(vizObj, targetDiv, backups){
    // This thing generates the visualization
    // Inputs: vizObj, jsonified dict (vizWindow.export())
    // targetDiv, the name of the div class in which to put the vizualization

    // reset the div every time this is called
    d3.select(targetDiv).html('<div class="row"><div class = "col-md-8"></div></div>')
    //initialization
    var duration = 400;
    var layout = new Layout(targetDiv, vizObj);
    dataset = vizObj.allRows;
    var selectedField = null;
    // layout.setRows(dataset); // set y values in dataset elements
    // create the svg! everything will be appended to this object
    // create the chart area, a div with class chart must be in the html, could change this to just have d3 add the div itself...
    var utcON = true; // initialize showing utc values (rather than HA)
    var initDate = Date.now();
    var tickNowTimer = null;
    var altNowTimers = [];

    var colorScale = chroma.scale("Viridis");
    var numPoints = dataset.length - 1
    var onSky = false
    for(i=0;i<dataset.length;i++){
            dataset[i].show = false
            dataset[i].id = i //so we can keep track when iterating through rows
            if(dataset[i].isChild){
                var out_of_seq = i*10/numPoints%1
                dataset[i].color = colorScale(out_of_seq).hex()
            }
            else{
                dataset[i].color = colorScale(i/numPoints).hex()
            }
            // for(j=0;j<dataset[i].vizWindows.length;j++){
            //     if(dataset[i].vizWindows[j].primary){
            //         dataset[i].vizWindows[j].fill = dataset[i].color
            //         // dataset[i].color = dataset[i].vizWindows[j].fill
            //     }
            // }
            if(jsDate(dataset[i].timeScale[0]) < initDate && jsDate(dataset[i].timeScale[1]) > initDate){
                dataset[i].current = true
                onSky = true
                // if(!dataset[i].isChild){
                //     dataset[i].expanded = true
                // }
            }
        }

    if(!onSky){
        for(i=0;i<dataset.length;i++){
            if(dataset[i].isHeader){
                continue
            }
            dataset[i].current = true
            if(!dataset[i].isChild){
                // dataset[i].expanded = true
                // once we hit the first non-child row we're done with the first block
                break
            }
        }
    }

    layout.setRows(dataset); // set y values in dataset elements

    function getElapsedMS(){
        // elapsed milliseconds
        return Date.now() - initDate;
    }

    function getAltNow(haInit, dec){
        //haInit, stale ha value to be adjusted for time elapsed
        var elapsedHours = ms2hours(getElapsedMS());
        var adjustedHA = haInit + 15*(elapsedHours);
        return getAlt(adjustedHA, dec);
    }

    function drawSVG(){
        layout.setScales();
        var svgBase = d3.select(targetDiv)
            .append("svg"); //will be built upon
        var svg = svgBase
            .attr("width", layout.totalWidth)
            .attr("height", layout.totalHeight);
        // begin drawing!

        var svgRow = svg.selectAll(".svgRow")
            .data(dataset)
            .enter()
            .append("g")
            .attr("class", "svgRow");

        function getX(d){
            if(utcON){
                // eventually store these
                // computations ahead of time
                startDate = jsDate(d.utRange[0]);
                return layout.timeScale(startDate);
            }
            else{
                return layout.hourAngleScale(d.haRange[0]);
            }
        }
        function getWidth(d){
            if(utcON){
                startDate = jsDate(d.utRange[0]);
                endDate = jsDate(d.utRange[1]);
                return layout.timeScale(endDate) - layout.timeScale(startDate);
            }
            else{
                startHa = d.haRange[0];
                endHa = d.haRange[1];
                return layout.hourAngleScale(endHa) - layout.hourAngleScale(startHa)
            }
        }

        function getTriangleVertices(yPos, isExpanded){
            // return a string to be used by points field in svg polygon
            var alpha = (layout.margin - 2*layout.rowBuffer)/2;  // x dir contracted
            var beta = (layout.rowHeight - 2*layout.rowBuffer)/2; // x dir contracted
            var yMid = yPos + 0.5*layout.rowHeight;
            var xMid = layout.margin/2;
            var pt1, pt2, pt3;
            if(isExpanded==false){
                pt1 = [String(layout.rowBuffer), String(yMid-beta)].join();
                pt2 = [String(layout.margin-layout.rowBuffer), String(yMid)].join();
                pt3 = [String(layout.rowBuffer), String(yMid+beta)].join();
            }
            else{
                // rotated 90 degrees to right
                pt1 = [String(xMid+beta), String(yMid-alpha)].join();
                pt2 = [String(xMid), String(yMid+alpha)].join();
                pt3 = [String(xMid - beta), String(yMid-alpha)].join();
            }
            return [pt1, pt2, pt3, pt1].join(" ");
        }

        function makeVerticalIndicator(yPos, xPos, color, width, opacity, className, height){
            var y2 = yPos + layout.rowHeight*height;
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
            var lastYValue = -1;
            var elapsedMS = getElapsedMS();
            var freshDate = null;
            if(dataset[0].currentTime != null){
                freshDate = new Date(
                    dataset[0].currentTime.year,
                    dataset[0].currentTime.month,
                    dataset[0].currentTime.day,
                    dataset[0].currentTime.hour,
                    dataset[0].currentTime.minute,
                    dataset[0].currentTime.second,
                    elapsedMS
                );
            }
            for (i=0;i<dataset.length;i++){
                // don't place ticks on header rows
                if(dataset[i].isHeader){
                    continue;
                }
                if(dataset[i].yValue==lastYValue){
                    // overlapping rows, don't draw again
                    continue;
                }
                var freshHA = null;
                var tickNowX = null;
                if(dataset[i].currentHA != null){
                    // account for elapsed ms (15 deg/hour)
                    var elapsedHours = ms2hours(elapsedMS);
                    freshHA = dataset[i].currentHA + 15*elapsedHours;
                }
                // console.log("elapsed hours "+String(elapsedHours));
                if(utcON && freshDate != null){
                    tickNowX = layout.timeScale(freshDate);
                }
                else if(!utcON && freshHA != null){
                    tickNowX = layout.hourAngleScale(freshHA);
                }
                if(tickNowX != null){
                    makeVerticalIndicator(dataset[i].yValue, tickNowX, "red", 2, 1, "tickNow", 1);
                }
                lastYValue = dataset[i].yValue;
            }
        }

        function makeTickOverlays(){
            // this could be added to main svg data binding

            // overlay stripes on each bar, indicating scale-ticks.
            // also add red current time/ha tick
            // inputs isUTC: boolean, if true, make UTC ticks, else make HA ticks

            // clean up any (potentially existing ticks before making new ones)
            // this is helpful for UTC/HA switching back and forth.
            svg.selectAll(".tickOverlay").remove();
            var i,j; //iter
            var scaledIntervals = [];
            var scaledIntervalsHours = [];
            var startTime = jsDate(vizObj.timeScale[0]);
            var endTime = jsDate(vizObj.timeScale[1]);
            var startHA = vizObj.haScale[0];
            var endHA = vizObj.haScale[1];
            if(utcON){
                // 15 minute time intervals
                var timeIntervals = d3.time.minute.range(startTime, endTime, 15); // every 15 minutes
                var timeIntervalsHours = d3.time.minute.range(startTime, endTime, 60); // every 15 minutes
                // turn em into pixel values
                for(i=0;i<timeIntervals.length;i++){
                    scaledIntervals.push(layout.timeScale(timeIntervals[i]));
                }
                for(i=0;i<timeIntervalsHours.length;i++){
                    scaledIntervalsHours.push(layout.timeScale(timeIntervalsHours[i]));
                }
            }
            else{
                //5 degree intervals
                var angleIntervals = d3.range(startHA, endHA, 5);
                // turn em into pixel values
                for(i=0;i<angleIntervals.length;i++){
                    scaledIntervals.push(layout.hourAngleScale(angleIntervals[i]));
                }
            }
            var lastYValue = -1;
            for (i=0;i<dataset.length;i++){
                // don't place ticks on header rows
                if(dataset[i].isHeader){
                    continue;
                }
                // don't plate tics on hidden rows (eg collapsed)
                if(layout.showOnlySelected && !dataset[i].selected){
                    continue;
                }
                if(dataset[i].yValue==lastYValue){
                    // overlapping rows, don't draw again
                    continue;
                }
                for(j=0;j<scaledIntervals.length;j++){
                    makeVerticalIndicator(dataset[i].yValue, scaledIntervals[j], "white", 0.8, 1, "tickOverlay", 0.5);
                }
                for(j=0;j<scaledIntervalsHours.length;j++){
                    makeVerticalIndicator(dataset[i].yValue, scaledIntervalsHours[j], "white", 1, 1, "tickOverlay", 1);
                }
                lastYValue = dataset[i].yValue;
            }
        }

        function makeAxis(){
            // add the time axis, align the bottom edge with the bottom edge of the zeroth row
            var axis;
            if(utcON){
                axis = layout.timeAxis;
            }
            else{
                axis = layout.hourAngleAxis;
            }
            svg.append("g")
                .attr("class", "xaxis")
                .attr('transform', 'translate(0, ' + (layout.margin + layout.rowHeight) + ')')
                .call(axis);
        }

        function makeToggleScaleButton(){
            var y = 0;
            var height = layout.margin-layout.rowBuffer;
            var x = layout.margin+2*layout.rowBuffer+layout.tableWidth;
            var width = 200;
            svg
                .append("rect")
                .attr("class", "toggleRect")
                .attr("fill", "steelblue")
                .attr("stroke", "black")
                .attr("opacity", 0.7)
                .attr("rx", 5)
                .attr("ry", 5)
                .attr("y", y)
                .attr("x", x)
                .attr("width", width)
                .attr("height", height);
            svg
                .append("text")
                .text("Click to toggle UTC <--> HA")
                .attr("class", "toggleTxt")
                .attr("y", (y + 0.65*height))
                .attr("x", x + 0.5*width)
                .attr("font-family", "sans-serif")
                .attr("font-size", "14px")
                .attr("font-weight", "bold")
                .attr("fill", "white")
                // .attr("stroke", "black")
                .attr("stroke-width", "1px")
                .attr("text-anchor", "middle");
            svg // overlay an invisible rectangle for clicking
                .append("rect")
                .attr("class", "invisRect")
                .attr("fill", "white")
                .attr("opacity", 0)
                .attr("rx", 5)
                .attr("ry", 5)
                .attr("y", y)
                .attr("x", x)
                .attr("width", width)
                .attr("height", height)
                .on("mouseover", function(){
                    d3.select(this)
                        .attr("cursor", "pointer");
                    svg.select(".toggleRect")
                        .attr("fill", "orange");
                })
                .on("mouseout", function(){
                    d3.select(this)
                        .attr("cursor", "none");
                    svg.select(".toggleRect")
                        .attr("fill", "steelblue");
                })
                .on("click", function(){
                    utcON = !utcON;
                    var newAxis;
                    if(utcON){
                        newAxis = layout.timeAxis;
                        }
                    else{
                        newAxis = layout.hourAngleAxis;
                        }
                    svg.selectAll(".svgRow")
                        .selectAll(".vizRects")
                        .transition()
                        .duration(duration)
                        .attr("x", getX)
                        .attr("width", getWidth);
                    svg.selectAll(".svgRow")
                        .selectAll(".scheduleTxt")
                        .transition()
                        .duration(duration)
                        .text(function(d){
                            // is it visible with ha or utc toggled?
                            if(utcON && d.showUT){
                                return d.text;
                            }
                            else if(!utcON && d.showHA)
                            {
                                return d.text;
                            }
                            else{
                                return ""
                            }
                        })
                        .attr("x", function(d){
                            var x = getX(d);
                            var width = getWidth(d);
                            return x + 0.5*width;
                        });
                    svg.select(".xaxis")
                        .transition()
                        .call(newAxis);
                    makeTickOverlays();
                    makeTickNow();
                });
        }

        function makeTextButton(){
            var y = 0;
            var height = layout.margin-layout.rowBuffer;
            var width = 200;
            var x = width + layout.margin+2*layout.rowBuffer+layout.tableWidth;
            svg
                .append("rect")
                .attr("class", "textRect")
                .attr("fill", "steelblue")
                .attr("stroke", "black")
                .attr("opacity", 0.7)
                .attr("rx", 5)
                .attr("ry", 5)
                .attr("y", y)
                .attr("x", x)
                .attr("width", width)
                .attr("height", height);
            svg
                .append("text")
                .text("Selected Plate Text")
                .attr("class", "toggleTxt")
                .attr("y", (y + 0.65*height))
                .attr("x", x + 0.5*width)
                .attr("font-family", "sans-serif")
                .attr("font-size", "14px")
                .attr("font-weight", "bold")
                .attr("fill", "white")
                // .attr("stroke", "black")
                .attr("stroke-width", "1px")
                .attr("text-anchor", "middle");
            svg // overlay an invisible rectangle for clicking
                .append("rect")
                .attr("class", "invisRect")
                .attr("fill", "white")
                .attr("opacity", 0)
                .attr("rx", 5)
                .attr("ry", 5)
                .attr("y", y)
                .attr("x", x)
                .attr("width", width)
                .attr("height", height)
                .on("mouseover", function(){
                    d3.select(this)
                        .attr("cursor", "pointer");
                    svg.select(".textRect")
                        .attr("fill", "orange");
                })
                .on("mouseout", function(){
                    d3.select(this)
                        .attr("cursor", "none");
                    svg.select(".textRect")
                        .attr("fill", "steelblue");
                })
                .on("click", function(){
                    var nSelected = 0;
                    var selectedPlates = "--Selected Plates--<br>(Cart) --> Plate ID:<br>";
                    svgRow
                        .each(function(row, i){
                            if(row.selected){
                                var cart = row.tableItems[0];
                                if (cart == null){
                                    cart = "None";
                                }
                                selectedPlates += " (" + cart + ") --> " + row.tableItems[1] + "<br>"
                                // get a range of x's at which to print "special!"
                            }
                        });
                    var newWindow = window.open("", "Selected Plates", "width=500, height=500, left=400, top=400");
                    newWindow.document.write(selectedPlates);
                    // alert(selectedPlates);
                });
        }

        function makeClickFilterButton(){
            var y = 0;
            var height = layout.margin-layout.rowBuffer;
            var x = layout.margin+2*layout.rowBuffer+layout.tableWidth;
            var width = 200;
            svg
                .append("rect")
                .attr("class", "toggleRect")
                .attr("fill", "steelblue")
                .attr("stroke", "black")
                .attr("opacity", 0.7)
                .attr("rx", 5)
                .attr("ry", 5)
                .attr("y", y)
                .attr("x", x)
                .attr("width", width)
                .attr("height", height);
            svg
                .append("text")
                .text("Compress/Expand")
                .attr("class", "toggleTxt")
                .attr("y", (y + 0.65*height))
                .attr("x", x + 0.5*width)
                .attr("font-family", "sans-serif")
                .attr("font-size", "14px")
                .attr("font-weight", "bold")
                .attr("fill", "white")
                // .attr("stroke", "black")
                .attr("stroke-width", "1px")
                .attr("text-anchor", "middle");
            svg // overlay an invisible rectangle for clicking
                .append("rect")
                .attr("class", "invisRect")
                .attr("fill", "white")
                .attr("opacity", 0)
                .attr("rx", 5)
                .attr("ry", 5)
                .attr("y", y)
                .attr("x", x)
                .attr("width", width)
                .attr("height", height)
                .on("mouseover", function(){
                    d3.select(this)
                        .attr("cursor", "pointer");
                    svg.select(".toggleRect")
                        .attr("fill", "orange");
                })
                .on("mouseout", function(){
                    d3.select(this)
                        .attr("cursor", "none");
                    svg.select(".toggleRect")
                        .attr("fill", "steelblue");
                })
                .on("click", function(){
                    layout.showOnlySelected = !layout.showOnlySelected;
                    // next adjust all y rows!
                    layout.setRows(dataset);

                    svg.transition()
                        .duration(duration)
                        .attr("height", layout.totalHeight)

                    svgRow.each(function(row, i){
                        // dont touch header row
                        if(i==0){
                            return;
                        }
                        d3.select(this)
                            .selectAll("rect")
                            .transition()
                            .duration(duration)
                            .attr("y", row.yValue);

                        d3.select(this)
                            .selectAll("text")
                            .transition()
                            .duration(duration)
                            .attr("y", row.yValue+0.5*layout.rowHeight);

                        d3.select(this)
                            .transition()
                            .duration(duration)
                            .attr("opacity", function(){
                                if(layout.showOnlySelected && !row.selected){
                                    return "0"
                                }
                                else{
                                    return "1"
                                }
                            });
                    });
                    makeTickOverlays();
                    makeTickNow();
                });
        }

        svgRow
            .each(function(row, i){
                // console.log(row)
                var tableFill = "white";
                var tableTxtFill = "black";
                var tableScale
                if(row.isChild){
                    tableScale = layout.childTableScale;
                }
                else{
                    tableScale = layout.tableScale;
                }

                // draw the viz windows
                var vizRects = d3.select(this)
                    .selectAll(".vizRects")
                    .data(row.vizWindows)
                        .enter()
                        .append("rect")
                        .attr("class", "vizRects")
                        .attr("y", row.yValue)
                        .attr("height", layout.rowHeight)
                        .attr("x", getX)
                        .attr("width", getWidth)
                        .attr("fill", function(d){return d.fill})
                        .attr("opacity", function(d){return d.opacity})
                        .attr("stroke", "none")
                        .attr("rx", function(d){return d.rx})
                        .attr("ry", function(d){return d.ry});

                if(row.isHeader){
                    tableFill = "gray";
                    tableTxtFill = "white";
                    var schedTxt = d3.select(this)
                        .selectAll(".scheduleTxt")
                        .data(row.vizWindows)
                        .enter()
                        .append("text")
                        .text(function(d){
                            // is it visible with ha or utc toggled?
                            if(utcON && d.showUT){
                                return d.text;
                            }
                            else if(!utcON && d.showHA)
                            {
                                return d.text;
                            }
                            else{
                                return ""
                            }
                        })
                        .attr("class", "scheduleTxt")
                        .attr("y", row.yValue + 0.4*layout.rowHeight)
                        .attr("x", function(d){
                            var x = getX(d);
                            var width = getWidth(d);
                            return x + 0.5*width;
                        })
                        .attr("font-family", "sans-serif")
                        .attr("font-size", "12px")
                        .attr("font-weight", "bold")
                        .attr("fill", "black")
                        // .attr("stroke", "black")
                        .attr("stroke-width", "1px")
                        .attr("text-anchor", "middle");
                }

                // table stuff
                // draw the rectangles
                var tableRects = d3.select(this)
                    .selectAll(".tableRects")
                    .data(row.tableItems)
                    .enter()
                    .append("rect")
                    .attr("class", "tableRects")
                    .attr("height", layout.rowHeight)
                    .attr("width", tableScale.rangeBand())
                    .attr("x", function(d,i){
                        return tableScale(i);
                    })
                    .attr("y", row.yValue)
                    .attr("fill", tableFill)
                    .attr("stroke", "black");

                // populate the table to the rectangles
                var tableItems = d3.select(this)
                    .selectAll(".tableItems")
                    .data(row.tableItems)
                    .enter()
                    .append("text")
                    .text(function(d, i){
                        var thisText = d3.select(this);
                        if(i==2 && !row.isChild && row.isHeader && row.setCurrent){
                            return "alt";
                        }
                        if(i==2 && !row.isHeader && row.setCurrent){
                            // this is the current alt value
                            // calculate it now
                            function getCurrAlt(){
                                var currAlt = getAltNow(row.trueHA, row.dec);
                                var altAz = getAltAz(row.trueHA, row.dec);
                                row.alt = altAz[0]
                                row.az = altAz[1]
                                return String(currAlt.toFixed(2));
                            }
                            function updateAlt(){
                                thisText
                                    .text(getCurrAlt);
                            }
                            var altNowTimer = setInterval(updateAlt, 500);
                            altNowTimers.push(altNowTimer);
                            return getCurrAlt();
                        }
                        // if(i==5 && !row.isChild && row.isHeader){
                        //     return "utc-mid";
                        // }
                        else{
                            return d;
                        }
                    })
                    .attr("class", "tableItems")
                    .attr("x", function(d,i){
                        return tableScale(i) + 0.5*tableScale.rangeBand();
                    })
                    .attr("y", row.yValue + 0.5*layout.rowHeight)
                    .attr("font-family","sans-serif")
                    .attr("font-size", function(d, i){
                        if(row.isHeader){
                            return "14px";
                        }
                        else{
                            return "12px";
                        }
                    })
                    .attr("font-weight","bold")
                    .attr("fill", function(d,i){
                        if(i == 0 && !row.isHeader){
                            return "blue";
                        }
                        else{
                            return tableTxtFill;
                        }
                    })
                    .attr("text-anchor", "middle")
                    .attr("dominant-baseline", "central")
                    .on("mouseover", function(d, i){
                        var isPlateID = i==0 && !row.isHeader;
                        if(isPlateID){
                            d3.select(this)
                                .attr("fill", "orange")
                                .attr("cursor", "pointer");
                        }
                    })
                    .on("mouseout", function(d, i){
                        var isPlateID = i==0 && !row.isHeader;
                        if(isPlateID){
                            d3.select(this)
                                .attr("fill", "blue")
                                .attr("cursor", "none");
                        }
                    })
                    .on("click", function(d, i){
                        var isPlateID = i==0 && !row.isHeader;
                        if(isPlateID){
                            var url = "fieldDetail.html?fieldID="+d+"&mjd="+row.mjd_start.toFixed(2);
                            d3.select(this)
                                .attr("fill", "blue");
                            window.open (url,'_self',false);
                        }
                    });


                // add a triangle for expanding contracting
                // if(row.hasChild){
                //     var svgTriangle = d3.select(this)
                //         .append("polygon")
                //         .attr("class", "triangle")
                //         .attr("points", getTriangleVertices(row.yValue, row.expanded))
                //         .attr("fill", "black")
                //         .on("mouseover", function(){
                //             d3.select(this)
                //                 .attr("fill", "orange")
                //                 .attr("cursor", "pointer");
                //         })
                //         .on("mouseout", function(){
                //             d3.select(this)
                //                 .attr("fill", "black")
                //                 .attr("cursor", "none");
                //         })
                //         .on("click", function(){
                //             row.expanded = !row.expanded;

                //             // next adjust all y rows!
                //             // console.log(row.id, dataset[row.id+4].yValue, row.yValue)
                //             layout.setRows(dataset);
                //             // console.log(row.id, dataset[row.id+4].yValue, row.yValue)

                //             d3.select(this)
                //                 .transition()
                //                 .duration(duration)
                //                 .attr("points", getTriangleVertices(row.yValue, row.expanded));

                //             // // next adjust all y rows!
                //             // layout.setRows(dataset);

                //             svg.transition()
                //                 .duration(duration)
                //                 .attr("height", layout.totalHeight)

                //             svgRow.each(function(row, i){
                //                 // dont touch header row
                //                 if(i==0){
                //                     return;
                //                 }
                //                 d3.select(this)
                //                     .selectAll("polygon")
                //                     .transition()
                //                     .duration(duration)
                //                     .attr("points", getTriangleVertices(row.yValue, row.expanded));
                //                 d3.select(this)
                //                     .selectAll("rect")
                //                     .transition()
                //                     .duration(duration)
                //                     .attr("y", row.yValue);

                //                 d3.select(this)
                //                     .selectAll("text")
                //                     .transition()
                //                     .duration(duration)
                //                     .attr("y", row.yValue+0.5*layout.rowHeight);
                //             });
                //             makeTickOverlays();
                //             makeTickNow();
                //             renderCloudCam(dataset);
                //         });
                // }

                //allow row clickability for filtering
                // !row.setCurrent &&  don't know why this would be needed..
                if(!row.isHeader){// && !row.isChild){
                    // var xStart = layout.margin + layout.tableWidth + 2*layout.rowBuffer;
                    // var xEnd = layout.totalWidth - layout.margin;
                    // var xVals = d3.range(xStart, xEnd, (xEnd-xStart)/5);
                    function drawSelectText(){
                        var xStart = layout.margin + layout.tableWidth + 2*layout.rowBuffer;
                        // var xEnd = layout.totalWidth - layout.margin;
                        // var xVals = d3.range(xStart, xEnd, (xEnd-xStart)/5);
                        
                        // console.log("drawing select!")
                        // console.log(this.parentNode)

                        d3.select(this.parentNode)
                            // .selectAll(".selectedTxt")
                            // .data(xVals)
                            // .enter()
                            .append("text")
                            .text("SELECTED")
                            .attr("class", "selectedTxt")
                            .attr("y", row.yValue + 0.7*layout.rowHeight)
                            .attr("x", xStart)//function(d){return d;})
                            .attr("font-family", "sans-serif")
                            .attr("font-size", "22px")
                            .attr("font-weight", "bold")
                            .attr("fill", "White")
                            .attr("opacity", "1")
                            .attr("stroke-width", "0.5px")
                            .attr("stroke", "black")
                            .attr("text-anchor", "left");
                    }
                    function toggleSelected(){
                        svg.selectAll(".selectedTxt").remove();
                        row.selected = !row.selected;
                        // console.log(row.fieldID, row.selected);
                        // console.log(d3.select(this.parentNode));
                        let toggleOff = true;
                        if(row.selected){
                            toggleOff = false;
                            for(i=0;i<dataset.length;i++){
                                if(dataset[i].id != row.id){
                                    dataset[i].selected = false
                                }
                            }
                            selectedField = row.fieldID
                            drawSelectText();
                        }
                        else{
                            d3.select(this.parentNode)
                                .selectAll(".selectedTxt")
                                .remove();
                        }
                        row.redraw(row);
                        renderCloudCam(dataset, backups);
                        // makeSendFieldButton();
                        var fields = document.getElementsByClassName("queue-field");
                        for (i=0;i<fields.length;i++){
                            if(fields[i].classList.contains("field-"+selectedField) && !toggleOff){
                                fields[i].style.backgroundColor = "rgba(224, 45, 45, 1)";
                            }
                            else{
                                fields[i].style.backgroundColor = "rgba(0, 0, 0, 0)";
                            }
                        }
                    }
                    if(row.selected){
                        drawSelectText();
                    }
                    d3.select(this)
                        .selectAll(".vizRects")
                        .on("mouseover", function(d){
                            d3.select(this)
                                .attr("cursor", "pointer")
                                .attr("opacity", function(d){
                                    return d.opacity - 0.2;
                                    // return "0.8";
                                    // return parseFloat(d3.select(this).attr("opacity")) - 0.2
                                    });
                                // .attr("cursor", "pointer")
                        })
                        .on("mouseout", function(d){
                            d3.select(this)
                                .attr("cursor", "none")
                                .attr("opacity", function(d){
                                    return d.opacity;
                                    // return "1";
                                    // return parseFloat(d3.select(this).attr("opacity")) + 0.2
                                    });
                                // .attr("cursor", "none")
                            // d3.select(this)
                            //     .selectAll(".vizRects")
                            //     .attr("opacity", "0.5")
                        })
                        .on("click", toggleSelected);
                }
                for(i=0;i<dataset.length;i++){
                    if(dataset[i].id == row.id){
                        // console.log(i + " setting toggle selected for " + dataset[i].id )
                        dataset[i].toggleSelected = toggleSelected;
                        // console.log(i, dataset[i].fieldID, dataset[i].toggleSelected)
                    }
                }

            });
        makeTickOverlays();
        makeAxis();
        makeTickNow();
        // makeSendFieldButton();
        if (vizObj.setCurrent){
            makeToggleScaleButton();
        }
        else {
            makeClickFilterButton();
            makeTextButton();
        }
        // start tick timer
        // first clear any potentially existing one
        if(tickNowTimer != null){
            clearInterval(tickNowTimer);
        }
        tickNowTimer = setInterval(makeTickNow, 5000); // every 5 seconds
        //d3.timer.flush();
        // d3.timer(makeTickNow); // could look into using setInterval instead
    }
    function redrawSVG(){
        var i //iter
        var nTimers = altNowTimers.length;
        for(i=0;i<nTimers;i++){
            clearInterval(altNowTimers[i]);
        }
        // pop them off the list
        for(i=0;i<nTimers;i++){
            altNowTimers.pop();
        }
        d3.select(targetDiv).select("svg").remove();
        renderCloudCam(dataset, backups);
        drawSVG();
    }
    drawSVG();
    if (showCloudCam){
        renderCloudCam(dataset, backups);
    }
    // start timer for real time red bar, update once a second (every 1000 ms)
    $( window ).on("resize", redrawSVG);

    // return redrawSVG
}
