$(document).ready(function()
{
    $('.edit_income').on('click', function(event)
    {
        location.assign($(this).attr('href'))
    });

    $('#capex_budget').DataTable( {
    "footerCallback": function ( row, data, start, end, display ) {
            var api = this.api(), data;

            // Remove the formatting to get integer data for summation
            var intVal = function ( i ) {
                return typeof i === 'string' ?
                    i.replace(/[\$,]/g, '')*1 :
                    typeof i === 'number' ?
                        i : 0;
            };

            // Total over all pages
            all_total = api
                .column(1)
                .data()
                .reduce( function (a, b) {
                    currency_name = b[0]
                    return intVal(a) + intVal(b);
                }, 0 );
            year_total = api
                .column(2)
                .data()
                .reduce( function (a, b) {
                    return intVal(a) + intVal(b);
                }, 0 );
            year_cost_total = api
                .column(3)
                .data()
                .reduce( function (a, b) {
                    return intVal(a) + intVal(b);
                }, 0 );
            month_cost_total = api
                .column(4)
                .data()
                .reduce( function (a, b) {
                    return intVal(a) + intVal(b);
                }, 0 );

            // Update footer
            $( api.column(1).footer() ).html(currency_name + all_total);
            $( api.column(2).footer() ).html(year_total + "(Year)");
            $( api.column(3).footer() ).html(currency_name + year_cost_total);
            $( api.column(4).footer() ).html(currency_name + month_cost_total.toFixed(2));
            },
            columnDefs: [
            { orderable: false, targets: 1 }
            ],
            pageLength : 24,
            lengthMenu: [[24,48, 72], [24,48, 72]]
    } );
    $('#revenue_table').DataTable( {
    "footerCallback": function(row, data, start, end, display) {

      var api = this.api(), data;
      column_length = $(this).attr('column_length')
     // Total over this page
     for(let j=2; j<column_length; j++)
     {

        pageTotal = api
            .column( j, { page: 'current'} )
            .data()
            .reduce( function (a, b)
            {
                currency_name = b[0]
                b = parseFloat(b.replace(currency_name, ''))
                return a + b;
            }, 0);
        $( api.column( j ).footer() ).html(currency_name+pageTotal);

     }
    },
     columnDefs: [
            { orderable: false, targets: 1 }
     ],
    pageLength : 12,
    lengthMenu: [[12, 24, 36], [12, 24, 36]]
    } );

$('#expense_table').DataTable( {
    "footerCallback": function(row, data, start, end, display) {

      var api = this.api(), data;
      category_name = []
      category_value = []
      graph_label = api
                .column( 1, { page: 'current'} )
                .data()
                .reduce( function (a, b)
                {
                    category_name.push(b)
                return b;
                }, 0 );

      pageTotal = api
                .column( 4, { page: 'current'} )
                .data()
                .reduce( function (a, b) {
                    currency_name = b[0]
                    b = parseFloat(b.replace(currency_name, ''))
                    category_value.push(b)
                return a + b;
                }, 0 );

            category_value = [{'name': 'Spent', 'data': category_value}]
            // Update footer
            $( api.column( 4 ).footer() ).html('$'+pageTotal);
            CategorySpentChart(category_name, category_value, "#column-chart");
    },
    columnDefs: [
            { orderable: false, targets: 3 }
     ],
    pageLength : 12,
    lengthMenu: [[12, 24, 36], [12, 24, 36]]
    } );

    if($('#lock_amount_check').prop("checked"))
    {
        $('#lock_amount_div').show();
    }
    else
    {
        $('#lock_amount_div').hide();
    }

    $('#lock_amount_check').on('click', function(event)
    {
        var check = $(this).prop("checked")
        if(check)
        {
            $('#lock_amount_div').show();
        }
        else
        {
            $('#lock_amount_div').hide();
        }
    });

// SELECT BILL AND ADD AUTOMATIC AMOUNT
    $('#id_bill').on('change', function(e)
    {
        bill_id = $(this).val();
        var csrftoken = getCookie('csrftoken');
        $.ajax({
            type: 'POST',
            url:'/bill/automatic_amount',
            data: {
            'bill_id': bill_id,
            'csrfmiddlewaretoken': csrftoken
            },
            dataType: 'json',
            success: function(data)
            {
                 $("#transaction_amount").val(data.bill_amount)
            }
        })

    });

    $('.new_category').on('click', function(e)
    {
        e.preventDefault();
        var category_name = $(this).text()
        var csrftoken = getCookie('csrftoken');
        $(this).remove();
        Swal.fire({
                    title: 'Added',
                    icon: 'success',
                    customClass: {
                      confirmButton: 'btn btn-primary'
                    },
                    buttonsStyling: false
                  });
        $.ajax({
            type: 'POST',
            url:'/category_add/',
            data: {
            'name': category_name,
            'csrfmiddlewaretoken': csrftoken
            },
            dataType: 'json',
            success: function()
            {

            }
        })
    });

// DOWNLOAD CSV FILE
    $('.download_csv').on("click", function(e)
    {
        var table_id = $(this).attr('table_id')
        $(table_id).DataTable().destroy();
        var file_name = $(this).attr('file_name')
        var table_length = parseInt($(this).attr('table_length'));
        var csv_data_key = $(this).attr('table_heading');
        var download_url = $(this).attr('url');
        var pdf_title = $(this).attr('pdf_title');
        var fun_name = $(this).attr('fun_name');
        var graph_type = $('#download_graph_data').attr('graph_type');
        csv_data_value = []
        var value_index = 1
        $(table_id + " >  tbody").find('tr').each(function (i, el)
        {
            var $tds = $(this).find('td')
            data_value = []
            for (i = 0; i < table_length; i++)
            {
                value = $tds.eq(i).text().trim()
                if(value == "")
                {
                    cleared_class = ".cleared" + value_index
                    var cleared = $(cleared_class).val()
                    data_value.push(cleared)
                }

                else
                {
                    data_value.push(value)
                }
            }
            value_index += 1;
            csv_data_value.push(data_value)
       });
       $(table_id).DataTable({"aaSorting": []});
        console.log(csv_data_value);
        $(".download_csv_form").empty();
        $(".download_pdf_form").empty();

        formHtml = "<form action=" +  download_url + " method='post'>" + "<input type='hidden' name='file_name' value='" + file_name + "' >"
                     + "<input type='hidden' name='csv_data_key' value='" + csv_data_key + "' >" + "<input type='hidden' name='csv_data_value' value='" + JSON.stringify(csv_data_value) + "' >"
        if(pdf_title)
        {
            formHtml += "<input type='hidden' name='pdf_title' value='" + pdf_title + "' >"
        }
        if(graph_type == 'transaction-bar')
        {
            var data_label = $('#download_graph_data').attr('data_label');
            var debit_value = $('#download_graph_data').attr('data_value');
            var credit_value = $('#download_graph_data').attr('credit_value');
            formHtml += "<input type='hidden' name='graph_type' value='" + graph_type + "' >" +
                        "<input type='hidden' name='data_label' value='" + data_label + "' >" +
                        "<input type='hidden' name='data_value' value='" + debit_value + "' >" +
                        "<input type='hidden' name='credit_value' value='" + credit_value + "' >"
        }
        if(graph_type == 'bar' || graph_type == 'line')
        {
            var data_label = $('#download_graph_data').attr('data_label');
            var data_value = $('#download_graph_data').attr('data_value');
            formHtml += "<input type='hidden' name='graph_type' value='" + graph_type + "' >" +
                        "<input type='hidden' name='data_label' value='" + data_label + "' >" +
                        "<input type='hidden' name='data_value' value='" + data_value + "' >"
        }
        formHtml += "</form>"
        var form = $(formHtml);
        if(fun_name == "download_csv")
        {
            $('.download_csv_form').append(form);
        }
        else
        {
            $('.download_pdf_form').append(form);
        }
        form.submit();

    });
    $('.delete_button').on("click", function(e)
    {
        name = $(this).attr('delete_name');
        text_msg = "Once deleted the " + name + ", cannot be recovered."
        delete_url = $(this).attr('url');
        Swal.fire({
        title: 'Delete Screener',
        text: text_msg,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, delete it!',
        customClass: {
          confirmButton: 'btn btn-primary',
          cancelButton: 'btn btn-outline-danger ml-1'
        },
        buttonsStyling: false
      }).then(function (result)
      {
        if (result.value)
        {
            var csrfmiddlewaretoken = getCookie('csrftoken');
            $.ajax
            ({
                type: 'POST',
                url: delete_url,
                data: {
                        'csrfmiddlewaretoken': csrfmiddlewaretoken
                        },
                success: function(response)
                {
                    if(response.status == "Successfully")
                    {
                         Swal.fire
                         ({
                            title: 'Deleted',
                            icon: 'success',
                            customClass: {
                              confirmButton: 'btn btn-primary'
                            },
                            buttonsStyling: false
                         });
                    }
                    if(response.path == "None")
                    {
                        location.reload()
                    }
                    else
                    {
                        location.assign(response.path);
                    }
                }
            });
        }
      });

    });
});

