$( document ).ready(function()
{

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
        $(".download_csv_form").empty();
        console.log(csv_data_key)
        formHtml = "<form action=" +  "/download/csv" + " method='post'>" + "<input type='hidden' name='file_name' value='" + file_name + "' >"
                     + "<input type='hidden' name='csv_data_key' value='" + csv_data_key + "' >" + "<input type='hidden' name='csv_data_value' value='" + JSON.stringify(csv_data_value) + "' >"
                     + "</form>"
        var form = $(formHtml);
        $('.download_csv_form').append(form);
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
            var csrfmiddlewaretoken = getCookie('csrftoken');;
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
                if(response.status == "Uploading Failed!! Please Check File Format")
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
