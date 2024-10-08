$(document).ready(function () {
    var myChart = echarts.init(document.getElementById('chart'));
    window.addEventListener('resize', function () {
        myChart.resize();
    });

    var searchData;
    var query_id
    var startDate, endDate;
    var currentStartDate, currentEndDate;

    function dateToTimestamp(date) {
        return date.getTime();
    }

    function timestampToDate(timestamp) {
        return new Date(timestamp);
    }

    function formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    function getColorByDate(dateString) {
        var date = new Date(dateString);
        var timeRange = endDate.getTime() - startDate.getTime();
        var timeElapsed = date.getTime() - startDate.getTime();
        var percentage = timeElapsed / timeRange;

        // 使用HSL颜色空间，从蓝色(240)到红色(0)
        var hue = 240 - (percentage * 240);
        return 'hsl(' + hue + ', 100%, 50%)';
    }
    function calculateFilteredData() {
        var citationCount = {};
        searchData.nodes.forEach(function (node) {
            citationCount[node.entry_id] = node.refered_ids.length || 1;
        });

        var filteredNodes = searchData.nodes.filter(function (node) {
            var nodeDate = new Date(node.published);
            return nodeDate >= currentStartDate && nodeDate <= currentEndDate;
        });

        var filteredNodeIds = new Set(filteredNodes.map(node => node.entry_id));

        // 重新计算引用计数，只考虑过滤后的节点
        var filteredCitationCount = {};
        filteredNodes.forEach(function (node) {
            filteredCitationCount[node.entry_id] = node.refered_ids.filter(id => filteredNodeIds.has(id)).length || 1;
        });

        var citationValues = Object.values(filteredCitationCount);
        citationValues.sort((a, b) => b - a);
        var thresholdIndex = Math.floor(citationValues.length * 0.05);
        var citationThreshold = citationValues[thresholdIndex] || 0;

        var filteredLinks = searchData.links.filter(function (link) {
            return filteredNodeIds.has(link.source) && filteredNodeIds.has(link.target);
        });

        return {
            citationCount: filteredCitationCount,
            citationThreshold: citationThreshold,
            filteredNodes: filteredNodes,
            filteredLinks: filteredLinks
        };
    }
    function updateChart() {
        if (!searchData) return;

        var filteredData = calculateFilteredData();
        var citationCount = filteredData.citationCount;
        var citationThreshold = filteredData.citationThreshold;
        var filteredNodes = filteredData.filteredNodes;
        var filteredLinks = filteredData.filteredLinks;

        var option = {
            tooltip: {
                confine: true, // 将 tooltip 限制在图表区域内
                enterable: true, // 允许鼠标进入 tooltip
                appendToBody: true,
                formatter: function (params) {
                    if (params.dataType === 'node') {
                        return '<div style="max-width: 500px; width: 500px; white-space: normal; word-break: break-all; overflow-wrap: break-word;">' +
                            '<strong style="display: block; margin-bottom: 5px;">' + params.data.title + '</strong>' +
                            '<span style="display: block;">ID: ' + params.data.entry_id + '</span>' +
                            '<span style="display: block;">Date: ' + params.data.published + '</span>' +
                             '<span style="display: block;">Depth: ' + params.data.depth + '</span>' +
                            '<span style="display: block;">Citations: ' + (citationCount[params.data.entry_id] || 0) + '</span>' +
                            '</div>';
                    }
                    return null;
                },
                position: function (point, params, dom, rect, size) {
                    // 计算 tooltip 的位置
                    var x = point[0];
                    var y = point[1];
                    var viewWidth = size.viewSize[0];
                    var viewHeight = size.viewSize[1];
                    var boxWidth = size.contentSize[0];
                    var boxHeight = size.contentSize[1];
                    var posX = x + 15;
                    var posY = y + 15;

                    // 当 tooltip 超出右边界时
                    if (posX + boxWidth > viewWidth) {
                        posX = x - boxWidth - 15;
                    }
                    // 当 tooltip 超出下边界时
                    if (posY + boxHeight > viewHeight) {
                        posY = y - boxHeight - 15;
                    }

                    return [posX, posY];
                }
            },
            textStyle: {
                width: 300,
                overflow: 'break'
            },
            animationDurationUpdate: 1500,
            animationEasingUpdate: 'quinticInOut',
            series: [{
                type: 'graph',
                layout: 'force',
                roam: true,
                draggable: true,
                data: filteredNodes.map(function (node) {
                    var citations = citationCount[node.entry_id] || 0;
                    return {
                        id: node.entry_id,
                        name: node.title,
                        title: node.title,
                        entry_id: node.entry_id,
                        published: node.published,
                        depth: node.depth,
                        symbolSize: 20 + Math.log(citations || 1) * 20,
                        x: null,
                        y: null,
                        itemStyle: {
                            color: getColorByDate(node.published)
                        },
                        label: {
                            show: citations >= citationThreshold,
                            formatter: '{b}',
                            color: getColorByDate(node.published)
                        },
                    };
                }),
                links: filteredLinks.map(function (link) {
                    return {
                        source: link.source,
                        target: link.target,
                        lineStyle: {
                            color: getColorByDate(filteredNodes.find(node => node.entry_id === link.source).published)
                        }
                    };
                }),
                edgeSymbol: ['circle', 'arrow'],
                edgeSymbolSize: [4, 10],
                force: {
                    repulsion: 500,
                    edgeLength: 200
                },
                symbol: function (value, params) {
                    // 使用正则表达式匹配ID
                    if (params.data.depth == 0) {
                         return 'circle';  // 默认形状为圆形
                    }
                    else if (Math.abs(params.data.depth) == 1) {
                        return 'diamond';  // 将匹配的节点形状设置为菱形
                    }
                    else return 'triangle';  // 将匹配的节点形状设置为菱形
                }
                , emphasis: {
                    focus: 'adjacency',
                }
            }]
        };
        myChart.setOption(option);
    }

    function performSearch(query) {
        $("#search-button").attr("disabled","true");
        myChart.showLoading();
        $.ajax({
            url: '/search',
            method: 'POST',
            data: { query: query },
            success: function (data) {
                $("#search-button").removeAttr("disabled");
                myChart.hideLoading();
                searchData = data;
                query_id = query
                // 获取数据中的最早和最晚日期
                var dates = data.nodes.map(node => new Date(node.published));
                startDate = new Date(Math.min.apply(null, dates));
                endDate = new Date(Math.max.apply(null, dates));
                currentStartDate = startDate;
                currentEndDate = endDate;

                // 更新滑动条
                $("#date-slider").slider("option", "min", dateToTimestamp(startDate));
                $("#date-slider").slider("option", "max", dateToTimestamp(endDate));
                $("#date-slider").slider("values", [dateToTimestamp(startDate), dateToTimestamp(endDate)]);
                $("#date-range").text(formatDate(startDate) + " - " + formatDate(endDate));

                updateChart();

                // 启用滑动条
                $("#date-slider").slider("enable");

                // 添加左键点击事件
                myChart.on('click', function (params) {
                    if (params.dataType === 'node') {
                        window.open(params.data.entry_id, '_blank');
                    }
                });

                // 添加右键点击事件
                myChart.on('contextmenu', function (params) {
                    if (params.dataType === 'node') {
                        params.event.event.preventDefault();
                        performSearch(params.data.entry_id);
                    }
                });
            },
            error : function(e){
                $("#search-button").removeAttr("disabled");
                myChart.hideLoading();
                if (e.status==429)
                window.alert("请求太快了，服务器受不了了！！！")
                if (e.status==404)
                window.alert("没有找到这篇论文呢,请检查输入的arxiv id。")
                if (e.status==408)
                window.alert("糟糕！遇见了超级节点，如果特别需要请联系作者。")
                if (e.status==500)
                window.alert("糟糕！bug了，请联系作者")
            }
        });
    }

    $('#search-button').click(function () {
        var query = $('#search-input').val();
        performSearch(query);
    });
    $('#try_one_try').click(function () {
        var query = "2106.13008";
        performSearch(query);
    });

    // 初始化日期滑动条
    $("#date-slider").slider({
        range: true,
        min: dateToTimestamp(new Date('1900-01-01')),
        max: dateToTimestamp(new Date()),
        step: 86400000, // 一天的毫秒数
        values: [dateToTimestamp(new Date('1900-01-01')), dateToTimestamp(new Date())],
        slide: function (event, ui) {
            var startDate = timestampToDate(ui.values[0]);
            var endDate = timestampToDate(ui.values[1]);
            $("#date-range").text(formatDate(startDate) + " - " + formatDate(endDate));
            currentStartDate = startDate;
            currentEndDate = endDate;
            updateChart();
        }
    });
    $("#date-range").text(formatDate(new Date('1900-01-01')) + " - " + formatDate(new Date()));

    // 初始时禁用滑动条
    $("#date-slider").slider("disable");
});