// SAVE UPLOAD TRANSACTION FILe

    $('#upload_transaction_form').submit(function()
    {
        var form = $('#upload_transaction_form')[0];
        var data = new FormData(form);
        $.ajax(
        {
            type: $(this).attr('method'),
            enctype: 'multipart/form-data',
            url: $(this).attr('action'),
            data: data,
            processData: false,
            contentType: false,
            cache: false,
            success: function(response)
            {
                if(response.status == "File Uploaded")
                {
                     Swal.fire({
                                title: response.status,
                                icon: 'success',
                                customClass: {
                                  confirmButton: 'btn btn-primary'
                                },
                                buttonsStyling: false
                              });
                     location.reload();
                }
                else
                {
                     Swal.fire({
                                title: response.status,
                                icon: 'error',
                                customClass: {
                                  confirmButton: 'btn btn-primary'
                                },
                                buttonsStyling: false
                              });
                }
            }
        });
        return false;
    });

$('.check_primary').on("click", function(e)
{
    $('.end_month').toggle();
    var month_label = $('#check_month').text()
    if(month_label == 'Start Month')
    {
        $('#check_month').text('Month')
    }
    else
    {
        $('#check_month').text('Start Month')
    }
});

// Fund Overtime

    $('.fund_overtime').on("click", function(e)
    {
        var account_name = $(this).closest('td').next().find('#acc_name').attr('account_name');
        var csrfmiddlewaretoken = getCookie('csrftoken');
        $.ajax(
        {
            type: 'POST',
            url: '/fund_overtime',
            data: {
                    'account_name': account_name,
                    'csrfmiddlewaretoken': csrfmiddlewaretoken
                  },
            success: function(response)
            {
                AccountsChart(response.fund_data, response.date_range_list, response.max_value, response.min_value);
            }
        });
    });

