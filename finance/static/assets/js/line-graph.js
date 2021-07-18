
  'use strict';

  var flatPicker = $('.flat-picker'),
    isRtl = $('html').attr('data-textdirection') === 'rtl',
    chartColors = {
      column: {
        series1: '#826af9',
        series2: '#d2b0ff',
        bg: '#f8d3ff'
      },
      success: {
        shade_100: '#7eefc7',
        shade_200: '#06774f'
      },
      donut: {
                series1: '#ffe700',
                series2: '#00d4bd',
                series3: '#826bf8',
                series4: '#2b9bf4',
                series5: '#FFA1A1',
                series6: '#a4f8cd',
                series7: '#60f2ca',
                series8: '#2bdac7',
                series9: '#826af9',
                series10: '#d2b0ff',
                series11: '#06774f',
                series12: '#7eefc7',
                series13: '#f8d3ff',
                series14: '#299AFF',
                series15: '#84D0FF',
                series16: '#EDF1F4',
                series17: '#28c76f66',
                series18: '#28c76f33'
              },
      area: {
                series1: '#ffe700',
                series2: '#00d4bd',
                series3: '#826bf8',
      }
    };

  // heat chart data generator
  function generateDataHeat(count, yrange) {
    var i = 0;
    var series = [];
    while (i < count) {
      var x = 'w' + (i + 1).toString();
      var y = Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;

      series.push({
        x: x,
        y: y
      });
      i++;
    }
    return series;
  }

  // Init flatpicker
  if (flatPicker.length) {
    var date = new Date();
    flatPicker.each(function () {
      $(this).flatpickr({
        mode: 'range',
        defaultDate: ['2019-05-01', '2019-05-10']
      });
    });
  }



  // Account Details Line Chart
  // --------------------------------------------------------------------
  function LinesGraph(close_graph_data)
  {
      var graph_data = []; // create an empty array
      console.log(close_graph_data);
    for(let i=0; i < close_graph_data.length; i++)
    {
            graph_data.push({
                        x:  new Date(close_graph_data[i]['x']),
                        y:  close_graph_data[i]['y']
                      });

    }
      isRtl = $('html').attr('data-textdirection') === 'rtl'
      var lineChartEl = document.querySelector('#Account-balance-line-chart'),
        lineChartConfig = {
          chart: {
            height: 400,
            type: 'line',
            zoom: {
              enabled: true
            },
            parentHeightOffset: 0,
            toolbar: {
              show: true
            }
          },
          series: [
            {
              data: graph_data
            }
          ],
          markers: {
            strokeWidth: 7,
            strokeOpacity: 1,
            strokeColors: [window.colors.solid.white],
            colors: [window.colors.solid.warning]
          },
          dataLabels: {
            enabled: false
          },
          stroke: {
            curve: 'straight'
          },
          colors: [window.colors.solid.warning],
          grid: {
            xaxis: {
              lines: {
                show: true
              }
            },
            padding: {
              top: -20
            }
          },
          tooltip: {
            custom: function (data) {
              return (
                '<div class="px-1 py-50">' +
                '<span>' +
                data.series[data.seriesIndex][data.dataPointIndex] +
                '</span>' +
                '</div>'
              );
            }
          },
          xaxis:
          {
            type: 'datetime'
          },
          yaxis:
          {
            tooltip: {
              enabled: true
            },
            labels: {
            formatter: function (price_value) {
              return parseInt(price_value) // The formatter function overrides format property
              }
            },
            opposite: isRtl
          }
        };
      if (typeof lineChartEl !== undefined && lineChartEl !== null) {
        var lineChart = new ApexCharts(lineChartEl, lineChartConfig);
        lineChart.render();
      }
  };

  // MortgageCalculator Area Chart
  // --------------------------------------------------------------------

  function MortgageChart(mortgage_graph_data, date_data)
  {
      var areaChartEl = document.querySelector('#line-area-chart'),
        areaChartConfig = {
          chart: {
            height: 600,
            type: 'area',
            parentHeightOffset: 0,
            toolbar: {
              show: false
            }
          },
          dataLabels: {
            enabled: false
          },
          stroke: {
            show: false,
            curve: 'straight'
          },
          legend: {
            show: true,
            position: 'top',
            horizontalAlign: 'start'
          },
          grid: {
            xaxis: {
              lines: {
                show: true
              }
            }
          },
          colors: [chartColors.area.series3, chartColors.area.series2, chartColors.area.series1],
          series: mortgage_graph_data,
          xaxis: {
            categories: date_data
          },
          fill: {
            opacity: 0.40,
            type: ''
          },
          tooltip: {
            shared: false
          },
          yaxis: [
                  {
                    title: {
                      text: "Balance"
                    },
                  },
                  {
                    opposite: true,
                    title: {
                      text: "Interest & Principle"
                    }
                  }
                  ]
        };
      if (typeof areaChartEl !== undefined && areaChartEl !== null) {
        var areaChart = new ApexCharts(areaChartEl, areaChartConfig);
        areaChart.render();
      }
  };

  // Multiple Account Chart
  // --------------------------------------------------------------------

    function AccountsChart(account_graph_data, account_date_data, max_value, min_value)
{
  var primaryColorShade = '#836AF9',
    yellowColor = '#ffe800',
    successColorShade = '#28dac6',
    warningColorShade = '#ffe802',
    warningLightColor = '#FDAC34',
    infoColorShade = '#299AFF',
    greyColor = '#4F5D70',
    blueColor = '#2c9aff',
    blueLightColor = '#84D0FF',
    greyLightColor = '#EDF1F4',
    tooltipShadow = 'rgba(0, 0, 0, 0.25)',
    lineChartPrimary = '#666ee8',
    lineChartDanger = '#ff4961',
    labelColor = '#6e6b7b',
    grid_line_color = 'rgba(200, 200, 200, 0.2)'; // RGBA color helps in dark layout

    var chart_colors = [lineChartPrimary, lineChartDanger, warningColorShade]
    var account_data_set = []; // create an empty array
    console.log(account_graph_data);
    console.log(account_date_data);
    for(let i=0; i < account_graph_data.length; i++)
    {
            account_data_set.push(
                                    {
                                    data: account_graph_data[i]['data_value'],
                                    label: account_graph_data[i]['label_name'],
                                    borderColor: chart_colors[i],
                                    lineTension: 0.5,
                                    pointStyle: 'circle',
                                    backgroundColor: chart_colors[i],
                                    fill: false,
                                    pointRadius: 1,
                                    pointHoverRadius: 5,
                                    pointHoverBorderWidth: 5,
                                    pointBorderColor: 'transparent',
                                    pointHoverBorderColor: window.colors.solid.white,
                                    pointHoverBackgroundColor: chart_colors[i],
                                    pointShadowOffsetX: 1,
                                    pointShadowOffsetY: 1,
                                    pointShadowBlur: 5,
                                    pointShadowColor: tooltipShadow
                                  }
                                )

    }
    console.log(account_data_set);
  var chartWrapper = $('.chartjs');
  let lineChartEx = $('.macro-chart');
  // Detect Dark Layout
  if ($('html').hasClass('dark-layout')) {
    labelColor = '#b4b7bd';
  }

  if (chartWrapper.length) {
        chartWrapper.each(function () {
          $(this).wrap($('<div style="height:' + this.getAttribute('data-height') + 'px"></div>'));
        });
      }

  if (lineChartEx.length) {
    var lineExample = new Chart(lineChartEx, {
      type: 'line',
      plugins: [
        // to add spacing between legends and chart
        {
          beforeInit: function (chart) {
            chart.legend.afterFit = function () {
              this.height += 20;
            };
          }
        }
      ],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        backgroundColor: false,
        hover: {
          mode: 'label'
        },
        tooltips: {
          // Updated default tooltip UI
          shadowOffsetX: 1,
          shadowOffsetY: 1,
          shadowBlur: 8,
          shadowColor: tooltipShadow,
          backgroundColor: window.colors.solid.white,
          titleFontColor: window.colors.solid.black,
          bodyFontColor: window.colors.solid.black
        },
        layout: {
          padding: {
            top: -15,
            bottom: -25,
            left: -15
          }
        },
        scales: {
          xAxes: [
            {
              display: true,
              scaleLabel: {
                display: true
              },
              gridLines: {
                display: true,
                color: grid_line_color,
                zeroLineColor: grid_line_color
              },
              ticks: {
                fontColor: labelColor
              }
            }
          ],
          yAxes: [
            {
              display: true,
              scaleLabel: {
                display: true
              },
              ticks: {
                stepSize: 2000,
                min: min_value,
                max: max_value,
                fontColor: labelColor
              },
              gridLines: {
                display: true,
                color: grid_line_color,
                zeroLineColor: grid_line_color
              }
            }
          ]
        },
        legend: {
          position: 'top',
          align: 'start',
          labels: {
            usePointStyle: true,
            padding: 25,
            boxWidth: 9
          }
        }
      },
      data: {
        labels: account_date_data,
        datasets: account_data_set
      }
    });
  }

}

  // Budgets Chart
  // --------------------------------------------------------------------

