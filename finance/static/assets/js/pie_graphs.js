 chartColors = {
              donut: {
                series1: '#ffe700',
                series2: '#00d4bd',
                series3: '#826bf8',
                series4: '#2b9bf4',
                series5: '#FFA1A1',
                series6: '#E13C00',
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
              }
                };

  // Budgets Chart
  // --------------------------------------------------------------------

function BudgetChart(graph_label, graph_data, graph_currency, graph_id)
{
  console.log("graph_id", graph_id)
  console.log("graph_label", graph_label)
  console.log("graph_data", graph_data)
  console.log("graph_currency", graph_currency)

  var donutChartEl = document.querySelector(graph_id),
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



//--------------- Portfolio Current & Weights Chart ---------------
//----------------------------------------------

        function showIndustry(industry_list, industry_value, ind_id)
        {
              var $earningsChart = document.querySelector(ind_id),
              earningsChartOptions = {
                chart: {
                  type: 'donut',
                  height: 161,
                  toolbar: {
                    show: false
                  }
                },
                dataLabels: {
                  enabled: false
                },
                series: industry_value,
                legend: { show: false },
                comparedResult: [2, -3, 8],
                labels: industry_list,
                stroke: { width: 0 },
                colors: [
                    chartColors.donut.series1,
                    chartColors.donut.series5,
                    chartColors.donut.series3,
                    chartColors.donut.series2,
                    chartColors.donut.series4,
                    chartColors.donut.series1,
                    chartColors.donut.series5,
                    chartColors.donut.series3,
                    chartColors.donut.series2,
                    chartColors.donut.series4,

                  ],
                grid: {
                  padding: {
                    right: -20,
                    bottom: -8,
                    left: -20
                  }
                },
                plotOptions: {
                  pie: {
                    startAngle: -10,
                    donut: {
                      labels: {
                        show: true,
                        name: {
                          offsetY: 20
                        },
                        value: {
                          offsetY: -15,
                          formatter: function (val) {
                            return parseInt(val) + '%';
                          }
                        },
                        total: {
                          show: true,
                          offsetY: 15,
                          label: industry_list[0],
                          formatter: function (w) {
                            return parseInt(industry_value[0]) + '%';
                          }
                        }
                      }
                    }
                  }
                },
                responsive: [
                  {
                    breakpoint: 1325,
                    options: {
                      chart: {
                        height: 100
                      }
                    }
                  },
                  {
                    breakpoint: 1200,
                    options: {
                      chart: {
                        height: 120
                      }
                    }
                  },
                  {
                    breakpoint: 1045,
                    options: {
                      chart: {
                        height: 100
                      }
                    }
                  },
                  {
                    breakpoint: 992,
                    options: {
                      chart: {
                        height: 120
                      }
                    }
                  }
                ]
              };
              earningsChart = new ApexCharts($earningsChart, earningsChartOptions);
              earningsChart.render();
        };

//--------------- Portfolio Industry Chart ---------------
//----------------------------------------------

        function portfolioIndustry(industry_list, industry_value, ind_id)
        {
              var $earningsChart = document.querySelector(ind_id),
              earningsChartOptions = {
                chart: {
                  type: 'donut',
                  height: 161,
                  toolbar: {
                    show: false
                  }
                },
                dataLabels: {
                  enabled: true,
                  formatter: function (val, opt) {
                      return parseInt(val) + '%';
                    }
                },
                series: industry_value,
                legend: { show: false },
                comparedResult: [2, -3, 8],
                labels: industry_list,
                stroke: { width: 0 },
                colors: [
                    chartColors.donut.series1,
                    chartColors.donut.series5,
                    chartColors.donut.series3,
                    chartColors.donut.series2,
                    chartColors.donut.series4,
                    chartColors.donut.series3,
                    chartColors.donut.series2,
                    chartColors.donut.series4,
                  ],
                grid: {
                  padding: {
                    right: -20,
                    bottom: -8,
                    left: -20
                  }
                },
                plotOptions: {
                  pie: {
                    startAngle: -10,
                    donut: {}
                  }
                },
                responsive: [
                  {
                    breakpoint: 1325,
                    options: {
                      chart: {
                        height: 100
                      }
                    }
                  },
                  {
                    breakpoint: 1200,
                    options: {
                      chart: {
                        height: 120
                      }
                    }
                  },
                  {
                    breakpoint: 1045,
                    options: {
                      chart: {
                        height: 100
                      }
                    }
                  },
                  {
                    breakpoint: 992,
                    options: {
                      chart: {
                        height: 120
                      }
                    }
                  }
                ]
              };
              earningsChart = new ApexCharts($earningsChart, earningsChartOptions);
              earningsChart.render();
        };

  //------------ Statistics Bar Chart ------------
  //----------------------------------------------

  function stockAmount(amount_data, amount_id)
  {
      var data_len = amount_data.length
      if(data_len <= 2)
      {
        var column_width = "10%"
      }
      else
      {
        var column_width = "20%"
      }
      console.log(amount_data);
      var $barColor = '#f3f3f3';
      var $statisticsOrderChart = document.querySelector(amount_id),
      statisticsOrderChartOptions = {
        chart: {
          height: 140,
          type: 'bar',
          stacked: true,
          toolbar: {
            show: false
          }
        },
        grid: {
          show: false,
          padding: {
            left: 0,
            right: 0,
            top: -15,
            bottom: -15
          }
        },
        plotOptions: {
          bar: {
            horizontal: false,
            columnWidth: column_width,
            startingShape: 'rounded',
            colors: {
              backgroundBarColors: [$barColor, $barColor, $barColor, $barColor, $barColor],
              backgroundBarRadius: 5
            }
          }
        },
        legend: {
          show: true
        },
        dataLabels: {
          enabled: false
        },
        colors: [window.colors.solid.warning],
        series: [
          {
            name: '2021',
            data: amount_data
          }
        ],
        xaxis: {
          labels: {
            show: false
          },
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
      statisticsOrderChart = new ApexCharts($statisticsOrderChart, statisticsOrderChartOptions);
      statisticsOrderChart.render();
      if(data_len == 1)
      {
        $(".apexcharts-backgroundBar").attr('fill', '#FF8C00');
      }

  };

    function showIndustryGraph(graph_label, graph_value)
    {
        portfolioIndustry(graph_label, graph_value, "#donut-industry-chart");

    }

    function portfolioWeights(graph_label, graph_value, graph_value2)
    {
        showIndustry(graph_label, graph_value, "#donut-weight1-chart");
        showIndustry(graph_label, graph_value2, "#donut-weight2-chart");

    }

    function showDonutGraph(current_value, optimize_value, symbol_list)
    {
        weightGraph(symbol_list, current_value, "#donut-current-chart");
        weightGraph(symbol_list, optimize_value, "#donut-optimize-chart");
    }

    function showStockAmount(portfolio_amount)
    {
        console.log(portfolio_amount);
        stockAmount(portfolio_amount, "#statistics-amount-chart");
    }


    function MakePieData(budgets_data, graph_currency, graph_id)
    {
        var i = 1
        for (const [key, value] of Object.entries(budgets_data))
        {
            graph_new_id = "#" + graph_id + i
            graph_label = ['Total Spent', 'Total Left']
            BudgetChart(graph_label, value, graph_currency, graph_new_id)
            var i = i + 1

        }

    }
    function AllCompareBudgets(week_budgets_data, month_budgets_data, quarter_budgets_data, year_budgets_data, graph_currency)
    {
        MakePieData(week_budgets_data, graph_currency, "week-pie-chart")
        MakePieData(month_budgets_data, graph_currency, "month-pie-chart")
        MakePieData(quarter_budgets_data, graph_currency, "quart-pie-chart")
        MakePieData(year_budgets_data, graph_currency, "year-pie-chart")
    }