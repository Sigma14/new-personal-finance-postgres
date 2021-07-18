$(document).ready(function()
{
    $('.edit_income').on('click', function(event)
    {
        location.assign($(this).attr('href'))
    });
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

            // Update footer
            $( api.column( 4 ).footer() ).html('$'+pageTotal);
            CategorySpentChart(category_name, category_value);
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