// Budget Month Filter budget_month_filter

    $('.budget_period_filter').on("change", function(e)
    {
        $("#period_filter_form").submit();
    });



// RENTAL PROPERTY JS

// ADD Units Fields
$("body").delegate(".add_unit_button", "click", function(event)
{
    div_number = $(this).attr('div_class')
    class_name = "unit_div_" + div_number
    extra_div_number = parseInt(div_number) + 1
    parent_div =  parseInt(div_number) - 1
    console.log(parent_div)
    var inputHtml = "<div class='col-12 " + class_name +" '>" + "<div class='form-group row'>" + "<div class='col-sm-3 col-form-label'>"
        inputHtml += "<label for='fname-icon'>" + "Unit" + div_number + "</label>" + "</div>" + "<div class='col-sm-7'>"
        inputHtml += "<div class='input-group input-group-merge'>" + "<input type='text' class='form-control' name='others_revenue_cost' required placeholder='Unit" + div_number + "' />"
        inputHtml += "</div>" + "</div>" + "<div class='col-sm-2 extra_unit_div_" + div_number + "'>"
        inputHtml += "<button class='btn btn-primary add_unit_button' div_class='" + extra_div_number + "' title='Add Unit'>"
        inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>"
    $(inputHtml).insertAfter(".unit_div_"+parent_div);
    deleteButton = "<button class='btn btn-danger remove_unit_button' div_number='" + parent_div + "' div_class='" + class_name + "' title='Delete Unit' style='margin-left:5px;' ><i class='fa fa-minus'></i></button></div></div></div>"
    $(".extra_unit_div_"+div_number).append(deleteButton)
    $(".extra_unit_div_"+parent_div).empty()
});

