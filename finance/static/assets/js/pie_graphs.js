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
