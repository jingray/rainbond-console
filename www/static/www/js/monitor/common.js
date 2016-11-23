
function GetOption(optitle) {
    var option = {
        title: {
            text: optitle,
            subtext: 'dataZoom支持'
        },
        toolbox: {
            show: true,
            feature: {
                mark: { show: true },
                dataView: { show: true, readOnly: false },
                restore: { show: true },
                saveAsImage: { show: true }
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                var date = new Date(params.value[0]);
                data = date.getFullYear() + '-' +
                    (date.getMonth() + 1) + '-' +
                    date.getDate() + ' ' +
                    date.getHours() + ':' +
                    date.getMinutes();
                return data + '<br/>' +
                    params.value[1] + 'Mb, ' +
                    params.value[2];
            }
        },
        dataZoom: {
            show: true,
            start: 70
        },
        legend: {
            data: ['series1']
        },
        grid: {
            y2: 80
        },
        xAxis: [{
            type: 'time',
        }],
        yAxis: [{
            type: 'value',
            axisLabel: {
                formatter: '{value} Mb'
            }
        }],
        series: [{
            name: 'series1',
            type: 'line',
            lineStyle: {
                normal: {
                    color: '#50df9b',
                }
            },
            itemStyle: {
                normal: {
                    color: '#50df9b',
                }
            },
            data: (function() {
                var d = [];
                var len = 0;
                var now = new Date();
                var value;
                while (len++ < 200) {
                    d.push([
                        new Date(2014, 9, 1, 0, len * 10000),
                        (Math.random() * 30).toFixed(2) - 0,
                        (Math.random() * 100).toFixed(2) - 0
                    ]);
                }
                return d;
            })()
        }]
    };


    return option
}

function showMem(mem,api) {
   $.get(api).done(function(data) {
        //console.log(data)
        var d = [];
        $.each(data.data.result[0].values, function(k, v) {
                d.push([
                    parseInt(v[0]) * 1000, (parseInt(v[1]) / 1024 / 1024).toFixed(2), (Math.random() * 100).toFixed(2) - 0
                ]);
            })
            // console.log(d)
        mem.setOption({
            legend: {
                data: ["最大内存限制", "实时内存使用"]
            },
            tooltip: {
                trigger: 'item',
                formatter: function(params) {
                    var date = new Date(params.value[0]);
                    data = date.getFullYear() + '-' +
                        (date.getMonth() + 1) + '-' +
                        date.getDate() + ' ' +
                        date.getHours() + ':' +
                        date.getMinutes();
                    return data + '<br/>' +
                        params.value[1] + 'Mb, ' +
                        params.value[2];
                }
            },
            series: [{
                name: '实时内存使用',
                type: 'line',
                data: d
            }]
        })
    })
}

function showCPU(cpu, api) {
    $.get(api).done(function(data) {
        //console.log(data)
        var d = [];
        $.each(data.data.result[0].values, function(k, v) {
                d.push([
                    parseInt(v[0]) * 1000, parseFloat(v[1]).toFixed(4), (Math.random() * 100).toFixed(2) - 0
                ]);
            })
            // console.log(d)
        cpu.setOption({
            legend: {
                data: ["实时CPU使用"]
            },
            tooltip: {
                trigger: 'item',
                formatter: function(params) {
                    var date = new Date(params.value[0]);
                    data = date.getFullYear() + '-' +
                        (date.getMonth() + 1) + '-' +
                        date.getDate() + ' ' +
                        date.getHours() + ':' +
                        date.getMinutes();
                    return data + '<br/>' +
                        params.value[1] + '%, ' +
                        params.value[2];
                }
            },
            yAxis: [{
                type: 'value',
                axisLabel: {
                    formatter: '{value} %'
                }
            }],
            series: [{
                name: '实时CPU使用',
                type: 'line',
                data: d
            }]
        })
    })
}

function showFS(zfs, api) {
    $.get(api).done(function(data) {
        //console.log(data)
        var d = [];
        $.each(data.data.result[0].values, function(k, v) {
                d.push([
                    parseInt(v[0]) * 1000, (parseInt(v[1]) / 1024 / 1024).toFixed(2), (Math.random() * 100).toFixed(2) - 0
                ]);
            })
            // console.log(d)
        zfs.setOption({
            legend: {
                data: ["实时硬盘使用"]
            },
            yAxis: [{
                type: 'value',
                axisLabel: {
                    formatter: '{value} Mb'
                }
            }],
            series: [{
                name: '实时硬盘使用',
                type: 'line',
                data: d
            }]
        })
    })
}
function showIO(io, api) {
    $.get(api).done(function(data) {
        //console.log(data)
        var d = [];
        $.each(data.data.result[0].values, function(k, v) {
                d.push([
                    parseInt(v[0]) * 1000, (parseInt(v[1]) / 1024 / 1024).toFixed(2), (Math.random() * 100).toFixed(2) - 0
                ]);
            })
            // console.log(d)
        io.setOption({
            legend: {
                data: ["实时IO使用"]
            },
            yAxis: [{
                type: 'value',
                axisLabel: {
                    formatter: '{value}'
                }
            }],
            series: [{
                name: '实时IO使用',
                type: 'line',
                data: d
            }]
        })
    })
}