function BudgetChart(graph_label, graph_data, graph_currency)
{
  console.log(graph_data)
  $('#budget-chart').empty();
  var donutChartEl = document.querySelector('#budget-chart'),
    donutChartConfig = {
      chart: {
        height: 350,
        type: 'donut'
      },
      legend: {
        show: true,
        position: 'bottom'
      },
      labels: graph_label,
      series: graph_data,
      colors: [
        chartColors.donut.series1,
        chartColors.donut.series5,
        chartColors.donut.series3,
        chartColors.donut.series2,
        chartColors.donut.series7,
        chartColors.donut.series6,
        chartColors.donut.series4,
        chartColors.donut.series8,
        chartColors.donut.series9,
        chartColors.donut.series10,
        chartColors.donut.series11,
        chartColors.donut.series12,
        chartColors.donut.series13,
      ],
      dataLabels: {
        enabled: true,
        formatter: function (val, opt) {
          return parseInt(val) + '%';
        }
      },
      plotOptions: {
        pie: {
          donut: {
            labels: {
              show: true,
              name: {
                fontSize: '2rem',
                fontFamily: 'Montserrat'
              },
              value: {
                fontSize: '1rem',
                fontFamily: 'Montserrat',
                formatter: function (val) {
                  return parseInt(val) + graph_currency;
                }
              },
              total: {
                show: true,
                fontSize: '1.5rem',
                label: graph_label[0],
                formatter: function (w) {
                  return parseInt(graph_data[0]) + graph_currency;
                }
              }
            }
          }
        }
      },
      responsive: [
        {
          breakpoint: 992,
          options: {
            chart: {
              height: 380
            }
          }
        },
        {
          breakpoint: 576,
          options: {
            chart: {
              height: 320
            },
            plotOptions: {
              pie: {
                donut: {
                  labels: {
                    show: true,
                    name: {
                      fontSize: '1.5rem'
                    },
                    value: {
                      fontSize: '1rem'
                    },
                    total: {
                      fontSize: '1.5rem'
                    }
                  }
                }
              }
            }
          }
        }
      ]
    };
  if (typeof donutChartEl !== undefined && donutChartEl !== null) {
    var donutChart = new ApexCharts(donutChartEl, donutChartConfig);
    donutChart.render();
  }
}

  // CategorySpent Chart
  // --------------------------------------------------------------------