$("body").delegate(".remove_unit_button", "click", function(event)
{
    div_number = parseInt($(this).attr('div_number'))
    unit_number = parseInt($(".last_unit").attr('unit_number'))
    if(div_number > unit_number)
    {
        extra_div_number = div_number + 1
        parent_div =  div_number - 1
        change_class = "unit_div_" + div_number
        inputHtml = "<button class='btn btn-primary add_unit_button' div_class='" + extra_div_number + "' title='Add Unit'>"
        inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>"
        inputHtml += "<button class='btn btn-danger remove_unit_button' div_number='" + parent_div + "' div_class='" + change_class + "' title='Delete Unit' style='margin-left:5px;' ><i class='fa fa-minus'></i></button></div></div></div>"
    }
    else
    {
        inputHtml = "<button class='btn btn-primary add_unit_button' div_class='" + 3 + "' title='Add Unit'>"
        inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>"
    }
    $(".extra_unit_div_"+div_number).append(inputHtml)
    class_name = $(this).attr('div_class')
    $("."+class_name).remove()
});

$("body").delegate(".add_other_cost", "click", function(event)
{
    main_class = $(this).attr('main_class')
    extra_class = $(this).attr('extra_class')
    input_name = $(this).attr('input_name')
    div_number = $(this).attr('div_class')
    class_name = main_class + div_number
    extra_div_number = parseInt(div_number) + 1
    parent_div =  parseInt(div_number) - 1
    var inputHtml = "<div class='col-12 " + class_name +" '>" + "<div class='form-group row'>" + "<div class='col-sm-3 col-form-label'>"
        inputHtml += "<input type='text' class='form-control' value='Other(Please Specify)' name='" + input_name + "' required placeholder='Other(Please Specify)'/> " + "</div>" + "<div class='col-sm-7' style='padding-top:7px;'>"
        inputHtml += "<div class='input-group input-group-merge'>" + "<input type='text' class='form-control' name='" + input_name + "' required placeholder='-' />"
        inputHtml += "</div>" + "</div>" + "<div class='col-sm-2 "+ extra_class + div_number + "' style='padding-top:7px;'>"
        inputHtml += "<button class='btn btn-primary add_other_cost' input_name='" + input_name + "' main_class='" + main_class + "' extra_class='" + extra_class + "' div_class='" + extra_div_number + "' title='Add Other'>"
        inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>"
    $(inputHtml).insertAfter("."+ main_class +parent_div);
    deleteButton = "<button class='btn btn-danger remove_other_cost' input_name='" + input_name + "' div_number='" + parent_div + "' main_class='" + main_class + "' extra_class='" + extra_class + "' div_class='" + class_name + "' title='Delete' style='margin-left:5px;' ><i class='fa fa-minus'></i></button></div></div></div>"
    $("."+extra_class+div_number).append(deleteButton)
    $("."+extra_class+parent_div).empty()


});

