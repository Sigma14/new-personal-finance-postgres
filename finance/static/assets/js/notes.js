$(document).ready(function()
{

   $(".initial_notes").hide();
   $("#initial_delete").hide();

   function select_note_list(user_notes, select_title)
   {
        $('#my_notes_list').empty()
        selectHTML = ""
        selectHTML += "<label class='form-label'>Notes List</label><select class='form-control' name='select_note' id='select_notes'>"

        $.each(user_notes, function(index, item)
        {
            if(select_title == item[0])
            {
                selectHTML += "<option selected>" + item[0] + "</option>"
                $("#note_title").val(item[0]);
                $("#task-desc").html(item[1])
            }
            else
            {
                selectHTML += "<option>" + item[0] + "</option>"
            }
        });
        selectHTML += "</select>"
        $('#my_notes_list').append(selectHTML)
   }

   function get_notes_list()
   {
        select_title = $("#select_notes").val();
        if (typeof select_title === "undefined")
        {
            select_title = ''
        }
        var csrfmiddlewaretoken = csrftoken;
        $.ajax(
        {
            type: 'POST',
            url: '/add-update/notes',
            data: {
                    'csrfmiddlewaretoken': csrfmiddlewaretoken,
                    'title': '',
                    'notes': '',
                    'select_title': select_title,
                    'notes_method': 'List'
                    },
            success: function(response)
            {
                select_note_list(response.user_notes, select_title)
            }
        });

   }


function add_note_show()
{
        $("#my_notes_list").hide();
        $("#all_notes_tab").show();
        $("#note_title").val("");
        $("#task-desc").text("");
//        $("#text-editor-area").empty("");
//        var spanHTML = ""
//        spanHTML += "<span class='ql-formats mr-0'><button class='ql-bold'></button><button class='ql-italic'></button>"
//        spanHTML += "<button class='ql-underline'></button><button class='ql-align'></button>"
//        spanHTML += "<button class='ql-link'></button></span>"
//        $("#text-editor-area").append(spanHTML);
        $(".delete_notes").hide();
        taskDesc = $('#task-desc');
        if (taskDesc.length) {
                                var todoDescEditor = new Quill('#task-desc', {
                                  bounds: '#task-desc',
                                  modules: {
                                    formula: true,
                                    syntax: true,
                                    toolbar: '.desc-toolbar'
                                  },
                                  placeholder: 'Write Your Notes',
                                  theme: 'snow'
                                });
                              }

        $("#submit_note_btn").text('Add')

}

   $("body").delegate("#new_notes_tab", "click", function(event)
   {
        add_note_show();
   });

   $("body").delegate("#all_notes_tab", "click", function(event)
   {
        $(".delete_notes").show();
        $("#my_notes_list").show();
        $("#submit_note_btn").text('Update');
        $("#initial_delete").show();
        get_notes_list();
   });

   $("body").delegate("#select_notes", "change", function(event)
   {
        get_notes_list();

   });


// ADD AND UPDATE USER NOTES

    $("body").delegate(".add-update-user-notes", "click", function(event)
    {
        title = $("#note_title").val();
        notes = $("#task-desc").html();
        notes_url = $(this).attr('url');
        $(".initial_notes").show();
        select_title = $("#select_notes").val();
        if (typeof select_title === "undefined")
        {
            select_title = ''
        }
        note_method = $("#submit_note_btn").text()
        var csrfmiddlewaretoken = csrftoken;
        $.ajax(
        {
            type: 'POST',
            url: notes_url,
            data: {
                    'csrfmiddlewaretoken': csrfmiddlewaretoken,
                    'title': title,
                    'notes': notes,
                    'select_title': select_title,
                    'notes_method': note_method
                    },
            success: function(response)
            {
               if(response.status == "Added" || response.status == "Updated")
               {
                     Swal.fire({
                                title: response.status + " Successfully Please Check My Notes!!",
                                icon: 'success',
                                customClass: {
                                  confirmButton: 'btn btn-primary'
                                },
                                buttonsStyling: false
                              });
                     console.log(title)
                     select_note_list(response.user_notes, title);
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

    // Delete Notes
    $("body").delegate(".delete_notes", "click", function(event)
    {
        var csrfmiddlewaretoken = csrftoken;
        var select_title = $("#select_notes").val()
        notes_url = $(this).attr('url');
        Swal.fire({
        title: 'Are you sure?',
        text: "You want to delete this Note",
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

        $.ajax(
        {
            type: 'POST',
            url: notes_url,
            data: {
                    'csrfmiddlewaretoken': csrfmiddlewaretoken,
                    'title': '',
                    'notes': '',
                    'select_title': select_title,
                    'notes_method': 'Delete'
                    },
            success: function(response)
            {
               if(response.status == "Deleted Successfully")
               {
                     Swal.fire({
                                title: response.status,
                                icon: 'success',
                                customClass: {
                                  confirmButton: 'btn btn-primary'
                                },
                                buttonsStyling: false
                              });


                     if(response.user_notes.length > 0)
                     {
                         select_note_list(response.user_notes, select_title);
                         get_notes_list();
                     }
                     else
                     {
                        add_note_show();
                        $("#all_notes_tab").removeClass('active');
                        $("#all_notes_tab").hide();
                        $("#new_notes_tab").addClass('active');

                     }
               }
            }
            });

        }
      });

    });


    var csrftoken = getCookie('csrftoken');
    function csrfSafeMethod(method)
    {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup(
    {
        beforeSend: function(xhr, settings)
        {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain)
            {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

});