function CategorySpentChart(categories_name, categories_value)
{
//  var columnChartEl = document.querySelector('#column-chart'),
//    columnChartConfig = {
//      chart: {
//        height: 400,
//        type: 'bar',
//        stacked: true,
//        parentHeightOffset: 0,
//        toolbar: {
//          show: false
//        }
//      },
//      plotOptions: {
//        bar: {
//          columnWidth: '15%',
//          colors: {
//            backgroundBarColors: [
//              chartColors.column.bg,
//              chartColors.column.bg,
//              chartColors.column.bg,
//              chartColors.column.bg,
//              chartColors.column.bg
//            ],
//            backgroundBarRadius: 10
//          }
//        }
//      },
//      dataLabels: {
//        enabled: false
//      },
//      legend: {
//        show: true,
//        position: 'top',
//        horizontalAlign: 'start'
//      },
//      colors: [chartColors.column.series1, chartColors.column.series2],
//      stroke: {
//        show: true,
//        colors: ['transparent']
//      },
//      grid: {
//        xaxis: {
//          lines: {
//            show: true
//          }
//        }
//      },
//      series: [
//        {
//          name: 'Spent',
//          data: categories_value
//        },
//      ],
//      xaxis: {
//        categories: categories_name
//      },
//      fill: {
//        opacity: 1
//      },
//      yaxis: {
//        opposite: isRtl
//      }
//    };
//  if (typeof columnChartEl !== undefined && columnChartEl !== null) {
//    var columnChart = new ApexCharts(columnChartEl, columnChartConfig);
//    columnChart.render();
//  }
  var options = {
          series: [
                    {
                        name: 'Spent',
                        data: categories_value
                    }
                  ],
          chart: {
          type: 'bar',
          height: 430
        },
        plotOptions: {
          bar: {
            horizontal: false,
            dataLabels: {
              position: 'top',
            },
            columnWidth: '5%'
          }
        },
        dataLabels: {
          enabled: false,
          offsetX: -6,
          style: {
            fontSize: '12px',
            colors: ['#fff']
          }
        },
        stroke: {
          show: true,
          width: 1,
          colors: ['#fff']
        },
        tooltip: {
          shared: true,
          intersect: false
        },
        colors: ['#826af9'],
        xaxis: {
          categories: categories_name,
        },
        };

        var chart = new ApexCharts(document.querySelector("#column-chart"), options);
        chart.render();

}