$("body").delegate(".remove_other_cost", "click", function(event)
{
    div_number = parseInt($(this).attr('div_number'))
    main_class = $(this).attr('main_class')
    extra_class = $(this).attr('extra_class')
    input_name = $(this).attr('input_name')

    if(input_name == "other_utilities")
    {
        last_div = parseInt($(".last_utility").attr('last_div')) + 1
        }
    if(input_name == "other_cost")
    {
        last_div = parseInt($(".last_cost").attr('last_div')) + 1
    }
    if(input_name == "other_expenses")
    {
        last_div = parseInt($(".last_expenses").attr('last_div')) + 1
    }

    if(div_number >= last_div)
    {
        extra_div_number = div_number + 1
        parent_div =  div_number - 1
        change_class = main_class + div_number
        inputHtml = "<button class='btn btn-primary add_other_cost' input_name='" + input_name + "' main_class='" + main_class + "' extra_class='" + extra_class + "' div_class='" + extra_div_number + "' title='Add Other'>"
        inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>"
        inputHtml += "<button class='btn btn-danger remove_other_cost' input_name='" + input_name + "' div_number='" + parent_div + "' main_class='" + main_class + "' extra_class='" + extra_class + "' div_class='" + change_class + "' title='Delete' style='margin-left:5px;' ><i class='fa fa-minus'></i></button></div></div></div>"
    }
    else
    {
        inputHtml = "<button class='btn btn-primary add_other_cost' input_name='" + input_name + "' main_class='" + main_class + "' extra_class='" + extra_class + "' div_class='" + last_div + "' title='Add Other'>"
        inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>"
    }
    $("."+extra_class+div_number).append(inputHtml)
    class_name = $(this).attr('div_class')
    $("."+class_name).remove()
});


$("body").delegate(".investor_button", "click", function(event)
{
    div_number = parseInt($(this).attr('div_class'))
    $(this).attr('div_class', div_number+1)
    var inputHtml = "<div class='col-12 investor_div_" + div_number + "' >" + "<div class='form-group row'>" + "<div class='col-sm-2 col-form-label'>"
        inputHtml += "<label for='fname-icon'>Name</label></div><div class='col-sm-4'><div class='input-group input-group-merge'>"
        inputHtml += "<input type='text' class='form-control' name='investor_detail' required placeholder='Investor Name'/></div></div>"
        inputHtml +=  "<div class='col-sm-2 col-form-label'><label for='fname-icon'>Capital Contribution</label></div><div class='col-sm-3'>"
        inputHtml +=  "<div class='input-group input-group-merge'><input type='text' class='form-control' name='investor_detail' required placeholder='Investor Name'/></div></div>"
        inputHtml += "<div class='col-sm-1'><button class='btn btn-danger remove_investor' div_class='investor_div_" + div_number + "' title='Delete' style='margin-left:5px;' ><i class='fa fa-minus'></i></button>"
        inputHtml +=  "</div></div></div>"

    $(inputHtml).insertBefore("#investor_add_div");
});


$("body").delegate(".budget_button", "click", function(event)
{
    div_number = parseInt($(this).attr('div_class'))
    $(this).attr('div_class', div_number+1)
    var inputHtml = "<div class='col-12 budget_div_" + div_number + "' >" + "<div class='form-group row'>" + "<div class='col-sm-3 col-form-label'>"
        inputHtml += "<input type='text' class='form-control' name='other_budget' placeholder='Name'/></div><div class='col-sm-4' style='padding-top:7px;'><div class='input-group input-group-merge'>"
        inputHtml += "<input type='text' class='form-control budget_cost' name='other_budget' placeholder='Total Replacement Cost'/></div></div>"
        inputHtml +=  "<div class='col-sm-4' style='padding-top:7px;' >"
        inputHtml +=  "<div class='input-group input-group-merge'><input type='text' class='form-control' name='other_budget' placeholder='Lifespan (years) '/></div></div>"
        inputHtml += "<div class='col-sm-1' style='padding-top:7px;'><button class='btn btn-danger remove_budget' div_class='budget_div_" + div_number + "' title='Delete' style='margin-left:5px;' ><i class='fa fa-minus'></i></button>"
        inputHtml +=  "</div></div></div>"

    $(inputHtml).insertBefore("#budget_add_div");
});

