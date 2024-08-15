$(document).ready(function () {
    var myChart = echarts.init(document.getElementById('chart'));
    function getColorByDate(dateString) {
        var date = new Date(dateString);
        var startDate = new Date('2015-01-01');
        var endDate = new Date();
        var timeRange = endDate - startDate;
        var timeElapsed = date - startDate;
        var percentage = timeElapsed / timeRange;

        // 使用HSL颜色空间，从蓝色(240)到红色(0)
        var hue = 240 - (percentage * 240);
        return 'hsl(' + hue + ', 100%, 50%)';
    }

    function performSearch(query) {
        myChart.showLoading();
        $.ajax({
            url: '/search',
            method: 'POST',
            data: { query: query },
            success: function (data) {
                myChart.hideLoading();
                // 计算每个节点被引用的次数
                var citationCount = {};
                data.links.forEach(function (link) {
                    citationCount[link.target] = (citationCount[link.target] || 0) + 1;
                });
                // 计算引用次数的阈值（前10%）
                var citationValues = Object.values(citationCount);
                citationValues.sort((a, b) => b - a);
                var thresholdIndex = Math.floor(citationValues.length * 0.05);
                var citationThreshold = citationValues[thresholdIndex] || 0;

                var option = {
                    title: {
                        text: 'Paper Citation Network'
                    },
                    tooltip: {
                        formatter: function (params) {
                            if (params.dataType === 'node') {
                                return '<strong>' + params.data.title + '</strong><br/>' +
                                    'ID: ' + params.data.entry_id + '<br/>' +
                                    'Year: ' + params.data.published + '<br/>' +
                                    'Citations: ' + (citationCount[params.data.entry_id] || 0);
                                'Color: ' + params.color + ' (represents publication date)';
                            }
                            return params.name;
                        }
                    },
                    animationDurationUpdate: 1500,
                    animationEasingUpdate: 'quinticInOut',
                    legend: {
                        data: ['Early publications', 'Recent publications'],
                        left: 'right'
                    },

                    series: [{
                        type: 'graph',
                        layout: 'force',
                        roam: true,
                        draggable: true,  // 使节点可拖动
                        edgeSymbol: ['circle', 'arrow'],
                        edgeSymbolSize: [4, 10],
                        edgeLabel: {
                            fontSize: 20
                        },
                        categories: [
                            {
                                name: 'Early publications',
                                itemStyle: {
                                    color: 'blue'
                                }
                            },
                            {
                                name: 'Recent publications',
                                itemStyle: {
                                    color: 'red'
                                }
                            }
                        ],
                        emphasis: {
                          focus: 'adjacency',
                          label: {
                            position: 'right',
                            show: true
                          }
                        },
                        data: data.nodes.map(function (node) {
                            var citations = citationCount[node.entry_id] || 0;
                            return {
                                id: node.entry_id,
                                name: node.title,
                                title: node.title,
                                entry_id: node.entry_id,
                                published: node.published,
                                symbolSize: 20 + (citationCount[node.entry_id] || 0) * 1, // 根据引用次数调整大小
                                x: null,  // 允许力导向算法初始化位置
                                y: null,
                                fixed: false,  // 节点初始不固定
                                itemStyle: {
                                    color: getColorByDate(node.published)
                                },
                                label: {
                                    show: citations >= citationThreshold,
                                    formatter: '{b}'
                                },
                            };
                        }),
                        links: data.links.map(function (link) {
                            return {
                                source: link.source,
                                target: link.target
                            };
                        }),
                        lineStyle: {
                            opacity: 0.9,
                            width: 2,
                            curveness: 0
                        },
                        force: {
                            repulsion: 500,
//                            edgeLength: 300  // 可以调整这个值来改变节点间的距离
                        }

                    }]
                };
                myChart.setOption(option);

                // 添加左键点击事件
                myChart.on('click', function (params) {
                    if (params.dataType === 'node') {
                        window.open(params.data.entry_id, '_blank');
                    }
                });

                // 添加右键点击事件
                myChart.on('contextmenu', function (params) {
                    if (params.dataType === 'node') {
                        // 阻止默认的右键菜单
                        params.event.event.preventDefault();
                        // 使用节点的 entry_id 作为新的查询值
                        performSearch(params.data.entry_id);
                    }
                });

                // 添加拖拽结束事件
                myChart.on('dragend', function (params) {
                    if (params.dataType === 'node') {
                        // 可以在这里添加拖拽结束后的逻辑
                        console.log('Node dragged:', params.data);
                    }
                });
            }
        });
    }

    $('#search-button').click(function () {
        var query = $('#search-input').val();
        performSearch(query);
    });
});
