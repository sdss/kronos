$(function () {
    $('#apg2Nmetrics').highcharts({
        chart: { zoomType: 'x' },
        title: { text: 'APOGEE-2N', x: -20 },
        xAxis: { min: 56900, max: 59031, title: { text: 'MJD' } },
        yAxis: { title: { text: 'Number of Visits' }, min: 0, plotLines: [{ value: 0, width: 1, color: '#808080' }] },
        tooltip: { crosshairs: true, shared: true },
        series: [{ name: 'Projected Baseline', data: [{% for p in baselines %}[{{ p[0] }},{{ p[1] }}],{% endfor %}], color: '#b7b7b7', marker: { radius: 0.1 } },
                 { name: '80% Baseline', data: [{% for p in baselines %}[{{ p[0] }},{{ 0.8 * p[1] }}],{% endfor %}], color: '#dbdbdb', visible: false },
                 { name: 'New Goal', data: [{% for p in baselines %}[{{ p[0] }},{{ p[4] }}],{% endfor %}], color: 'green', visible: true },
                 { name: 'Observed',  data: [{% for p in apg_visits_metrics %}[{{ p[0] }},{{ p[1] }}],{% endfor %}], color: '#258aec' }]
    });
});

$(function () {
    $('#apg2Smetrics').highcharts({
        chart: { zoomType: 'x' },
        title: { text: 'APOGEE-2S', x: -20 },
        xAxis: { min: 56900, max: 59031, title: { text: 'MJD' } },
        yAxis: { title: { text: 'Number of Visits' }, min: 0, plotLines: [{ value: 0, width: 1, color: '#808080' }] },
        tooltip: { crosshairs: true, shared: true },
        series: []
    });
});

$(function () {
    $('#manmetrics').highcharts({
        chart: { zoomType: 'x' },
        title: { text: 'MaNGA', x: -20 },
        xAxis: { min: 56900, max: 59031, title: { text: 'MJD' } },
        yAxis: { title: { text: 'Number of Plates' }, min: 0, plotLines: [{ value: 0, width: 1, color: '#808080' }] },
        tooltip: { crosshairs: true, shared: true },
        series: [{ name: 'Projected Baseline', data: [{% for p in baselines %}[{{ p[0] }},{{ p[2] }}],{% endfor %}], color: '#b7b7b7', marker: { radius: 0.1 } },
                 { name: '80% Baseline', data: [{% for p in baselines %}[{{ p[0] }},{{ 0.8 * p[2] }}],{% endfor %}], color: '#dbdbdb', visible: false },
                 { name: 'New Goal', data: [{% for p in baselines %}[{{ p[0] }},{{ p[5] }}],{% endfor %}], color: 'green', visible: true },
                 { name: 'Observed',  data: [{% for p in man_plates_metrics %}[{{ p[0] }},{{ p[1] }}],{% endfor %}], color: '#258aec' }]
    });
});

$(function () {
    $('#ebometrics').highcharts({
        chart: { zoomType: 'x' },
        title: { text: 'eBOSS', x: -20 },
        xAxis: { min: 56900, max: 59031, title: { text: 'MJD' } },
        yAxis: { title: { text: 'Number of Plates' }, min: 0, plotLines: [{ value: 0, width: 1, color: '#808080' }] },
        tooltip: { crosshairs: true, shared: true },
        series: [{ name: 'Projected Baseline', data: [{% for p in baselines %}[{{ p[0] }},{{ p[3] }}],{% endfor %}], color: '#b7b7b7', marker: { radius: 0.1 } },
                 { name: '80% Baseline', data: [{% for p in baselines %}[{{ p[0] }},{{ 0.8 * p[3] }}],{% endfor %}], color: '#dbdbdb', visible: false },
                 { name: 'New Goal', data: [{% for p in baselines %}[{{ p[0] }},{{ p[6] }}],{% endfor %}], color: 'green', visible: true },
                 { name: 'Observed',  data: [{% for p in ebo_plates_metrics %}[{{ p[0] }},{{ p[1] }}],{% endfor %}], color: '#258aec' }]
    });
});