$("body").delegate(".remove_investor", "click", function(event)
{
    class_name = $(this).attr('div_class')
    $("."+class_name).remove()
    div_number = parseInt($(".investor_button").attr('div_class')) - 1
    $(".investor_button").attr('div_class', div_number)
});

$("body").delegate(".budget_cost", "change", function(event)
{
    var sum = 0;
    var budget_cost_data = []
    $(".budget_cost").each(function(){

        input_val = $(this).val()
        if(input_val)
        {
            budget_cost_data.push(input_val)
            sum = sum + parseFloat(input_val);
        }
    });
    $(".total_budget_cost").val(sum);
    $(".capital_expenditure_monthtly").attr('budget_cost_data', JSON.stringify(budget_cost_data))
});
$("body").delegate(".capital_expenditure_monthtly", "click", function(event)
{
    var life_sum = 0;
    var budget_cost_data = JSON.parse($(this).attr("budget_cost_data"))
    var budget_index = 0
    $(".life_span_input").each(function(){
        input_val = $(this).val()
        if(input_val)
        {
            if (input_val != 0 && budget_cost_data[budget_index] != 0)
            {
                life_value = budget_cost_data[budget_index] / input_val
                life_value = life_value / 12;
                life_sum = life_sum + life_value
            }
            budget_index = budget_index + 1
        }
    });

    if(life_sum)
    {
        $(".capital_expenditure_monthtly").val(life_sum.toFixed(2));
    }
    else
    {
        $(".capital_expenditure_monthtly").val("*please check Capex Budgets Details Something Went Wrong");
    }

});

$("body").delegate(".remove_budget", "click", function(event)
{
    class_name = $(this).attr('div_class')
    $("."+class_name).remove()
    div_number = parseInt($(".budget_button").attr('div_class')) - 1
    $(".budget_button").attr('div_class', div_number)
});

// SELECT PURCHASE PRICE

$('.select_purchase_price').on("change", function(e)
    {
        select_value = $(this).val()

        if(select_value == "best_case")
        {
            purchase_price = $("#best_case").val()
            $(".purchase_price_value").val(purchase_price)
        }
        if(select_value == "likely_case")
        {
            purchase_price = $("#likely_case").val()
            $(".purchase_price_value").val(purchase_price)
        }
        if(select_value == "worst_case")
        {
            purchase_price = $("#worst_case").val()
            $(".purchase_price_value").val(purchase_price)
        }

    });


// Add Property and Liability Data :-

$("body").delegate(".add_property_liab", "click", function()
{
    form_id = "#" + $(this).attr('form_id')
    buy_price = $('#buy_price').text().trim()
    buy_price = parseFloat(buy_price.replace(buy_price[0], ''))
    down_price = $('#down_price').text().trim()
    down_price = parseFloat(down_price.replace(down_price[0], ''))
    mortgage_price = buy_price - down_price
    form_data = $(form_id).serialize()
    console.log(mortgage_price)
    form_data += "&balance=" + mortgage_price
    console.log(form_data)
    $.ajax(
        {
            data: form_data, // get the form data
            type: 'POST', // GET or POST
            url: '/property_add/', // the file to call
            success: function(response)
            {
                console.log("success")
            }
        });
    $.ajax(
        {
            data: form_data, // get the form data
            type: 'POST', // GET or POST
            url: '/liability_add/', // the file to call
            success: function(response)
            {
                console.log("success")
                location.reload()
            }
        });

});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