function TransactionGraph(debit_graph_data, credit_graph_data, transaction_date_data)
{
  var options = {
          series: [
                    {
                        name: 'Debit',
                        data: debit_graph_data
                    },
                    {
                        name: 'Credit',
                        data: credit_graph_data
                    }
                  ],
          chart: {
          type: 'bar',
          height: 430
        },
        plotOptions: {
          bar: {
            horizontal: false,
            dataLabels: {
              position: 'top',
            },
            columnWidth: '10%'
          }
        },
        dataLabels: {
          enabled: false,
          offsetX: -6,
          style: {
            fontSize: '12px',
            colors: ['#fff']
          }
        },
        stroke: {
          show: true,
          width: 1,
          colors: ['#fff']
        },
        tooltip: {
          shared: true,
          intersect: false
        },
        colors: ['#B22222', '#008000'],
        xaxis: {
          categories: transaction_date_data,
        },
        };

        var chart = new ApexCharts(document.querySelector("#transaction-chart"), options);
        chart.render();

}

// Candlestick Chart
// --------------------------------------------------------------------

function PortfolioValueChart(candlestick_data, candlestick_id)
{
    console.log(candlestick_id)
    var graph_data = []; // create an empty array

    for (let i = 0; i < candlestick_data.length; i++)
    {
            graph_data.push({
                        x:  new Date(candlestick_data[i]['x']),
                        y:  candlestick_data[i]['y']
                      });

    }
    console.log(graph_data);
  var candlestickEl = document.querySelector(candlestick_id),
    candlestickChartConfig = {
      chart: {
        height: 400,
        type: 'candlestick',
        parentHeightOffset: 0,
        toolbar: {
          show: true
        }
      },
      series: [
        {
          data: graph_data
        }
      ],
      xaxis: {
        type: 'datetime'
      },
      yaxis: {
        tooltip: {
          enabled: true
        },
        labels: {
        formatter: function (price_value) {
          return parseInt(price_value) // The formatter function overrides format property
          }
        }
      },
      grid: {
        xaxis: {
          lines: {
            show: true
          }
        },
        padding: {
          top: -23
        }
      },
      plotOptions: {
        candlestick: {
          colors: {
            upward: window.colors.solid.success,
            downward: window.colors.solid.danger
          }
        },
        bar: {
          columnWidth: '40%'
        }
      }
    };
  if (typeof candlestickEl !== undefined && candlestickEl !== null) {
    var candlestickChart = new ApexCharts(candlestickEl, candlestickChartConfig);
    candlestickChart.render();
  }
}

  //------------ Portfolio Line Chart With Range 1M 1Y------------
  //-----------------------------------------------


function showPortfolioRange(close_range_data, close_id)
{
    console.log(typeof(close_id));
    var graph_data = []; // create an empty array

    for (let i = 0; i < close_range_data.length; i++)
    {
            graph_data.push({
                        x:  new Date(close_range_data[i]['x']),
                        y:  close_range_data[i]['y']
                      });

    }


  var $trackBgColor = '#EBEBEB';
  var statisticsProfitChart = document.querySelector(close_id);
  var statisticsProfitChartOptions = {
                                    chart: {
                                      height: 100,
                                      type: 'line',
                                      toolbar: {
                                        show: false
                                      },
                                      zoom: {
                                        enabled: false
                                      }
                                    },
                                    grid: {
                                      borderColor: $trackBgColor,
                                      strokeDashArray: 5,
                                      xaxis: {
                                        lines: {
                                          show: true
                                        }
                                      },
                                      yaxis: {
                                        lines: {
                                          show: false
                                        }
                                      },
                                      padding: {
                                        top: -30,
                                        bottom: -10
                                      }
                                    },
                                    stroke: {
                                      width: 3
                                    },
                                    colors: [window.colors.solid.info],
                                    series: [
                                      {
                                        name: 'Portfolio Change',
                                        data: graph_data
                                      }
                                    ],
                                    markers: {
                                      size: 2,
                                      colors: window.colors.solid.info,
                                      strokeColors: window.colors.solid.info,
                                      strokeWidth: 2,
                                      strokeOpacity: 1,
                                      strokeDashArray: 0,
                                      fillOpacity: 1,
                                      discrete: [
                                        {
                                          seriesIndex: 0,
                                          dataPointIndex: 5,
                                          fillColor: '#ffffff',
                                          strokeColor: window.colors.solid.info,
                                          size: 5
                                        }
                                      ],
                                      shape: 'circle',
                                      radius: 2,
                                      hover: {
                                        size: 3
                                      }
                                    },
                                    xaxis: {
                                      labels: {
                                        show: true,
                                        style: {
                                          fontSize: '0px'
                                        }
                                      },
                                      type: 'datetime',
                                      axisBorder: {
                                        show: false
                                      },
                                      axisTicks: {
                                        show: false
                                      }
                                    },
                                    yaxis: {
                                      show: false
                                    },
                                    tooltip: {
                                      x: {
                                        show: false
                                      }
                                    }
                                };
  statisticsProfitChart = new ApexCharts(statisticsProfitChart, statisticsProfitChartOptions);
  statisticsProfitChart.render();

}
