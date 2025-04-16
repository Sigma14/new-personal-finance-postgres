$(document).ready(function () {
  $("#save_div").hide();
  $("#edit_tr").hide();
  $(".remove_td").hide();

  if ($("#page_url").attr("page_type") == "update_property") {
    var every_month_value = parseInt($(".change_every_month_date").val());
    make_month_list(every_month_value);
    duration_calculate();
    due_date = $(".change_every_month_date").attr("update_rental_date");
    $("#rental_invoice").val(due_date);
    method_name = $("#page_url").attr("method_name");
    if (method_name == "tenant") {
      $(".step").removeClass("active");
      $("#personal-info").removeClass("active");
      $("#personal-info").removeClass("dstepper-block");
      $(".step").addClass("crossed");

      $("#tenant_info").addClass("active");
      $("#tenant_info").removeClass("crossed");
      $(".step-trigger").removeAttr("disabled");
      $("#address-step").addClass("active");
      $("#address-step").addClass("dstepper-block");
    }
  } else {
    $("#rental_prop_form").hide();
    $(".invoice_div").hide();
    $("#first_rental_div").hide();
    $("#edit_invoice_div").hide();
    $("#rental_due_on_div").hide();
  }
  $(".rental_edit_invoice_div").hide();

  $(".edit_income").on("click", function (event) {
    location.assign($(this).attr("href"));
  });

  if ($("#page_name").attr("name") == "Add") {
    $(".property_relate").hide();
  }

  $("#capex_budget").DataTable({
    footerCallback: function (row, data, start, end, display) {
      var api = this.api(),
        data;

      // Remove the formatting to get integer data for summation
      var intVal = function (i) {
        return typeof i === "string"
          ? // Remove any special character except decimal
          i.replace(/[^\d.-]/g, "") * 1
          : typeof i === "number"
            ? i
            : 0;
      };

      // Total over all pages
      all_total = api
        .column(1)
        .data()
        .reduce(function (a, b) {
          currency_name = b[0];
          return intVal(a) + intVal(b);
        }, 0);
      year_total = api
        .column(2)
        .data()
        .reduce(function (a, b) {
          return intVal(a) + intVal(b);
        }, 0);
      year_cost_total = api
        .column(3)
        .data()
        .reduce(function (a, b) {
          return intVal(a) + intVal(b);
        }, 0);
      month_cost_total = api
        .column(4)
        .data()
        .reduce(function (a, b) {
          return intVal(a) + intVal(b);
        }, 0);

      // Update footer
      $(api.column(1).footer()).html(currency_name + all_total);
      $(api.column(2).footer()).html(year_total + "(Year)");
      $(api.column(3).footer()).html(currency_name + year_cost_total);
      $(api.column(4).footer()).html(
        currency_name + month_cost_total.toFixed(2)
      );
    },
    columnDefs: [{ orderable: false, targets: 1 }],
    pageLength: 24,
    lengthMenu: [
      [24, 48, 72],
      [24, 48, 72],
    ],
  });
  $("#revenue_table").DataTable({
    footerCallback: function (row, data, start, end, display) {
      var api = this.api(),
        data;
      column_length = $(this).attr("column_length");
      // Total over this page
      for (let j = 2; j < column_length; j++) {
        pageTotal = api
          .column(j, { page: "current" })
          .data()
          .reduce(function (a, b) {
            currency_name = b[0];
            b = parseFloat(b.replace(currency_name, ""));
            return a + b;
          }, 0);
        $(api.column(j).footer()).html(currency_name + pageTotal);
      }
    },
    columnDefs: [{ orderable: false, targets: 1 }],
    pageLength: 12,
    lengthMenu: [
      [12, 24, 36],
      [12, 24, 36],
    ],
  });

  $("#expense_table").DataTable({
    footerCallback: function (row, data, start, end, display) {
      var api = this.api(),
        data;
      category_name = [];
      category_value = [];
      graph_label = api
        .column(1, { page: "current" })
        .data()
        .reduce(function (a, b) {
          category_name.push(b);
          return b;
        }, 0);

      pageTotal = api
        .column(4, { page: "current" })
        .data()
        .reduce(function (a, b) {
          currency_name = b[0];
          b = parseFloat(b.replace(currency_name, ""));
          category_value.push(b);
          return a + b;
        }, 0);

      category_value = [{ name: "Spent", data: category_value }];
      // Update footer
      $(api.column(4).footer()).html("$" + pageTotal);
      CategorySpentChart(category_name, category_value, "#column-chart");
    },
    columnDefs: [{ orderable: false, targets: 3 }],
    pageLength: 12,
    lengthMenu: [
      [12, 24, 36],
      [12, 24, 36],
    ],
  });

  if ($("#lock_amount_check").prop("checked")) {
    $("#lock_amount_div").show();
  } else {
    $("#lock_amount_div").hide();
  }

  $("#lock_amount_check").on("click", function (event) {
    var check = $(this).prop("checked");
    if (check) {
      $("#lock_amount_div").show();
    } else {
      $("#lock_amount_div").hide();
    }
  });

  // SELECT BILL AND ADD AUTOMATIC AMOUNT
  $("#id_bill").on("change", function (e) {
    bill_id = $(this).val();
    var csrftoken = getCookie("csrftoken");
    $.ajax({
      type: "POST",
      url: "/en/bill/automatic_amount",
      data: {
        bill_id: bill_id,
        csrfmiddlewaretoken: csrftoken,
      },
      dataType: "json",
      success: function (data) {
        $("#id_amount").val(data.bill_amount);
      },
    });
  });

  $("body").delegate(".new_category", "click", function (e) {
    e.preventDefault();
    var category_name = $(this).text().trim();
    var method_name = $(this).attr("method_name");
    var csrftoken = getCookie("csrftoken");
    if (method_name == "group_add") {
      var category_name = $("#category_group_name").val().trim();
    } else {
      $(this).remove();
    }
    Swal.fire({
      title: "Added",
      icon: "success",
      customClass: {
        confirmButton: "btn btn-primary",
      },
      buttonsStyling: false,
    });
    $.ajax({
      type: "POST",
      url: "/en/category_add/",
      data: {
        name: category_name,
        csrfmiddlewaretoken: csrftoken,
      },
      dataType: "json",
      success: function (response) {
        console.log(response);
      },
    });
    location.assign("/budget_add/");
  });

  $("body").delegate(".sub_cat_popup", "click", function (e) {
    var csrftoken = getCookie("csrftoken");

    // Take the value from either id_category or id_categories, Both are different in Transaction add and Budget add.
    let group_id;
    if ($("#id_category").val()) {
      group_id = $("#id_category").val();
    } else if ($("#id_categories").val()) {
      group_id = $("#id_categories").val();
    }
    $.ajax({
      type: "POST",
      url: "/en/subcategory_suggestion",
      data: {
        category_pk: group_id,
        csrfmiddlewaretoken: csrftoken,
      },
      dataType: "json",
      success: function (response) {
        $(".sub_cat_sugg").empty();
        sugg_html = "";
        $.each(response.subcategory_suggestions, function (i, val) {
          sugg_html +=
            "<a style='margin:5px; font-size: 12px;' url='/subcategory_add/" +
            response.category_pk +
            "' class='btn btn-outline-secondary new_subcategory'>" +
            val +
            "&nbsp;<i class='fa fa-plus'></i></a>";
        });
        $("#sub_cat_add_btn").attr(
          "url",
          "/en/subcategory_add/" + response.category_pk
        );
        $(".sub_cat_sugg").append(sugg_html);
      },
    });
  });

  $("body").delegate(".sub_cat_select", "change", function (e) {
    var csrftoken = getCookie("csrftoken");
    group_id = $("#category_group").val();
    $.ajax({
      type: "POST",
      url: "/en/subcategory_suggestion",
      data: {
        category_pk: group_id,
        csrfmiddlewaretoken: csrftoken,
      },
      dataType: "json",
      success: function (response) {
        $(".sub_cat_sugg").empty();
        sugg_html = "";
        $.each(response.subcategory_suggestions, function (i, val) {
          sugg_html +=
            "<a style='margin:5px; font-size: 12px;' url='/subcategory_add/" +
            response.category_pk +
            "' class='btn btn-outline-secondary new_subcategory'>" +
            val +
            "&nbsp;<i class='fa fa-plus'></i></a>";
        });
        $("#sub_cat_add_btn").attr(
          "url",
          "/subcategory_add/" + response.category_pk
        );
        $(".sub_cat_sugg").append(sugg_html);
      },
    });
  });

  // show subcategory of the group
  $("body").delegate(".show_sub_category", "change", function (e) {
    var csrftoken = getCookie("csrftoken");
    group_name = $("#category_group").val();
    $.ajax({
      type: "POST",
      url: "/en/subcategory_list",
      data: {
        category_group: group_name,
        csrfmiddlewaretoken: csrftoken,
      },
      dataType: "json",
      success: function (response) {
        var cat_list = response.subcategories;
        $("#browsers").empty();
        optionHtml = "";
        for (let i = 0; i < cat_list.length; i++) {
          if (i == 0) {
            $("#sub_category_name").val(cat_list[i]);
          }
          optionHtml +=
            "<option value='" +
            cat_list[i] +
            "' data-id='" +
            i +
            "'>" +
            cat_list[i] +
            "</option>";
        }
        console.log(optionHtml);
        $("#browsers").append(optionHtml);
      },
    });
  });

  $("body").delegate(".new_subcategory", "click", function (e) {
    e.preventDefault();
    var category_name = $(this).text().trim();
    var sub_url = $(this).attr("url");
    method_name = $(this).attr("method_name");
    var csrftoken = getCookie("csrftoken");
    if (method_name == "sub_cat_budget") {
      var category_name = $("#sub_category_name").val().trim();
    } else {
      $(this).remove();
    }
    Swal.fire({
      title: "Added",
      icon: "success",
      customClass: {
        confirmButton: "btn btn-primary",
      },
      buttonsStyling: false,
    });
    $.ajax({
      type: "POST",
      url: sub_url,
      data: {
        name: category_name,
        csrfmiddlewaretoken: csrftoken,
      },
      dataType: "json",
      success: function () { },
    });

    location.assign("/budget_add/");
  });

  $("body").delegate(".show_bdgt_exp", "click", function (e) {
    method_name = $(this).attr("method_name");
    $("." + method_name).toggle();
    if (method_name == "expenses_budgets_cls") {
      $(".expense_drp_sign").toggle();
      $(".daily_week_records").hide();
      $(".daily_week_drop").show();
    } else {
      $(".income_drp_sign").toggle();
    }
  });

  $("body").delegate(".show_transaction", "click", function (e) {
    method_name = $(this).attr("method_name");
    $("." + method_name).toggle();
    if (method_name == "transactions_cls") {
      $(".transactions_drp_sign").toggle();
    }
  });

  $("body").delegate(".daily_bdgt_data", "click", function (e) {
    class_name = $(this).attr("class_name");
    $(class_name).toggle();
  });

  // Add Tags for Transactions
  $("body").delegate(".select_tag", "click", function (e) {
    tag_name = $(this).text().trim();
    $("#transaction_tags").val(tag_name);
  });

  $("body").delegate(".add_tag_btn", "click", function (e) {
    tag_name = $("#tag_name").val().trim();
    var csrftoken = getCookie("csrftoken");
    $.ajax({
      type: "POST",
      url: "/en/tag_add/",
      data: {
        name: tag_name,
        csrfmiddlewaretoken: csrftoken,
      },
      dataType: "json",
      success: function (response) {
        console.log(response);
        if (response.status == "success") {
          Swal.fire({
            title: "Added",
            icon: "success",
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          });

          tagHTML =
            "<a style='margin:5px; font-size: 12px;' class='btn btn-outline-secondary close select_tag' data-dismiss='modal' aria-label='Close'>" +
            response.name +
            "&nbsp;<i class='fa fa-plus'></i></a>";
          $(".tag_sugg").append(tagHTML);
        } else {
          Swal.fire({
            title: "Tag already exists",
            icon: "error",
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          });
        }
      },
    });
  });

  // Select Split Category
  $("body").delegate(".select_split_category", "change", function (e) {
    e.preventDefault();
    select_value = $(this).val();
    cat_list = JSON.parse($(".save_split_cat_btn").attr("split_cat_list"));
    amount_list = JSON.parse(
      $(".save_split_cat_btn").attr("split_amount_list")
    );
    len_cat_list = cat_list.length;
    if (select_value) {
      if (cat_list.includes(select_value)) {
        Swal.fire({
          title: "Category already selected",
          icon: "error",
          customClass: {
            confirmButton: "btn btn-primary",
          },
          buttonsStyling: false,
        });
      } else {
        cat_list.push(select_value);
        amount_list.push("0");
        tdHTML =
          "<tr><td><div class='d-flex align-items-center'><div class='font-weight-bolder'>" +
          select_value +
          "</div></div></td><td><div class='d-flex align-items-center'><div class='font-weight-bolder'><input type='text' class='form-control change_split_amount' amount_index='" +
          len_cat_list +
          "' value='0'></div></div></i></button></td><td><button class='btn btn-danger delete_split_cat' cat_value='" +
          select_value +
          "'><i class='fa fa-minus'></td></tr>";
        $(".split_cat_table").append(tdHTML);
        $(".save_split_cat_btn").attr(
          "split_cat_list",
          JSON.stringify(cat_list)
        );
        $(".save_split_cat_btn").attr(
          "split_amount_list",
          JSON.stringify(amount_list)
        );
      }
    }
  });
  $("body").delegate(".delete_split_cat", "click", function (e) {
    cat_value = $(this).attr("cat_value");
    cat_list = JSON.parse($(".save_split_cat_btn").attr("split_cat_list"));
    list_index = cat_list.indexOf(cat_value);
    amount_list = JSON.parse(
      $(".save_split_cat_btn").attr("split_amount_list")
    );
    cat_list.splice(list_index, 1);
    amount_list.splice(list_index, 1);
    $(".save_split_cat_btn").attr("split_cat_list", JSON.stringify(cat_list));
    $(".save_split_cat_btn").attr(
      "split_amount_list",
      JSON.stringify(amount_list)
    );
    $(this).parent().parent().remove();
    var amount_index_cls = $(".change_split_amount");
    var amount_index = 0;
    amount_index_cls.each(function (index) {
      $(this).attr("amount_index", amount_index);
      amount_index += 1;
    });
  });
  $("body").delegate(".change_split_amount", "change", function (e) {
    amount_val = $(this).val();
    amount_index = $(this).attr("amount_index");
    amount_list = JSON.parse(
      $(".save_split_cat_btn").attr("split_amount_list")
    );
    amount_list[amount_index] = amount_val;
    $(".save_split_cat_btn").attr(
      "split_amount_list",
      JSON.stringify(amount_list)
    );
  });

  $("body").delegate(".save_split_cat_btn", "click", function (e) {
    cat_list = JSON.parse($(this).attr("split_cat_list"));
    amount_list = JSON.parse($(this).attr("split_amount_list"));
    method_name = $(this).attr("method_name");
    original_split_amount = parseFloat(
      $("#original_split_amount").text().trim()
    );
    total_sum = amount_list.reduce((acc, val) => acc + parseFloat(val), 0);
    if (original_split_amount != total_sum) {
      Swal.fire({
        title: "Split amount should be equal to original amount",
        icon: "error",
        customClass: {
          confirmButton: "btn btn-primary",
        },
        buttonsStyling: false,
      });
    } else {
      transaction_id = $(this).attr("transaction_id");
      console.log(transaction_id);
      var csrfmiddlewaretoken = getCookie("csrftoken");
      $.ajax({
        type: "POST",
        url: "/en/transaction_split",
        data: {
          original_amount: total_sum,
          category_list: JSON.stringify(cat_list),
          amount_list: JSON.stringify(amount_list),
          transaction_id: transaction_id,
          method_name: method_name,
          csrfmiddlewaretoken: csrfmiddlewaretoken,
        },
        success: function (response) {
          if (response.status == "success") {
            Swal.fire({
              title: "Transaction Split Successfully",
              icon: "success",
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            });
          } else {
            Swal.fire({
              title: response.message,
              icon: "error",
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            });
          }
        },
      });
    }
  });
  // Save Split Transaction Amount

  function inputHTML(formHtml, name, value) {
    formHtml +=
      "<input type='hidden' name='" + name + "' value='" + value + "' >";
    return formHtml;
  }
  // DOWNLOAD RENTAL MODEL PDF

  $(".download_rental_pdf").on("click", function (e) {
    var download_url = "/en" + $(this).attr("url");
    var invest_summary_data = $(this).attr("invest_summary_data");
    var yearly_projection_data = $(this).attr("yearly_projection_data");
    var roi_with_appreciation_dict_investors_data = $(this).attr(
      "roi_with_appreciation_dict_investors_data"
    );
    var roi_dict_investors_data = $(this).attr("roi_dict_investors_data");
    var total_return_investor_data = $(this).attr("total_return_investor_data");
    var net_operating_income_data = $(this).attr("net_operating_income_data");
    var annual_cashflow_data = $(this).attr("annual_cashflow_data");
    var cash_on_cash_return_data = $(this).attr("cash_on_cash_return_data");
    var return_on_investment_data = $(this).attr("return_on_investment_data");
    var debt_cov_ratio_data = $(this).attr("debt_cov_ratio_data");
    var property_expense_data = $(this).attr("property_expense_data");
    var return_investment_data = $(this).attr("return_investment_data");
    var revenue_yearly_data = $(this).attr("revenue_yearly_data");
    var expenses_yearly_data = $(this).attr("expenses_yearly_data");
    var yearly_return_data = $(this).attr("yearly_return_data");
    var property_name = $(this).attr("property_name");
    var property_image = $(this).attr("property_image");

    formHtml = "<form action=" + download_url + " method='post'>";
    formHtml = inputHTML(formHtml, "invest_summary_data", invest_summary_data);
    formHtml = inputHTML(
      formHtml,
      "yearly_projection_data",
      yearly_projection_data
    );
    formHtml = inputHTML(
      formHtml,
      "roi_with_appreciation_dict_investors_data",
      roi_with_appreciation_dict_investors_data
    );
    formHtml = inputHTML(
      formHtml,
      "roi_dict_investors_data",
      roi_dict_investors_data
    );
    formHtml = inputHTML(
      formHtml,
      "total_return_investor_data",
      total_return_investor_data
    );
    formHtml = inputHTML(
      formHtml,
      "net_operating_income_data",
      net_operating_income_data
    );
    formHtml = inputHTML(
      formHtml,
      "annual_cashflow_data",
      annual_cashflow_data
    );
    formHtml = inputHTML(
      formHtml,
      "cash_on_cash_return_data",
      cash_on_cash_return_data
    );
    formHtml = inputHTML(
      formHtml,
      "return_on_investment_data",
      return_on_investment_data
    );
    formHtml = inputHTML(formHtml, "debt_cov_ratio_data", debt_cov_ratio_data);
    formHtml = inputHTML(
      formHtml,
      "property_expense_data",
      property_expense_data
    );
    formHtml = inputHTML(
      formHtml,
      "return_investment_data",
      return_investment_data
    );
    formHtml = inputHTML(formHtml, "revenue_yearly_data", revenue_yearly_data);
    formHtml = inputHTML(
      formHtml,
      "expenses_yearly_data",
      expenses_yearly_data
    );
    formHtml = inputHTML(formHtml, "yearly_return_data", yearly_return_data);
    formHtml = inputHTML(formHtml, "property_name", property_name);
    formHtml = inputHTML(formHtml, "property_image", property_image);

    formHtml += "</form>";
    console.log(formHtml);
    var form = $(formHtml);
    $("#download_rental_pdf_form").append(form);
    form.submit();
  });

  // DOWNLOAD CSV FILE
  $("body").delegate(".download_csv", "click", function (event) {
    var table_id = $(this).attr("table_id");
    $(table_id).DataTable().destroy();
    var file_name = $(this).attr("file_name");
    var table_length = parseInt($(this).attr("table_length"));
    var csv_data_key = $(this).attr("table_heading");
    var download_url = $(this).attr("url");
    var pdf_title = $(this).attr("pdf_title");
    var fun_name = $(this).attr("fun_name");
    var graph_type = $("#download_graph_data").attr("graph_type");
    csv_data_value = [];
    var value_index = 1;
    $(table_id + " >  tbody")
      .find("tr")
      .each(function (i, el) {
        var $tds = $(this).find("td");
        data_value = [];
        for (i = 0; i < table_length; i++) {
          value = $tds.eq(i).text().trim();
          if (value == "") {
            cleared_class = ".cleared" + value_index;
            var cleared = $(cleared_class).val();
            data_value.push(cleared);
          } else {
            data_value.push(value);
          }
        }
        value_index += 1;
        csv_data_value.push(data_value);
      });
    $(table_id).DataTable({ aaSorting: [] });
    console.log(csv_data_value);
    $(".download_csv_form").empty();
    $(".download_pdf_form").empty();

    formHtml =
      "<form action=" +
      download_url +
      " method='post'>" +
      "<input type='hidden' name='file_name' value='" +
      file_name +
      "' >" +
      "<input type='hidden' name='csv_data_key' value='" +
      csv_data_key +
      "' >" +
      "<input type='hidden' name='csv_data_value' value='" +
      JSON.stringify(csv_data_value) +
      "' >";
    if (pdf_title) {
      formHtml +=
        "<input type='hidden' name='pdf_title' value='" + pdf_title + "' >";
    }
    if (graph_type == "transaction-bar") {
      var data_label = $("#download_graph_data").attr("data_label");
      var debit_value = $("#download_graph_data").attr("data_value");
      var credit_value = $("#download_graph_data").attr("credit_value");
      formHtml +=
        "<input type='hidden' name='graph_type' value='" +
        graph_type +
        "' >" +
        "<input type='hidden' name='data_label' value='" +
        data_label +
        "' >" +
        "<input type='hidden' name='data_value' value='" +
        debit_value +
        "' >" +
        "<input type='hidden' name='credit_value' value='" +
        credit_value +
        "' >";
    }
    if (graph_type == "bar" || graph_type == "line" || graph_type == "pie") {
      var data_label = $("#download_graph_data").attr("data_label");
      var data_value = $("#download_graph_data").attr("data_value");
      formHtml +=
        "<input type='hidden' name='graph_type' value='" +
        graph_type +
        "' >" +
        "<input type='hidden' name='data_label' value='" +
        data_label +
        "' >" +
        "<input type='hidden' name='data_value' value='" +
        data_value +
        "' >";
    }
    formHtml += "</form>";
    var form = $(formHtml);
    if (fun_name == "download_csv") {
      $(".download_csv_form").append(form);
    } else {
      $(".download_pdf_form").append(form);
    }
    console.log(formHtml);

    form.submit();
  });

  // Download function for Category list page
  $("body").delegate(".cat-download-csv", "click", function (event) {
    var table_id = $(this).attr("table_id");
    var file_name = $(this).attr("file_name");
    var table_length = 4; // Set the length to 4 to process only the first 4 columns
    var csv_data_key = $(this).attr("table_heading");
    var download_url = $(this).attr("url");
    var pdf_title = $(this).attr("pdf_title");
    var fun_name = $(this).attr("fun_name");
    var graph_type = $("#download_graph_data").attr("graph_type");
    var csv_data_value = [];
    var value_index = 1;

    // Read the data from the rows
    $(table_id + " tr").each(function (i, el) {
      // Exclude rows that contain a "table" element or a "div" element with the class "progress"
      if (
        $(this).find("table").length > 0 ||
        $(this).find("div.progress").length > 0
      ) {
        return true; // Skip to the next iteration
      }

      var $tds = $(this).find("td");
      var data_value = [];
      for (var j = 0; j < table_length; j++) {
        // Change i to j and limit to 4 columns
        var value = $tds.eq(j).text().trim();
        if (value === "") {
          var cleared_class = ".cleared" + value_index;
          var cleared = $(cleared_class).val();
          data_value.push(cleared);
        } else {
          data_value.push(value);
        }
      }
      value_index += 1;
      csv_data_value.push(data_value);
    });

    $(".download_csv_form").empty();
    $(".download_pdf_form").empty();

    var formHtml =
      "<form action='" +
      download_url +
      "' method='post'>" +
      "<input type='hidden' name='file_name' value='" +
      file_name +
      "' >" +
      "<input type='hidden' name='csv_data_key' value='" +
      csv_data_key +
      "' >" +
      "<input type='hidden' name='csv_data_value' value='" +
      JSON.stringify(csv_data_value) +
      "' >";

    if (pdf_title) {
      formHtml +=
        "<input type='hidden' name='pdf_title' value='" + pdf_title + "' >";
    }

    if (graph_type == "transaction-bar") {
      var data_label = $("#download_graph_data").attr("data_label");
      var debit_value = $("#download_graph_data").attr("data_value");
      var credit_value = $("#download_graph_data").attr("credit_value");
      formHtml +=
        "<input type='hidden' name='graph_type' value='" +
        graph_type +
        "' >" +
        "<input type='hidden' name='data_label' value='" +
        data_label +
        "' >" +
        "<input type='hidden' name='data_value' value='" +
        debit_value +
        "' >" +
        "<input type='hidden' name='credit_value' value='" +
        credit_value +
        "' >";
    } else if (
      graph_type == "bar" ||
      graph_type == "line" ||
      graph_type == "pie"
    ) {
      var data_label = $("#download_graph_data").attr("data_label");
      var data_value = $("#download_graph_data").attr("data_value");
      formHtml +=
        "<input type='hidden' name='graph_type' value='" +
        graph_type +
        "' >" +
        "<input type='hidden' name='data_label' value='" +
        data_label +
        "' >" +
        "<input type='hidden' name='data_value' value='" +
        data_value +
        "' >";
    }

    formHtml += "</form>";
    var form = $(formHtml);

    if (fun_name == "download_csv") {
      $(".download_csv_form").append(form);
    } else {
      $(".download_pdf_form").append(form);
    }

    form.submit();
  });

  $("body").delegate(".delete_button", "click", function (event) {
    name = $(this).attr("delete_name");
    del_method = $(this).attr("del_method");
    text_msg = "Once deleted the " + name + ", cannot be recovered.";
    if (del_method == "account_delete") {
      text_msg += "All the transactions related to this account also deleted.";
    }
    if (del_method == "income_delete") {
      text_msg +=
        "All the transactions related to this income source also deleted and total transaction amount added to selected income account.";
    }
    if (del_method == "Goals") {
      text_msg +=
        "All the allocated or lock amount of this goal will be added into their fund account";
    }
    if (del_method == "Funds") {
      text_msg +=
        "All the goals related to this fund also delete and freeze amount of this fund will be added into their bank account";
    }

    if (del_method == "category_delete") {
      text_msg +=
        "All the transactions, bills and budgets related to this category also deleted.";
    }
    if (del_method == "bill_delete") {
      text_msg += "All the transactions, paid or unpaid bills also deleted.";
    }
    if (del_method == "selected_bill_delete") {
      text_msg += "All the transactions related to this bills also deleted.";
    }
    if (del_method == "budget_delete") {
      text_msg +=
        "All the past and current transactions related to this budget also deleted.";
    }

    delete_url = $(this).attr("url");
    Swal.fire({
      title: "Delete Screener",
      text: text_msg,
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Yes, delete it!",
      customClass: {
        confirmButton: "btn btn-primary",
        cancelButton: "btn btn-outline-danger ml-1",
      },
      buttonsStyling: false,
    }).then(function (result) {
      if (result.value) {
        var csrfmiddlewaretoken = getCookie("csrftoken");
        $.ajax({
          type: "POST",
          url: delete_url,
          data: {
            csrfmiddlewaretoken: csrfmiddlewaretoken,
          },
          success: function (response) {
            if (response.status == "Successfully") {
              Swal.fire({
                title: "Deleted",
                icon: "success",
                customClass: {
                  confirmButton: "btn btn-primary",
                },
                buttonsStyling: false,
              });
            }
            if (response.path == "None") {
              location.reload();
            } else {
              location.assign(response.path);
            }
          },
        });
      }
    });
  });

  // SAVE UPLOAD TRANSACTION FILe

  $("#upload_transaction_form").submit(function () {
    var form = $("#upload_transaction_form")[0];
    var data = new FormData(form);
    $.ajax({
      type: "post",
      enctype: "multipart/form-data",
      url: "/en/transaction_upload",
      data: data,
      processData: false,
      contentType: false,
      cache: false,
      success: function (response) {
        if (response.status == "File Uploaded") {
          Swal.fire({
            title: response.status,
            icon: "success",
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          });
          location.reload();
        } else {
          Swal.fire({
            title: response.status,
            icon: "error",
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          });
        }
      },
    });
    return false;
  });

  $(".check_primary").on("click", function (e) {
    $(".end_month").toggle();
    var month_label = $("#check_month").text();
    if (month_label == "Start Month") {
      $("#check_month").text("Month");
    } else {
      $("#check_month").text("Start Month");
    }
  });

  // Fund Overtime

  $(".fund_overtime").on("click", function (e) {
    var account_name = $(this)
      .closest("td")
      .next()
      .find("#acc_name")
      .attr("account_name");
    var csrfmiddlewaretoken = getCookie("csrftoken");
    $.ajax({
      type: "POST",
      url: "/en/fund_overtime",
      data: {
        account_name: account_name,
        csrfmiddlewaretoken: csrfmiddlewaretoken,
      },
      success: function (response) {
        AccountsChart(
          response.fund_data,
          response.date_range_list,
          response.max_value,
          response.min_value
        );
      },
    });
  });

  // Budget Month Filter budget_month_filter

  $(".budget_period_filter").on("change", function (e) {
    $("#period_filter_form").submit();
  });

  //  User Budget Filter

  $(".user_budget_filter").on("change", function (e) {
    $("#user_budget_form").submit();
  });

  //  Function for Available user budgets dropdown
  $("#user_budget_name").on("change", function (e) {
    location.assign($("#user_budget_name").val());
  });

  //  Function for Setting a Budget as Default
  $(".default_bgt_select").on("change", function (e) {
    form_index = $(this).data("form-id");
    $("#defaultBudgetForm" + form_index).submit();
  });

  // User Budget Update function
  $("#bgt-update-btn").on("click", function (e) {
    e.preventDefault();
    console.log(window.location.href);
    action_url = $(this).attr("url");
    console.log(action_url);
    updated_name = $("#user_budget_input").val();
    console.log("changed name", updated_name);
    var csrf_token = getCookie("csrftoken");

    $.ajax({
      data: {
        user_budget_name: updated_name,
        csrfmiddlewaretoken: csrf_token,
      },
      type: "POST",
      url: action_url,
      success: function (response) {
        console.log(response);
        if (response.status === "true") {
          Swal.fire({
            title: "Updated Successfully",
            icon: "success",
            text: response.message,
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          }).then(function () {
            console.log("Swal closed, attempting to reload");
            // Ensure this reload doesn't trigger any unintended navigation
            location.reload(); // Reload the page after success
          });
        } else {
          Swal.fire({
            title: "Saving Failed",
            icon: "error",
            text: response.message,
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          });
        }
      },
    });
    return false;
  });

  // Budget type selection

  $("body").delegate(".select_cmp_type", "change", function (e) {
    type = $(this).val();
    if (type == "Incomes") {
      $(".select_income_budget").show();
      $(".select_exp_budget").hide();
    } else {
      $(".select_income_budget").hide();
      $(".select_exp_budget").show();
    }
  });

  // Budget Transactions

  $("body").delegate(".show_bdgt_trans", "click", function (e) {
    method_name = $(this).attr("method_name");
    $("." + method_name).toggle();
  });

  // RENTAL PROPERTY JS

  // ADD Units Fields
  $("body").delegate(".add_unit_button", "click", function (event) {
    div_number = $(this).attr("div_class");
    class_name = "unit_div_" + div_number;
    extra_div_number = parseInt(div_number) + 1;
    parent_div = parseInt(div_number) - 1;
    console.log(parent_div);
    var inputHtml =
      "<div class='col-12 " +
      class_name +
      " '>" +
      "<div class='form-group row'>" +
      "<div class='col-sm-3 col-form-label'>";
    inputHtml +=
      "<label for='fname-icon'>" +
      "Unit" +
      div_number +
      "</label>" +
      "</div>" +
      "<div class='col-sm-7'>";
    inputHtml +=
      "<div class='input-group input-group-merge'>" +
      "<input type='text' class='form-control' name='others_revenue_cost' required placeholder='Unit" +
      div_number +
      "' />";
    inputHtml +=
      "</div>" +
      "</div>" +
      "<div class='col-sm-2 extra_unit_div_" +
      div_number +
      "'>";
    inputHtml +=
      "<button class='btn btn-primary add_unit_button' div_class='" +
      extra_div_number +
      "' title='Add Unit'>";
    inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>";
    $(inputHtml).insertAfter(".unit_div_" + parent_div);
    deleteButton =
      "<button class='btn btn-danger remove_unit_button' div_number='" +
      parent_div +
      "' div_class='" +
      class_name +
      "' title='Delete Unit' style='margin-left:5px;' ><i class='fa fa-minus'></i></button></div></div></div>";
    $(".extra_unit_div_" + div_number).append(deleteButton);
    $(".extra_unit_div_" + parent_div).empty();
  });

  $("body").delegate(".remove_unit_button", "click", function (event) {
    div_number = parseInt($(this).attr("div_number"));
    unit_number = parseInt($(".last_unit").attr("unit_number"));
    if (div_number > unit_number) {
      extra_div_number = div_number + 1;
      parent_div = div_number - 1;
      change_class = "unit_div_" + div_number;
      inputHtml =
        "<button class='btn btn-primary add_unit_button' div_class='" +
        extra_div_number +
        "' title='Add Unit'>";
      inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>";
      inputHtml +=
        "<button class='btn btn-danger remove_unit_button' div_number='" +
        parent_div +
        "' div_class='" +
        change_class +
        "' title='Delete Unit' style='margin-left:5px;' ><i class='fa fa-minus'></i></button></div></div></div>";
    } else {
      inputHtml =
        "<button class='btn btn-primary add_unit_button' div_class='" +
        3 +
        "' title='Add Unit'>";
      inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>";
    }
    $(".extra_unit_div_" + div_number).append(inputHtml);
    class_name = $(this).attr("div_class");
    $("." + class_name).remove();
  });

  $("body").delegate(".add_other_cost", "click", function (event) {
    main_class = $(this).attr("main_class");
    extra_class = $(this).attr("extra_class");
    input_name = $(this).attr("input_name");
    div_number = $(this).attr("div_class");
    class_name = main_class + div_number;
    extra_div_number = parseInt(div_number) + 1;
    parent_div = parseInt(div_number) - 1;
    var inputHtml =
      "<div class='col-12 " +
      class_name +
      " '>" +
      "<div class='form-group row'>" +
      "<div class='col-sm-3 col-form-label'>";
    inputHtml +=
      "<input type='text' class='form-control' value='Other(Please Specify)' name='" +
      input_name +
      "' required placeholder='Other(Please Specify)'/> " +
      "</div>" +
      "<div class='col-sm-7' style='padding-top:7px;'>";
    inputHtml +=
      "<div class='input-group input-group-merge'>" +
      "<input type='text' class='form-control' name='" +
      input_name +
      "' required placeholder='-' />";
    inputHtml +=
      "</div>" +
      "</div>" +
      "<div class='col-sm-2 " +
      extra_class +
      div_number +
      "' style='padding-top:7px;'>";
    inputHtml +=
      "<button class='btn btn-primary add_other_cost' input_name='" +
      input_name +
      "' main_class='" +
      main_class +
      "' extra_class='" +
      extra_class +
      "' div_class='" +
      extra_div_number +
      "' title='Add Other'>";
    inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>";
    $(inputHtml).insertAfter("." + main_class + parent_div);
    deleteButton =
      "<button class='btn btn-danger remove_other_cost' input_name='" +
      input_name +
      "' div_number='" +
      parent_div +
      "' main_class='" +
      main_class +
      "' extra_class='" +
      extra_class +
      "' div_class='" +
      class_name +
      "' title='Delete' style='margin-left:5px;' ><i class='fa fa-minus'></i></button></div></div></div>";
    $("." + extra_class + div_number).append(deleteButton);
    $("." + extra_class + parent_div).empty();
  });

  $("body").delegate(".remove_other_cost", "click", function (event) {
    div_number = parseInt($(this).attr("div_number"));
    main_class = $(this).attr("main_class");
    extra_class = $(this).attr("extra_class");
    input_name = $(this).attr("input_name");

    if (input_name == "other_utilities") {
      last_div = parseInt($(".last_utility").attr("last_div")) + 1;
    }
    if (input_name == "other_cost") {
      last_div = parseInt($(".last_cost").attr("last_div")) + 1;
    }
    if (input_name == "other_expenses") {
      last_div = parseInt($(".last_expenses").attr("last_div")) + 1;
    }

    if (div_number >= last_div) {
      extra_div_number = div_number + 1;
      parent_div = div_number - 1;
      change_class = main_class + div_number;
      inputHtml =
        "<button class='btn btn-primary add_other_cost' input_name='" +
        input_name +
        "' main_class='" +
        main_class +
        "' extra_class='" +
        extra_class +
        "' div_class='" +
        extra_div_number +
        "' title='Add Other'>";
      inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>";
      inputHtml +=
        "<button class='btn btn-danger remove_other_cost' input_name='" +
        input_name +
        "' div_number='" +
        parent_div +
        "' main_class='" +
        main_class +
        "' extra_class='" +
        extra_class +
        "' div_class='" +
        change_class +
        "' title='Delete' style='margin-left:5px;' ><i class='fa fa-minus'></i></button></div></div></div>";
    } else {
      inputHtml =
        "<button class='btn btn-primary add_other_cost' input_name='" +
        input_name +
        "' main_class='" +
        main_class +
        "' extra_class='" +
        extra_class +
        "' div_class='" +
        last_div +
        "' title='Add Other'>";
      inputHtml += "<i class='fa fa-plus'></i></button></div></div></div>";
    }
    $("." + extra_class + div_number).append(inputHtml);
    class_name = $(this).attr("div_class");
    $("." + class_name).remove();
  });

  $("body").delegate(".investor_button", "click", function (event) {
    div_number = parseInt($(this).attr("div_class"));
    $(this).attr("div_class", div_number + 1);
    var inputHtml =
      "<div class='col-12 investor_div_" +
      div_number +
      "' >" +
      "<div class='form-group row'>" +
      "<div class='col-sm-2 col-form-label'>";
    inputHtml +=
      "<label for='fname-icon'>Name</label></div><div class='col-sm-4'><div class='input-group input-group-merge'>";
    inputHtml +=
      "<input type='text' class='form-control' name='investor_detail' required placeholder='Investor Name'/></div></div>";
    inputHtml +=
      "<div class='col-sm-2 col-form-label'><label for='fname-icon'>Capital Contribution</label></div><div class='col-sm-3'>";
    inputHtml +=
      "<div class='input-group input-group-merge'><input type='text' class='form-control' name='investor_detail' required placeholder='Investor Name'/></div></div>";
    inputHtml +=
      "<div class='col-sm-1'><button class='btn btn-danger remove_investor' div_class='investor_div_" +
      div_number +
      "' title='Delete' style='margin-left:5px;' ><i class='fa fa-minus'></i></button>";
    inputHtml += "</div></div></div>";

    $(inputHtml).insertBefore("#investor_add_div");
  });

  $("body").delegate(".budget_button", "click", function (event) {
    div_number = parseInt($(this).attr("div_class"));
    $(this).attr("div_class", div_number + 1);
    var inputHtml =
      "<div class='col-12 budget_div_" +
      div_number +
      "' >" +
      "<div class='form-group row'>" +
      "<div class='col-sm-3 col-form-label'>";
    inputHtml +=
      "<input type='text' class='form-control' name='other_budget' placeholder='Name'/></div><div class='col-sm-4' style='padding-top:7px;'><div class='input-group input-group-merge'>";
    inputHtml +=
      "<input type='text' class='form-control budget_cost' name='other_budget' placeholder='Total Replacement Cost'/></div></div>";
    inputHtml += "<div class='col-sm-4' style='padding-top:7px;' >";
    inputHtml +=
      "<div class='input-group input-group-merge'><input type='text' class='form-control' name='other_budget' placeholder='Lifespan (years) '/></div></div>";
    inputHtml +=
      "<div class='col-sm-1' style='padding-top:7px;'><button class='btn btn-danger remove_budget' div_class='budget_div_" +
      div_number +
      "' title='Delete' style='margin-left:5px;' ><i class='fa fa-minus'></i></button>";
    inputHtml += "</div></div></div>";

    $(inputHtml).insertBefore("#budget_add_div");
  });

  $("body").delegate(".remove_investor", "click", function (event) {
    class_name = $(this).attr("div_class");
    $("." + class_name).remove();
    div_number = parseInt($(".investor_button").attr("div_class")) - 1;
    $(".investor_button").attr("div_class", div_number);
  });

  $("body").delegate(".budget_cost", "change", function (event) {
    var sum = 0;
    var budget_cost_data = [];
    $(".budget_cost").each(function () {
      input_val = $(this).val();
      if (input_val) {
        budget_cost_data.push(input_val);
        sum = sum + parseFloat(input_val);
      }
    });
    $(".total_budget_cost").val(sum);
    $(".capital_expenditure_monthtly").attr(
      "budget_cost_data",
      JSON.stringify(budget_cost_data)
    );
  });
  $("body").delegate(
    ".capital_expenditure_monthtly",
    "click",
    function (event) {
      var life_sum = 0;
      var budget_cost_data = JSON.parse($(this).attr("budget_cost_data"));
      var budget_index = 0;
      $(".life_span_input").each(function () {
        input_val = $(this).val();
        if (input_val) {
          if (input_val != 0 && budget_cost_data[budget_index] != 0) {
            life_value = budget_cost_data[budget_index] / input_val;
            life_value = life_value / 12;
            life_sum = life_sum + life_value;
          }
          budget_index = budget_index + 1;
        }
      });

      if (life_sum) {
        $(".capital_expenditure_monthtly").val(life_sum.toFixed(2));
      } else {
        $(".capital_expenditure_monthtly").val(
          "*please check Capex Budgets Details Something Went Wrong"
        );
      }
    }
  );

  $("body").delegate(".remove_budget", "click", function (event) {
    class_name = $(this).attr("div_class");
    $("." + class_name).remove();
    div_number = parseInt($(".budget_button").attr("div_class")) - 1;
    $(".budget_button").attr("div_class", div_number);
  });

  // SELECT PURCHASE PRICE

  $(".select_purchase_price").on("change", function (e) {
    select_value = $(this).val();

    if (select_value == "best_case") {
      purchase_price = $("#best_case").val();
      $(".purchase_price_value").val(purchase_price);
    }
    if (select_value == "likely_case") {
      purchase_price = $("#likely_case").val();
      $(".purchase_price_value").val(purchase_price);
    }
    if (select_value == "worst_case") {
      purchase_price = $("#worst_case").val();
      $(".purchase_price_value").val(purchase_price);
    }
  });

  // Add Property and Liability Data :-

  $("body").delegate(".add_property_liab", "click", function () {
    var method_type = $(this).attr("method_type");
    form_id = "#" + $(this).attr("form_id");
    var form_data = $(form_id).serialize();

    if (method_type == "add_prop") {
      $(form_id).submit();
    } else {
      buy_price = $("#buy_price").text().trim();
      buy_price = parseFloat(buy_price.replace(buy_price[0], ""));
      down_price = $("#down_price").text().trim();
      down_price = parseFloat(down_price.replace(down_price[0], ""));
      mortgage_price = buy_price - down_price;
      console.log(form_data);
      form_data += "&balance=" + mortgage_price;
      $.ajax({
        data: form_data, // get the form data
        type: "POST", // GET or POST
        url: "/en/liability_add/", // the file to call
        success: function (response) {
          location.reload();
        },
      });
    }
  });

  // Property Next Functionality
  $("body").delegate(".next_click_prop", "click", function () {
    curr_id = $(this).attr("curr_id");
    next_id = $(this).attr("next_id");
    next_trigger_id = $(this).attr("next_trigger_id");
    next_data = $(this).attr("next_data");

    $(curr_id).removeClass("active");
    $(".content").removeClass("active");
    $(".content").removeClass("dstepper-block");
    $(".step-trigger").attr("aria-selected", "false");
    $(next_id).addClass("active");
    $(next_trigger_id).attr("aria-selected", "true");
    $(next_id).removeClass("dstepper-block");
    $(".step").removeClass("crossed");
    $(curr_id).addClass("crossed");
    $(next_data).addClass("active");
  });

  // Property Unit Details

  $("body").delegate(".change_quantity", "change", function (event) {
    quantity_id = $(this).attr("st_id");
    input_value = $(this).val();
    $(quantity_id).text(input_value);
  });

  $("body").delegate(".remove_another_prop_unit", "click", function (event) {
    var div_class = "." + $(this).attr("div_class");
    $(".add_another_prop_unit").attr(
      "div_class",
      div_class[parseInt(div_class.length) - 1]
    );
    $(div_class).remove();
  });

  // ADD Another Property Units
  $("body").delegate(".add_another_prop_unit", "click", function (event) {
    div_class = parseInt($(this).attr("div_class"));
    var check_id = div_class - 1;
    var detailHtml = "";
    detailHtml +=
      "<div class='col-lg-3 col-md-3 unit_ex" +
      div_class +
      "'><div class='form-group'><input type='text' class='form-control unit_names' name='unit_name' placeholder='Suite 101' required/></div></div>";
    detailHtml +=
      "<div class='col-lg-8 col-md-8 unit_ex" +
      div_class +
      "'><div class='form-group'><div class='collapse-default'><div class='card'>";
    detailHtml +=
      "<div id='headingCollapse" +
      div_class +
      "' class='card-header' data-toggle='collapse' role='button' data-target='#collapse" +
      div_class +
      "' aria-expanded='false' aria-controls='collapse1'><span><i class='fa fa-bed' aria-hidden='true'></i><strong id='bed_quantity" +
      div_class +
      "'>1</strong></span><span><i class='fa fa-bath' aria-hidden='true'></i><strong id='bath_quantity" +
      div_class +
      "'>1</strong></span><span><i class='fa fa-area-chart' aria-hidden='true'></i><strong id='feet_quantity" +
      div_class +
      "'>1</strong></span></div>";
    detailHtml +=
      "<div id='collapse" +
      div_class +
      "' role='tabpanel' aria-labelledby='headingCollapse1' class='collapse'><div class='card-body'><div class='col-12'><div class='row match-height'>";
    detailHtml +=
      "<div class='col-lg-4 col-md-12'><div class='form-group'><label for='bed_room_quantity'>BedRooms</label><input id='bed_room_quantity' type='text' value='1' st_id='#bed_quantity" +
      div_class +
      "' class='form-control change_quantity' name='bed_room_quantity' required/></div></div>";
    detailHtml +=
      "<div class='col-lg-4 col-md-12'><div class='form-group'><label for='bath_room_quantity'>Bathrooms</label><input id='bath_room_quantity' type='text' class='form-control change_quantity' st_id='#bath_quantity" +
      div_class +
      "' value='1' name='bath_room_quantity' required/></div></div>";
    detailHtml +=
      "<div class='col-lg-4 col-md-12'><div class='form-group'><label for='square_feet'>Square Feet</label><input id='square_feet' type='text' class='form-control change_quantity' st_id='#feet_quantity" +
      div_class +
      "' value='1' name='square_feet' required/></div></div><div class='col-12'><div class='form-group'><label for='square_feet'>Rent Includes</label></div></div>";
    detailHtml +=
      "<div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='electricity_check" +
      check_id +
      "' class='custom-control-input select_category' id='customCheck1" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck1" +
      div_class +
      "'>Electricity</label></div></div></div>";
    detailHtml +=
      "<div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='gas_check" +
      check_id +
      "' class='custom-control-input select_category' id='customCheck2" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck2" +
      div_class +
      "'>Gas</label></div></div></div><div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='water_check' class='custom-control-input select_category' id='customCheck3" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck3" +
      div_class +
      "'>Water</label></div></div></div>";
    detailHtml +=
      "<div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='int_cable_check" +
      check_id +
      "' class='custom-control-input select_category' id='customCheck4" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck4" +
      div_class +
      "'>Internet and Cable</label></div></div></div><div class='col-12'><div class='form-group'><label>Amenities</label></div></div>";
    detailHtml +=
      "<div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='ac_check" +
      check_id +
      "' class='custom-control-input select_category' id='customCheck5" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck5" +
      div_class +
      "'>A/C</label></div></div></div>";
    detailHtml +=
      "<div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='pool_check" +
      check_id +
      "' class='custom-control-input select_category' id='customCheck6" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck6" +
      div_class +
      "'>Pool</label></div></div></div>";
    detailHtml +=
      "<div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='pets_check" +
      check_id +
      "' class='custom-control-input select_category' id='customCheck7" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck7" +
      div_class +
      "'>Pets Allowed</label></div></div></div>";
    detailHtml +=
      "<div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='furnished_check" +
      check_id +
      "' class='custom-control-input select_category' id='customCheck8" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck8" +
      div_class +
      "'>Furnished</label></div></div></div>";
    detailHtml +=
      "<div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='balcony_check" +
      check_id +
      "' class='custom-control-input select_category' id='customCheck9" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck9" +
      div_class +
      "'>Balcony/Deck</label></div></div></div>";
    detailHtml +=
      "<div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='hardwood_check" +
      check_id +
      "' class='custom-control-input select_category' id='customCheck10" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck10" +
      div_class +
      "'>Hardwood Floor</label></div></div></div>";
    detailHtml +=
      "<div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='wheel_check" +
      check_id +
      "' class='custom-control-input select_category' id='customCheck11" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck11" +
      div_class +
      "'>Wheelchair Access</label></div></div></div>";
    detailHtml +=
      "<div class='col-lg-3 col-md-3'><div class='form-group'><div class='custom-control custom-checkbox'><input type='checkbox' name='parking_check" +
      check_id +
      "' class='custom-control-input select_category' id='customCheck12" +
      div_class +
      "' /><label class='custom-control-label' for='customCheck12" +
      div_class +
      "'>Off-street Parking</label></div></div></div></div></div></div></div></div></div></div></div></div></div>";
    detailHtml +=
      "<div class='col-lg-1 col-md-1 unit_ex" +
      div_class +
      "'><div class='form-group'><button type='button' class='btn btn-danger remove_another_prop_unit' div_class='unit_ex" +
      div_class +
      "' title='Delete Unit' style='margin-left:5px;' ><i class='fa fa-minus'></i></button></div></div>";
    $("#add_property_unit").before(detailHtml);
    $(this).attr("div_class", div_class + 1);
  });

  // Selected Terms Changes

  function make_date_str(date_value) {
    var month_date = date_value.toLocaleString("default", { month: "long" });
    var result_date =
      month_date + " " + date_value.getDate() + ", " + date_value.getFullYear();
    console.log(result_date);
    return result_date;
  }

  function make_month_list(every_month_value) {
    $("#rental_invoice").empty();
    lease_start_date = new Date($("#lease_start_date").val());
    lease_end_date = new Date($("#lease_end_date").val());
    var result_start_date = make_date_str(lease_start_date);
    var result_end_date = make_date_str(lease_end_date);
    var actualDate = new Date(result_start_date);
    var nextMonth = new Date(
      actualDate.getFullYear(),
      actualDate.getMonth() + 1,
      every_month_value
    );
    optionHtml = "<option>Select</option>";
    var invoice_length = [];
    if (nextMonth < lease_end_date) {
      for (var i = 0; nextMonth < lease_end_date; i++) {
        if (i == 0) {
          console.log("iii", i);
          optionHtml += "<option>" + result_start_date + "</option>";
          invoice_length.push(result_start_date);
        }
        var actualDate = make_date_str(nextMonth);
        optionHtml += "<option>" + actualDate + "</option>";
        invoice_length.push(actualDate);
        var actualDate = new Date(actualDate);
        var nextMonth = new Date(
          actualDate.getFullYear(),
          actualDate.getMonth() + 1,
          every_month_value
        );
      }
    } else {
      optionHtml += "<option>" + result_start_date + "</option>";
      invoice_length.push(result_start_date);
      var nextMonth = new Date(
        actualDate.getFullYear(),
        actualDate.getMonth(),
        every_month_value
      );
      if (nextMonth < lease_end_date) {
        var actualDate = make_date_str(nextMonth);
        optionHtml += "<option>" + actualDate + "</option>";
        invoice_length.push(actualDate);
      }
    }

    $("#rental_invoice").append(optionHtml);
    $("#rental_invoice").attr("invoice_list", JSON.stringify(invoice_length));
    $("#first_rental_div").show();
    return invoice_length;
  }

  $("body").delegate(".change_every_month_date", "change", function (event) {
    var every_month_value = parseInt($(this).val());
    make_month_list(every_month_value);
  });

  function make_rent_duration(lease_start_date, lease_end_date) {
    var date1 = new Date(lease_start_date);
    var date2 = new Date(lease_end_date);
    var diff = new Date(date2.getTime() - date1.getTime());
    year_no = diff.getUTCFullYear() - 1970;
    month_no = diff.getUTCMonth();
    day_no = diff.getUTCDate() - 1;
    rent_duration = "";
    if (year_no > 0) {
      if (year_no > 1) {
        rent_duration += year_no + " Years ";
      } else {
        rent_duration += year_no + " Year ";
      }
    }
    if (month_no > 0) {
      if (month_no > 1) {
        rent_duration += month_no + " Months ";
      } else {
        rent_duration += month_no + " Month ";
      }
    }
    if (day_no > 0) {
      if (day_no > 1) {
        rent_duration += day_no + " Days ";
      } else {
        rent_duration += day_no + " Day ";
      }
    }
    return rent_duration;
  }

  function duration_calculate() {
    lease_start_date = $("#lease_start_date").val();
    lease_end_date = $("#lease_end_date").val();
    var result_start_date = make_date_str(new Date(lease_start_date));
    var result_end_date = make_date_str(new Date(lease_end_date));
    $(".rent_start_date").text(result_start_date);

    if (new Date(lease_start_date) >= new Date(lease_end_date)) {
      $("#rent_duration").text("Oops! Could not calculate duration!");
      $("#rent_duration").addClass("text-danger");
      $(".rent_end_date").text("*Please choose greater date from start date");
      $(".rent_end_date").addClass("text-danger");
    } else {
      $("#rent_duration").removeClass("text-danger");
      $(".rent_end_date").removeClass("text-danger");
      if ($(".rent_end_date").text() != "Month-to-Month") {
        $(".rent_end_date").text(result_end_date);
        rent_duration = make_rent_duration(lease_start_date, lease_end_date);
        $("#rent_duration").text(rent_duration);
      } else {
        $("#rent_duration").text("1 Month");
      }
    }
  }

  $("body").delegate(".change_date", "change", function (event) {
    $("#rental_invoice").empty();
    $(".due_date_rental").text("N/A");
    $(".change_every_month_date").val("Select");
    duration_calculate();
  });

  $("body").delegate(".select_terms", "click", function (event) {
    $(".select_terms").removeClass("active");
    select_id = $(this).attr("id");
    lease_start_date = $("#lease_start_date").val();
    lease_end_date = $("#lease_end_date").val();
    var result_start_date = make_date_str(new Date(lease_start_date));
    var result_end_date = make_date_str(new Date(lease_end_date));
    $("#invoice_body_div").empty();
    $("#rental_invoice").empty();
    if (select_id == "month_term_tab") {
      $(".lease_end_date_remove").hide();
      $(".term_name").text("Month-to-Month");
      $(".rent_start_date").text(result_start_date);
      $(".rent_end_date").text("Month-to-Month");
      $("#rent_duration").text("1 Month");
      $(".change_every_month_date").val("Select");
      month_start_data = new Date(lease_start_date);
      month_year = month_start_data.getFullYear() + 1;
      month_no = month_start_data.getMonth();
      month_date = month_start_data.getDate();
      var month_end_date = month_year + "-" + month_no + "-" + month_date;
      $("#lease_end_date").val(month_end_date);
      $("#rental_term_name").val("Month-to-Month");
    } else {
      $(".lease_end_date_remove").show();
      $(".term_name").text("Fixed Term");
      $(".rent_start_date").text(result_start_date);
      $(".rent_end_date").text(result_end_date);
      rent_duration = make_rent_duration(lease_start_date, lease_end_date);
      $("#rent_duration").text(rent_duration);
      $("#rental_term_name").val("Fixed Term");
    }
  });
  //Deposit Amount Changes

  $("body").delegate(".deposit_amount_input", "change", function (event) {
    deposit_amount = $(this).val();
    currency_symbol = $("#currency_name").val();
    $(".deposit_amount_field").text(currency_symbol + deposit_amount);
  });

  $("#already_deposit_check").on("click", function (event) {
    var check = $(this).prop("checked");
    if (check) {
      $(".deposit_check").text("Already Collected");
    } else {
      $(".deposit_check").text("");
    }
  });

  //Rental Amount Changes

  $("body").delegate(".change_rent_amount", "change", function (event) {
    rental_amount = $(this).val();
    currency_symbol = $("#currency_name").val();
    $(".rent_amount_month").text(currency_symbol + rental_amount + "/month");
    $("#rental_invoice").empty();
    $(".change_every_month_date").val("Select");
    $(".due_date_rental").text("N/A");
    $("#rental_due_on_div").show();
  });

  // Add Units Options
  $("body").delegate(".unit_names", "change", function (event) {
    var inputs = $(".unit_names");
    var input_unit_val = $(this).val();
    $("#unit_options").empty();
    optionHtml = "";
    for (var i = 0; i < inputs.length; i++) {
      var unit_val = $(inputs[i]).val();
      if (input_unit_val == unit_val && i < inputs.length - 1) {
        $(this).val("");
        Swal.fire({
          title: "Unit name already added",
          icon: "error",
          customClass: {
            confirmButton: "btn btn-primary",
          },
          buttonsStyling: false,
        });
      } else {
        optionHtml += "<option>" + unit_val + "</option>";
      }
    }

    $("#unit_options").append(optionHtml);
    var unit_name = $("#unit_options").val();
    $(".unit_heading").text(unit_name);
  });

  // Select Units For Tenants and Rental
  $("body").delegate(".unit_selected", "change", function (event) {
    var unit_name = $(this).val();
    $(".unit_heading").text(unit_name);
  });

  // Select First Rental Amount Due
  $("body").delegate("#rental_invoice", "change", function (event) {
    var due_date = $(this).val();
    var term_name = $(".term_name").text();
    var rent_amount = parseFloat($(".change_rent_amount").val());
    //    var due_date = $("#rental_invoice option:selected").html();
    $(".due_date_rental").text(due_date);
    var invoice_arr = JSON.parse($("#rental_invoice").attr("invoice_list"));
    var invoice_total_amount = 0;
    var invoice_total_record = 0;
    $("#invoice_body_div").empty();
    tableHtml = "";
    var invoice_date_list = [];
    var invoice_amount_list = [];

    if (term_name == "Fixed Term") {
      for (i = 0; i < invoice_arr.length; i++) {
        if (invoice_total_record >= 1) {
          invoice_total_record += 1;
          invoice_total_amount += rent_amount;
          invoice_date_list.push(invoice_arr[i]);
          invoice_amount_list.push(parseFloat(rent_amount));
          tableHtml +=
            "<tr><td><input type='text' invoice_length_index='" +
            invoice_total_record +
            "'  class='form-control flatpickr-human-friendly record" +
            i +
            "' value='" +
            invoice_arr[i] +
            "' name='invoice_due_date' disabled/></td><td><input type='text' id='" +
            invoice_total_record +
            "' class='form-control record" +
            i +
            "' value='" +
            rent_amount +
            "' name='invoice_amount' disabled/></td>";
          tableHtml +=
            "<td id='record" +
            i +
            "'><a href='javascript:void(0);' title='Edit' input_class='record" +
            i +
            "' class='btn btn-success btn-sm rounded-0 edit_schedule'><i class='fa fa-edit' style='font-size:10px;'></i></a><a href='javascript:void(0);' title='Delete' class='btn btn-danger btn-sm rounded-0 edit_schedule' input_class='record" +
            i +
            "'><i class='fa fa-trash' style='font-size:13px;'></i></a></td></tr>";
        }

        if (invoice_arr[i] == due_date) {
          invoice_total_record += 1;
          invoice_total_amount += rent_amount;
          invoice_date_list.push(invoice_arr[i]);
          invoice_amount_list.push(parseFloat(rent_amount));
          tableHtml +=
            "<tr><td><input type='text' invoice_length_index='" +
            invoice_total_record +
            "'  class='form-control flatpickr-human-friendly record" +
            i +
            "' value='" +
            invoice_arr[i] +
            "' name='invoice_due_date' disabled/></td><td><input type='text' id='" +
            invoice_total_record +
            "' class='form-control record" +
            i +
            "' value='" +
            rent_amount +
            "' name='invoice_amount' disabled/></td>";
          tableHtml +=
            "<td id='record" +
            i +
            "'><a href='javascript:void(0);' title='Edit' input_class='record" +
            i +
            "' class='btn btn-success btn-sm rounded-0 edit_schedule'><i class='fa fa-edit' style='font-size:10px;'></i></a><a href='javascript:void(0);' title='Delete' class='btn btn-danger btn-sm rounded-0 edit_schedule' input_class='record" +
            i +
            "'><i class='fa fa-trash' style='font-size:13px;'></i></a></td></tr>";
        }
      }
    } else {
      var every_month_value = parseInt($(".change_every_month_date").val());
      var actualDate = new Date(due_date);
      var nextMonth = new Date(
        actualDate.getFullYear(),
        actualDate.getMonth() + 1,
        every_month_value
      );
      invoice_total_record += 1;
      invoice_total_amount += rent_amount;
      invoice_date_list.push(due_date);
      invoice_amount_list.push(parseFloat(rent_amount));

      tableHtml +=
        "<tr><td><input type='text' invoice_length_index='" +
        invoice_total_record +
        "'  class='form-control flatpickr-human-friendly record0' value='" +
        due_date +
        "' name='invoice_due_date' disabled/></td><td><input type='text' id='" +
        invoice_total_record +
        "' class='form-control record0' value='" +
        rent_amount +
        "' name='invoice_amount' disabled/></td>";
      tableHtml +=
        "<td id='record0'><a href='javascript:void(0);' title='Edit' input_class='record0' class='btn btn-success btn-sm rounded-0 edit_schedule'><i class='fa fa-edit' style='font-size:10px;'></i></a><a href='javascript:void(0);' title='Delete' class='btn btn-danger btn-sm rounded-0 edit_schedule' input_class='record0'><i class='fa fa-trash' style='font-size:13px;'></i></a></td></tr>";

      for (var i = 1; i < 12; i++) {
        var actualDate = make_date_str(nextMonth);
        invoice_total_record += 1;
        invoice_total_amount += rent_amount;
        invoice_date_list.push(actualDate);
        invoice_amount_list.push(parseFloat(rent_amount));
        tableHtml +=
          "<tr><td><input type='text' invoice_length_index='" +
          invoice_total_record +
          "'  class='form-control flatpickr-human-friendly record" +
          i +
          "' value='" +
          actualDate +
          "' name='invoice_due_date' disabled/></td><td><input type='text' id='" +
          invoice_total_record +
          "' class='form-control record" +
          i +
          "' value='" +
          rent_amount +
          "' name='invoice_amount' disabled/></td>";
        tableHtml +=
          "<td id='record" +
          i +
          "'><a href='javascript:void(0);' title='Edit' input_class='record" +
          i +
          "' class='btn btn-success btn-sm rounded-0 edit_schedule'><i class='fa fa-edit' style='font-size:10px;'></i></a><a href='javascript:void(0);' title='Delete' class='btn btn-danger btn-sm rounded-0 edit_schedule' input_class='record" +
          i +
          "'><i class='fa fa-trash' style='font-size:13px;'></i></a></td></tr>";
        var actualDate = new Date(actualDate);
        var nextMonth = new Date(
          actualDate.getFullYear(),
          actualDate.getMonth() + 1,
          every_month_value
        );
      }
    }
    currency_symbol = $("#currency_name").val();
    $(".total_invoices_no").text(invoice_total_record);
    $(".total_rental_amount").text(currency_symbol + invoice_total_amount);
    $("#invoice_body_div").append(tableHtml);
    $(".invoice_div").show();
    $("#edit_invoice_div").show();
    $("#invoice_date_list").val(JSON.stringify(invoice_date_list));
    $("#invoice_amount_list").val(JSON.stringify(invoice_amount_list));

    humanFriendlyPickr = $(".flatpickr-human-friendly");
    if (humanFriendlyPickr.length) {
      humanFriendlyPickr.flatpickr({
        altInput: true,
        altFormat: "F j, Y",
        dateFormat: "F j, Y",
      });
    }
  });

  // Enable and disabled
  $("body").delegate(".edit_schedule", "click", function (event) {
    class_attr = $(this).attr("input_class");
    input_class = "." + class_attr;
    input_id = "#" + class_attr;
    title_name = $(this).attr("title");
    $(input_id).empty();

    if (title_name == "Edit") {
      $(input_class).removeAttr("disabled");
      saveHtml =
        "<a href='javascript:void(0);' title='Save' input_class='record" +
        input_class[7] +
        "' class='btn btn-success btn-sm rounded-0 edit_schedule'><i class='fa fa-file' style='font-size:10px;'></i></a>";
    }
    if (
      title_name == "Save" ||
      title_name == "Delete" ||
      title_name == "Undo"
    ) {
      var amount_id = $(input_class).attr("invoice_length_index");
      list_index = parseInt(amount_id) - 1;
      var invoice_date_list = JSON.parse($("#invoice_date_list").val());
      var invoice_amount_list = JSON.parse($("#invoice_amount_list").val());
      var input_list = $(input_class);

      new_date_value = input_list[0].getAttribute("value");
      new_amount_value = parseFloat($("#" + amount_id).val());
      old_date_value = invoice_date_list[list_index];
      old_amount_value = parseFloat(invoice_amount_list[list_index]);
      var total_rental_amount_str = $(".total_rental_amount")[0].getInnerHTML();
      total_rental_amount = total_rental_amount_str.replace(
        total_rental_amount_str[0],
        ""
      );

      $(input_class).attr("disabled", "disabled");
      if (title_name == "Save") {
        total_rental_amount =
          parseFloat(total_rental_amount) - old_amount_value + new_amount_value;
        invoice_date_list.splice(list_index, 1);
        invoice_date_list.splice(list_index, 0, new_date_value);
        invoice_amount_list.splice(list_index, 1);
        invoice_amount_list.splice(list_index, 0, new_amount_value);
        saveHtml =
          "<a href='javascript:void(0);' title='Edit' input_class='record" +
          input_class[7] +
          "' class='btn btn-success btn-sm rounded-0 edit_schedule'><i class='fa fa-edit' style='font-size:10px;'></i></a><a href='javascript:void(0);' title='Delete' class='btn btn-danger btn-sm rounded-0 edit_schedule' input_class='record" +
          input_class[7] +
          "'><i class='fa fa-trash' style='font-size:13px;'></i></a>";
      }

      if (title_name == "Delete") {
        total_rental_amount =
          parseFloat(total_rental_amount) - new_amount_value;
        invoice_date_list.splice(list_index, 1);
        invoice_date_list.splice(list_index, 0, "None");
        invoice_amount_list.splice(list_index, 1);
        invoice_amount_list.splice(list_index, 0, "None");

        $(input_class).addClass("is-invalid");
        saveHtml =
          "<a href='javascript:void(0);' title='Undo' input_class='record" +
          input_class[7] +
          "' class='btn btn-success btn-sm rounded-0 edit_schedule'><i class='fa fa-undo' style='font-size:10px;'></i></a>";
      }

      if (title_name == "Undo") {
        total_rental_amount =
          parseFloat(total_rental_amount) + new_amount_value;
        invoice_date_list.splice(list_index, 1);
        invoice_date_list.splice(list_index, 0, new_date_value);
        invoice_amount_list.splice(list_index, 1);
        invoice_amount_list.splice(list_index, 0, new_amount_value);
        $(input_class).removeClass("is-invalid");
        saveHtml =
          "<a href='javascript:void(0);' title='Edit' input_class='record" +
          input_class[7] +
          "' class='btn btn-success btn-sm rounded-0 edit_schedule'><i class='fa fa-edit' style='font-size:10px;'></i></a><a href='javascript:void(0);' title='Delete' class='btn btn-danger btn-sm rounded-0 edit_schedule' input_class='record" +
          input_class[7] +
          "'><i class='fa fa-trash' style='font-size:13px;'></i></a>";
      }

      $(".total_rental_amount").text(
        total_rental_amount_str[0] + total_rental_amount
      );
      $("#invoice_date_list").val(JSON.stringify(invoice_date_list));
      $("#invoice_amount_list").val(JSON.stringify(invoice_amount_list));
    }
    $(input_id).append(saveHtml);
  });

  // Show Invoices Div Data
  $("body").delegate(".view_invoices_div", "click", function (event) {
    $(".rental_edit_invoice_div").toggle();
    $(".rental_summary_div").toggle();
  });

  // Propert Details Page Click Functionality
  $("body").delegate(".property_tr", "click", function (event) {
    var prop_url = $(this).attr("property_detail_url");
    location.assign(prop_url);
  });

  // Property Select Info

  $(".select_property").on("change", function (e) {
    $("#unit_options").empty();
    $("#tenant_n").val("");
    property_name = $(this).val();
    var csrftoken = getCookie("csrftoken");
    $.ajax({
      type: "POST",
      url: "/en/property/property_info/",
      data: {
        property_name: property_name,
        csrfmiddlewaretoken: csrftoken,
      },
      dataType: "json",
      success: function (data) {
        var unit_list = data.unit_list;
        var tenant_dict = data.tenant_dict;
        var optionHtml = "";
        for (let i = 0; i < unit_list.length; i++) {
          if (i == 0) {
            $("#tenant_n").val(tenant_dict[unit_list[i]["name"]]);
            $("#tenant_n").attr("tenant_dict", JSON.stringify(tenant_dict));
          }
          optionHtml += "<option>" + unit_list[i]["name"] + "</option>";
        }
        console.log();
        $("#unit_options").append(optionHtml);
        $(".property_relate").show();
        $(".currency_symbol").text(data.currency_symbol);
      },
    });
  });

  $("body").delegate(".select_currency_symbol", "change", function (event) {
    currency_value = $(this).val();
    $(".currency_code_class").text(currency_value);
  });

  $("#unit_options").on("change", function (e) {
    unit_value = $(this).val();
    tenant_dict = JSON.parse($("#tenant_n").attr("tenant_dict"));
    $.each(tenant_dict, function (key, value) {
      if (key == unit_value) {
        $("#tenant_n").val(value);
      }
    });
  });

  // EDIT INVOICE DETAILS

  $("body").delegate(".edit_invoice_button", "click", function (event) {
    $("#edit_div").hide();
    $("#save_div").show();
    $("#edit_tr").show();
    $(".remove_td").show();
    $("#default_tr").hide();
  });

  $("body").delegate(".save_invoice_button", "click", function (event) {
    method_type = $(this).attr("method_type");
    if (method_type == "save") {
      $("#invoice_edit_form").submit();
    } else {
      $("#edit_div").show();
      $("#save_div").hide();
      $("#edit_tr").hide();
      $(".remove_td").hide();
      $("#default_tr").show();
    }
  });

  $("body").delegate(".total_amount_event", "change", function (event) {
    item_amount = $("#item_amount").val();
    quantity = $("#quantity").val();
    paid_amount = parseFloat($(".invoices-paid-amount").text());
    console.log(paid_amount);
    if (isNaN(paid_amount)) {
      paid_amount = parseFloat($(".invoices-paid-amount").val());
    }
    total_amount = parseFloat(item_amount) * parseFloat(quantity);
    remaining_amount = total_amount - paid_amount;
    $(".invoices-total-amount").text(total_amount);
    $(".invoices-remaining-amount").text(remaining_amount);
  });

  $("body").delegate(".paid_amount_check", "change", function (event) {
    item_amount = parseFloat($(this).val());
    check_amount = parseFloat($(".invoices-remaining-amount").text());
    if (item_amount > check_amount) {
      $(this).val("");
      $(".paid_amount_error").text(
        "You entered an amount greater than the balance due."
      );
    }
    if (item_amount <= 0) {
      $(this).val("");
      $(".paid_amount_error").text("You entered an wrong amount.");
    }
  });
  $("body").delegate(".delete_payment", "click", function (event) {
    var currentRow = $(this).closest("tr");
    var payment_index = currentRow.find("td:eq(0)").text();
    var paid_amount = currentRow.find("td:eq(4)").text();
    var invoice_id = $("#invoice_id").val();
    location_url =
      "/en/property/invoice/payment_delete/" +
      invoice_id +
      "/" +
      payment_index +
      "/" +
      paid_amount;
    location.assign(location_url);
  });

  // get Transactions
  $("body").delegate(".get_transaction_btn", "click", function (event) {
    start_date = $("#start_date").val();
    end_date = $("#end_date").val();
    if (start_date && end_date) {
      $("#import-transaction-form").submit();
    } else {
      Swal.fire({
        title: "Please Choose Date Range",
        icon: "error",
        customClass: {
          confirmButton: "btn btn-primary",
        },
        buttonsStyling: false,
      });
      return false;
    }
  });

  //  HIDE AND SHOW MORE APP DETAILS

  $(".more_button").on("click", function (event) {
    if ($(this).html() == "More...") {
      $(this).html("Hide");
      $(".see_more_summary").show();
    } else {
      $(this).html("More...");
      $(".see_more_summary").hide();
    }
  });

  //  Percentage Increase / Decrease
  $("body").delegate(".price_percentage", "change", function (event) {
    price_p_val = parseFloat($(this).val());
    likely_case_price = parseFloat($("#likely_case").val());
    method_name = $(this).attr("method_name");
    percentage_val = (likely_case_price * price_p_val) / 100;

    if (method_name == "best_case") {
      $("#best_case").val(likely_case_price - percentage_val);
    }
    if (method_name == "worst_case") {
      $("#worst_case").val(likely_case_price + percentage_val);
    }
    if (method_name == "likely_case") {
      best_price_p_val = $("#best_p_val").val();
      worst_p_val = $("#worst_p_val").val();
      best_case_p = (likely_case_price * best_price_p_val) / 100;
      worst_case_p = (likely_case_price * worst_p_val) / 100;
      $("#best_case").val(likely_case_price - best_case_p);
      $("#worst_case").val(likely_case_price + worst_case_p);
    }
  });

  //  Get Mortgage Year
  $("body").delegate("#mortgage_year", "change", function (event) {
    year = $(this).val();
    if (year != 30 && year != 25) {
      $(".get_mortgage_year").removeClass("badge-success");
      $(".get_mortgage_year").removeClass("badge-primary");
      $(".get_mortgage_year").addClass("badge-primary");
    } else {
      if (year == 25) {
        $("#min_year").removeClass("badge-primary");
        $("#min_year").addClass("badge-success");
        if ($("#max_year").hasClass("badge-success")) {
          $("#max_year").removeClass("badge-success");
          $("#max_year").addClass("badge-primary");
        }
      } else {
        $("#max_year").removeClass("badge-primary");
        $("#max_year").addClass("badge-success");
        if ($("#min_year").hasClass("badge-success")) {
          $("#min_year").removeClass("badge-success");
          $("#min_year").addClass("badge-primary");
        }
      }
    }
  });

  //  Get Mortgage Year
  $("body").delegate(".get_mortgage_year", "click", function (event) {
    year = $(this).text().trim();
    year_id = $(this).attr("id");
    if (year_id == "min_year") {
      if ($("#max_year").hasClass("badge-success")) {
        $("#max_year").removeClass("badge-success");
        $("#max_year").addClass("badge-primary");
      }
    } else {
      if ($("#min_year").hasClass("badge-success")) {
        $("#min_year").removeClass("badge-success");
        $("#min_year").addClass("badge-primary");
      }
    }
    $(this).removeClass("badge-primary");
    $(this).addClass("badge-success");
    $("#mortgage_year").val(year);
  });

  //  Show Interest Rate
  $("body").delegate(".show_interest_rate", "click", function (event) {
    $(".interest_rate_info").toggle();
  });

  //  Show and hide subcategory
  $("body").delegate(".category", "click", function (event) {
    class_name = $(this).attr("class_name");
    $("." + class_name).toggle();
    $("." + class_name + "_dropdown").toggle();
  });

  $("body").on("click", ".compare-category", function (event) {
    var class_name = $(this).data("class-name");
    var arrow = $("#arrow-" + class_name);

    // Toggle the collapse of the rows
    $("." + class_name).collapse("toggle");

    // Immediately toggle the arrow direction
    if (arrow.hasClass("fa-chevron-right")) {
      arrow.removeClass("fa-chevron-right").addClass("fa-chevron-down");
    } else {
      arrow.removeClass("fa-chevron-down").addClass("fa-chevron-right");
    }
  });

  //  Show and hide subcategory
  $("body").delegate(".pick_category", "change", function (event) {
    $(".transaction_due_bill_list").hide();
    $(".transaction_income_list").hide();
    $("#id_amount").val("");
    $("#id_amount").attr("disabled", false);
    $("#customRadio1").prop("checked", true);
    category_group = $(this).val();
    method_name = $(this).attr("method_name");
    category_group_name = $(this).find("option:selected").text().trim();
    if (method_name == "add_budget") {
      if (category_group_name.includes("Bills")) {
        location.assign("/bill_add/");
      }
    }
    $("#category_group").val(category_group);
    var csrftoken = getCookie("csrftoken");
    $.ajax({
      type: "POST",
      url: "/en/subcategory_list",
      data: {
        category_group: category_group,
        csrfmiddlewaretoken: csrftoken,
      },
      success: function (response) {
        var cat_list = response.subcategories;
        var optionHtml =
          "<select class='form-control show_due_bills check_budget_category' id='subcategory' name='subcategory'><option value='' selected=''>Select Category</option>";
        $("#trans_sub_cat").empty();
        for (let i = 0; i < cat_list.length; i++) {
          optionHtml += "<option>" + cat_list[i] + "</option>";
        }
        optionHtml += "</select>";
        $("#trans_sub_cat").append(optionHtml);
        $(".transaction_cat_list").show();
      },
      error: function (xhr, status, error) {
        console.error("Error occurred during AJAX request:", status, error);
      },
    });
  });

  //  Show and hide due bills
  $("body").delegate(".show_due_bills", "change", function (event) {
    category_id = $(" #id_category").val();
    var category_name = $("#id_category option:selected").text();
    sub_category = $(this).val();
    var csrftoken = getCookie("csrftoken");
    //    if (category_name == "Income")
    //    {
    //
    //        $.ajax({
    //            type: 'POST',
    //            url: "/en/income/uncredited_list',
    //            data: {
    //            'sub_category': sub_category,
    //            'category_id': category_id,
    //            'csrfmiddlewaretoken': csrftoken
    //            },
    //            success: function(response)
    //            {
    //                if(response.status == 'error')
    //                {
    //                    $(".transaction_income_list").hide();
    //                    $("#trans_income").empty();
    //                }
    //                else
    //                {
    //                    var income_dict = response.income_dict
    //                    var optionHtml = "<select class='form-control' amount_dict='" + response.amount_dict + "' id='due_income' name='due_income' required><option value='' selected=''>Select uncredited income</option>"
    //                    $("#trans_income").empty();
    //                    $.each(income_dict, function(key, value) {
    //                        optionHtml += "<option value='" + key + "'>" + value + "</option>"
    //                    });
    //                    optionHtml += "</select>"
    //                    $("#trans_income").append(optionHtml);
    //                    $(".transaction_income_list").show();
    //                }
    //            }
    //        });
    //    }
    if (category_name == "Bills & Subscriptions" || category_name == "Bills") {
      $.ajax({
        type: "POST",
        url: "/en/bill/due_list",
        data: {
          sub_category: sub_category,
          category_id: category_id,
          csrfmiddlewaretoken: csrftoken,
        },
        success: function (response) {
          if (response.status === "error") {
            $(".transaction_due_bill_list").hide();
            $("#trans_bills").empty();
          } else {
            let unpaid_bill_dict = response.unpaid_bill_dict;
            let optionHtml =
              "<select class='form-control' amount_dict='" +
              JSON.stringify(response.amount_dict) +
              "' id='due_bill' name='due_bill' required><option value='' selected=''>Select due bills</option>";
            $("#trans_bills").empty();
            $.each(unpaid_bill_dict, function (key, value) {
              optionHtml +=
                "<option value='" + key + "'>" + value + "</option>";
            });
            optionHtml += "</select>";
            $("#trans_bills").append(optionHtml);
            $(".transaction_due_bill_list").show();
          }
        },
        error: function (xhr, status, error) {
          console.error("Error occurred during AJAX request:", status, error);
          $(".transaction_due_bill_list").hide();
          $("#trans_bills").empty();
        },
      });
    }
  });

  $("body").delegate("#due_bill", "change", function (event) {
    let amount_dict = JSON.parse($(this).attr("amount_dict"));
    let bill_id = $(this).val();
    if (amount_dict[bill_id]) {
      $("#id_amount").val(amount_dict[bill_id]);
      $("#id_amount").attr("max_amount", amount_dict[bill_id]);
    } else {
      $("#id_amount").val("");
      $("#id_amount").removeAttr("max_amount");
    }
  });

  // add uncredited amount when select uncredited income
  $("body").delegate("#due_income", "change", function (event) {
    amount_dict = JSON.parse($(this).attr("amount_dict"));
    income_id = $(this).val();
    var income_date = $("#due_income option:selected").text();
    $("#id_transaction_date").val(income_date);
    $("#id_amount").val(amount_dict[income_id]);
    $("#customRadio2").prop("checked", true);
    //    $("#id_amount").attr('disabled', 'disabled')
  });

  // don't enter grater amount than due bill amount
  $("body").delegate("#id_amount", "change paste keypress", function (event) {
    $("#amount_error").hide();
    max_amount = parseFloat($(this).attr("max_amount"));
    enter_amount = $(this).val();
    if (enter_amount > max_amount) {
      $(this).val(max_amount);
      $("#amount_error").text(
        "Amount should not be greater than due bill amount"
      );
      $("#amount_error").show();
    }
  });

  //  check Budget Category
  $("body").delegate(".check_budget_category", "change", function (event) {
    category_name = $("#id_categories, #id_category").val();
    cat_name = $("#id_categories option:selected").text();

    var user_budget_id = $('[name="user_budget"] option:selected').val();
    if (cat_name == "Income") {
      $("#customRadio2").prop("checked", true);
    } else {
      $("#customRadio1").prop("checked", true);
    }
    sub_category_name = $("#subcategory").val();
    var csrftoken = getCookie("csrftoken");
    $.ajax({
      type: "POST",
      url: "/en/subcategory_budget",
      data: {
        category: category_name,
        name: sub_category_name,
        user_budget_id: user_budget_id,
        csrfmiddlewaretoken: csrftoken,
      },
      success: function (response) {
        if (response.budget_name) {
          $("#budget_name").val(response.budget_name);
          $(".budget_div").show();
        } else {
          $("#budget_name").val("");
          $(".budget_div").hide();
        }
      },
    });
  });

  // check auto bill & budget
  $("body").delegate(".check_auto_bill", "change", function (event) {
    var check = $(this).prop("checked");
    if (check) {
      $(".show_bill_budget_periods").show();
    } else {
      $(".show_bill_budget_periods").hide();
    }
  });

  // show portfolio holdings
  $("body").delegate(".portfolio_show_form", "click", function (event) {
    form_id = $(this).attr("form_id");
    $("#" + form_id).submit();
  });

  // add_portfolio_to_networth
  $("body").delegate(".add_portfolio_to_networth", "click", function (event) {
    method_name = $(this).attr("method_name");
    portfolio_value = $(this).attr("portfolio_value");
    portfolio_name = $(this).attr("portfolio_name");
    portfolio_id = $(this).attr("portfolio_id");
    portfolio_currency = $(this).attr("portfolio_currency");
    var url = "/en/add_port_in_networth";
    var csrfmiddlewaretoken = getCookie("csrftoken");
    $.ajax({
      type: "POST",
      url: url,
      data: {
        portfolio_name: portfolio_name,
        portfolio_id: portfolio_id,
        portfolio_value: portfolio_value,
        portfolio_currency: portfolio_currency,
        method_name: method_name,
        csrfmiddlewaretoken: csrfmiddlewaretoken,
      },
      success: function (response) {
        if (response.status == "true") {
          Swal.fire({
            title: "Added Successfully in your networth",
            icon: "success",
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          });
        } else {
          if (response.status == "delete") {
            Swal.fire({
              title: "Deleted Successfully from your networth",
              icon: "success",
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            });
          } else {
            Swal.fire({
              title: "Failed to add in networth",
              icon: "error",
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            });
          }
        }
      },
    });
    if (method_name == "add_port") {
      $(this).hide();
      $(".already_holds").show();
    } else {
      $(".add_portfolio_to_networth").show();
      $(".already_holds").hide();
    }
    return false;
  });

  // show daily budgets
  // check auto bill & budget
  $("body").delegate(".show_daily_budget", "click", function (event) {
    id_name = $(this).attr("id_name");
    class_name = ".show_daily_rows" + id_name;
    $(class_name).toggle();
    $("." + "dropdown_" + id_name).toggle();
  });

  // change mortgage down payment amount according to mortgage amount
  $("body").delegate("#add_category_group", "change", function (event) {
    category_name = $(this).val();
    var csrfmiddlewaretoken = getCookie("csrftoken");
    $.ajax({
      type: "POST",
      url: "/en/category_group_add/",
      data: {
        category_name: category_name,
        csrfmiddlewaretoken: csrfmiddlewaretoken,
      },
      success: function (response) {
        if (response.status == "success") {
          Swal.fire({
            title: "Category Created Successfully",
            icon: "success",
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          });
          location.reload();
        } else {
          Swal.fire({
            title: "Category already exists!",
            icon: "error",
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          });
        }
      },
    });
  });

  // change mortgage down payment amount according to mortgage amount
  $("body").delegate("#mortgage_amount", "change", function (event) {
    amount = $(this).val();
    percentage = parseFloat($("#down_pay_per").val());
    down_payment = (amount * percentage) / 100;
    $("#down_pay_amount").val(down_payment);
  });

  // change mortgage down payment percentage
  $("body").delegate("#down_pay_amount", "change", function (event) {
    down_payment = $(this).val();
    amount = $("#mortgage_amount").val();
    if (amount) {
      percentage = (down_payment / amount) * 100;
    } else {
      percentage = 0;
    }
    percentage = $("#down_pay_per").val(percentage);
  });

  // change mortgage percentage
  $("body").delegate("#down_pay_per", "change", function (event) {
    percentage = parseFloat($(this).val());
    console.log(percentage);
    amount = $("#mortgage_amount").val();
    if (amount) {
      down_payment = (amount * percentage) / 100;
    } else {
      down_payment = 0;
    }
    $("#down_pay_amount").val(down_payment);
    $("#down_pay_per").val(percentage);
  });

  // Pay bill amount

  // Pay bill

  $(".pay_bill_amount").on("click", function (e) {
    var pay_id = $(this).attr("pay_id");
    var url = "/en/bill_pay/" + pay_id;
    var csrfmiddlewaretoken = getCookie("csrftoken");
    $.ajax({
      type: "POST",
      url: url,
      data: {
        csrfmiddlewaretoken: csrfmiddlewaretoken,
      },
      success: function (response) {
        if (response.status == "true") {
          Swal.fire({
            title: "Paid Successfully",
            icon: "success",
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          });
          location.reload();
        } else {
          Swal.fire({
            title: "Account Balance is low you can not pay bill",
            icon: "error",
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          });
        }
      },
    });
  });

  // Add Income Budget Walkthrough
  $("body").delegate(".update_income_bgt_walkthrough", "click", function (e) {
    e.preventDefault();
    income_index = $(this).attr("income_index");
    income_account_id = $("#income_account_id").val();
    user_budget_name = $("#user_budget_name").val();
    user_budget_id = $(this).attr("user_budget");
    id = $(this).attr("income_id");
    name = $("#income_sources" + income_index).val();
    exp_amount = $("#income_expected_amount" + income_index).val();
    actual_amount = $("#income_actual_amount" + income_index).val();
    if (name && exp_amount && actual_amount) {
      console.log($(".total_income_exp").val());
      total_exp_amount = 0;
      total_act_amount = 0;

      $(".total_income_exp").map(function () {
        total_exp_amount = total_exp_amount + parseFloat($(this).val());
      });

      $(".total_income_act").map(function () {
        total_act_amount = total_act_amount + parseFloat($(this).val());
      });

      $("#total_inc_exp").text(total_exp_amount);
      $("#total_inc_act").text(total_act_amount);

      var csrfmiddlewaretoken = getCookie("csrftoken");
      $.ajax({
        type: "POST",
        url: "/en/budgets/income/walk_through",
        data: {
          id: id,
          name: name,
          exp_amount: exp_amount,
          actual_amount: actual_amount,
          income_account_id: income_account_id,
          user_budget_id: user_budget_id,
          csrfmiddlewaretoken: csrfmiddlewaretoken,
        },
        success: function (response) {
          if (response.status == "true") {
            Swal.fire({
              title: "Saved Successfully",
              icon: "success",
              text: response.message,
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            }).then(function () {
              // Reload the page & takes to income section
              location.href =
                "/en/budgets/walk_through/" +
                user_budget_id +
                "#income-section";
              location.reload();
            });
          } else {
            Swal.fire({
              title: "Saving Failed!",
              icon: "error",
              text: response.message,
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            }).then(function () {
              // Reload the page
              location.href =
                "/en/budgets/walk_through/" +
                user_budget_id +
                "#income-section";
              location.reload();
            });
          }
        },
      });
    } else {
      Swal.fire({
        title: "All fields are required",
        icon: "error",
        customClass: {
          confirmButton: "btn btn-primary",
        },
        buttonsStyling: false,
      });
    }
  });

  // Add Income Budget Walkthrough
  $("body").delegate(".add_other_income", "click", function (e) {
    last_index = parseInt($(this).attr("last_index")) + 1;
    var user_budget = $(this).attr("user_budget");
    trHTML =
      "<tr>" +
      "<td><input type='text' value='Other Income' id='income_sources" +
      last_index +
      "' name='income_sources' class='form-control income_sources' required/></td>" +
      "<td><input type='number' value='0.0' id='income_expected_amount" +
      last_index +
      "' name='income_expected_amount' class='form-control total_income_exp' required/>" +
      "<input type='number' value='0.0' id='income_actual_amount" +
      last_index +
      "' name='income_actual_amount' class='form-control total_income_act' required hidden/></td>" +
      "<td><button class='btn btn-outline-secondary update_income_bgt_walkthrough' income_index='" +
      last_index +
      "' income_id='false' user_budget='" +
      user_budget +
      "'>Update</button></td></tr>";
    $(".total_income_row").before(trHTML);
    return false;
  });

  // Add Bill Budget Walkthrough
  $("body").delegate(".update_bill_bgt_walkthrough", "click", function (e) {
    e.preventDefault();
    bill_index = $(this).attr("bill_index");
    bill_account_id = $("#bill_account_id").val();
    user_budget_name = $("#user_budget_name").val();
    user_budget_id = $(this).attr("user_budget");
    id = $(this).attr("bill_id");
    name = $("#bill_sources" + bill_index).val();
    exp_amount = $("#bill_expected_amount" + bill_index).val();
    actual_amount = $("#bill_actual_amount" + bill_index).val();
    budget_period = $("#bill_budget_period" + bill_index).val();
    budget_date = $("#bill_add_budget_date" + bill_index).val();
    console.log("budget period====>", budget_period);
    console.log("budget date======>", budget_date);
    if (name && exp_amount && actual_amount) {
      total_exp_amount = 0;
      total_act_amount = 0;

      $(".total_bill_exp").map(function () {
        total_exp_amount = total_exp_amount + parseFloat($(this).val());
      });

      $(".total_bill_act").map(function () {
        total_act_amount = total_act_amount + parseFloat($(this).val());
      });

      $("#total_bill_exp").text(total_exp_amount);
      $("#total_bill_act").text(total_act_amount);
      var csrfmiddlewaretoken = getCookie("csrftoken");
      $.ajax({
        type: "POST",
        url: "/en/bill_walk_through/",
        data: {
          id: id,
          name: name,
          exp_amount: exp_amount,
          actual_amount: actual_amount,
          bill_account_id: bill_account_id,
          budget_period: budget_period,
          budget_date: budget_date,
          user_budget_id: user_budget_id,
          csrfmiddlewaretoken: csrfmiddlewaretoken,
        },
        success: function (response) {
          if (response.status == "true") {
            Swal.fire({
              title: "Saved Successfully",
              icon: "success",
              text: response.message,
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            }).then(function () {
              // Reload the page & takes to bills section
              location.href =
                "/en/budgets/walk_through/" + user_budget_id + "#bill-section";
              location.reload();
            });
          } else {
            Swal.fire({
              title: "Saving Failed!",
              icon: "error",
              text: response.message,
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            }).then(function () {
              location.href =
                "/en/budgets/walk_through/" + user_budget_id + "#bill-section";
              location.reload();
            });
          }
        },
      });
    } else {
      Swal.fire({
        title: "All fields are required",
        icon: "error",
        customClass: {
          confirmButton: "btn btn-primary",
        },
        buttonsStyling: false,
      });
    }
  });

  // Add New Bills
  $("body").delegate(".add_other_bill", "click", function (e) {
    var last_index = parseInt($(this).attr("last_index")) + 1;
    var user_budget = $(this).attr("user_budget");

    trHTML =
      "<tr>" +
      "<td><input type='text' value='Other Bill' id='bill_sources" +
      last_index +
      "' name='bill_sources' class='form-control bill_sources' required/></td>" +
      "<td><input type='number' value='0.0' id='bill_expected_amount" +
      last_index +
      "' name='bill_expected_amount' class='form-control total_bill_exp' required/>" +
      "<input type='number' value='0.0' id='bill_actual_amount" +
      last_index +
      "' name='income_bill_amount' class='form-control total_bill_act' required hidden/></td>" +
      "<td>" +
      "<select id='bill_budget_period" +
      last_index +
      "' name='bill_budget_period' class='form-control' required>" +
      "<option value='Monthly'>Monthly</option>" +
      "<option value='Yearly'>Yearly</option>" +
      "</select>" +
      "</td>" +
      "<td>" +
      "<i class='fa fa-calendar fa-1 bill_calender_icon' index='" +
      last_index +
      "' id='bill_calender_icon" +
      last_index +
      "'></i>" +
      "<input type='text' id='bill_add_budget_date" +
      last_index +
      "' name='bill_add_budget_date' class='form-control flatpickr-basic' hidden required>" +
      "</td>" +
      "<td><button class='btn btn-outline-secondary update_bill_bgt_walkthrough' bill_index='" +
      last_index +
      "' user_budget='" +
      user_budget +
      "' bill_id='false'>Update</button></td></tr>";
    $(".total_bill_row").before(trHTML);
    return false;
  });

  // Date picker for Bill budget
  $("body").delegate(".bill_calender_icon", "click", function (e) {
    var last_index = parseInt($(this).attr("index"));
    var budgetDateId = "#bill_add_budget_date" + last_index;

    // Show the budget_date input field
    $(budgetDateId).removeAttr("hidden");

    // Get Flatpickr instance of the budget_date input
    var flatpickrInstance = $(budgetDateId).flatpickr();

    // Open the Flatpickr calendar
    if (flatpickrInstance) {
      flatpickrInstance.open();
    }
    setTimeout(function () {
      // Add the 'hidden' attribute back to the #budget_date input (optional)
      $(budgetDateId).attr("hidden", true);
    }, 100);
  });

  // Add Expense Budget Walkthrough
  $("body").delegate(".update_expenses_bgt_walkthrough", "click", function (e) {
    e.preventDefault();
    expenses_index = $(this).attr("expenses_index");
    expenses_account_id = $("#expenses_account_id").val();
    id = $(this).attr("expenses_id");
    name = $("#expenses_sources" + expenses_index).val();
    user_budget_id = $(this).attr("user_budget");
    exp_amount = $("#expenses_expected_amount" + expenses_index).val();
    actual_amount = $("#expenses_actual_amount" + expenses_index).val();
    budget_period = $("#expenses_budget_period" + expenses_index).val();
    budget_date = $("#expenses_add_budget_date" + expenses_index).val();
    cat_name = $(this).attr("category_name");
    if (name && cat_name && exp_amount && actual_amount) {
      console.log($(".total_expenses_exp").val());
      total_exp_amount = 0;
      total_act_amount = 0;

      $(".total_expenses_exp").map(function () {
        total_exp_amount = total_exp_amount + parseFloat($(this).val());
      });

      $(".total_expenses_act").map(function () {
        total_act_amount = total_act_amount + parseFloat($(this).val());
      });

      $("#total_expenses_exp").text(total_exp_amount);
      $("#total_expenses_act").text(total_act_amount);

      var csrfmiddlewaretoken = getCookie("csrftoken");
      $.ajax({
        type: "POST",
        url: "/en/budgets/expenses/walk_through",
        data: {
          id: id,
          name: name,
          exp_amount: exp_amount,
          actual_amount: actual_amount,
          cat_name: cat_name,
          expenses_account_id: expenses_account_id,
          budget_period: budget_period,
          budget_date: budget_date,
          user_budget_id: user_budget_id,
          csrfmiddlewaretoken: csrfmiddlewaretoken,
        },
        success: function (response) {
          if (response.status == "true") {
            Swal.fire({
              title: "Saved Successfully",
              icon: "success",
              text: response.message,
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            }).then(function () {
              // Reload the page & takes to expenses section
              location.href =
                "/en/budgets/walk_through/" +
                user_budget_id +
                "#expense-section";
              location.reload();
            });
          } else {
            Swal.fire({
              title: "Saving Failed!",
              icon: "error",
              text: response.message,
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            }).then(function () {
              location.href =
                "/en/budgets/walk_through/" +
                user_budget_id +
                "#expense-section";
              location.reload();
            });
          }
        },
      });
    } else {
      Swal.fire({
        title: "All fields are required",
        icon: "error",
        customClass: {
          confirmButton: "btn btn-primary",
        },
        buttonsStyling: false,
      });
    }
  });

  // Add other expenses
  $("body").delegate(".add_other_expenses", "click", function (e) {
    last_index = parseInt($(this).attr("last_index")) + 1;
    var user_budget = $(this).attr("user_budget");
    trHTML =
      "<tr><th colspan='4'><input type=text class='form-control other_exp_name' btn_id='other_exp_btn" +
      last_index +
      "' placeholder='Enter Group Name'</th></tr>";
    trHTML +=
      "<tr>" +
      "<td><input type='text' placeholder='Enter Category name' id='expenses_sources" +
      last_index +
      "' name='expenses_sources' class='form-control expenses_sources' required/></td>" +
      "<td><input type='number' value='0.0' id='expenses_expected_amount" +
      last_index +
      "' name='expenses_expected_amount' class='form-control total_expenses_exp' required/>" +
      "<input type='number' value='0.0' id='expenses_actual_amount" +
      last_index +
      "' name='income_expenses_amount' class='form-control total_expenses_act' required hidden/></td>" +
      "<td>" +
      "<select id='expenses_budget_period" +
      last_index +
      "' name='expenses_budget_period' class='form-control' required>" +
      "<option value='Monthly'>Monthly</option>" +
      "<option value='Yearly'>Yearly</option>" +
      "</select>" +
      "</td>" +
      "<td>" +
      "<i class='fa fa-calendar fa-1 expenses_calender_icon' index='" +
      last_index +
      "' id='expenses_calender_icon" +
      last_index +
      "'></i>" +
      "<input type='text' id='expenses_add_budget_date" +
      last_index +
      "' name='expenses_add_budget_date' class='form-control flatpickr-basic' hidden required>" +
      "</td>" +
      "<td><button class='btn btn-outline-secondary update_expenses_bgt_walkthrough' id='other_exp_btn" +
      last_index +
      "' expenses_index='" +
      last_index +
      "' expenses_id='false' user_budget='" +
      user_budget +
      "'>Update</button></td></tr>";
    $(".total_expenses_row").before(trHTML);
    return false;
  });

  $("body").delegate(".other_exp_name", "change", function (e) {
    btn_id = $(this).attr("btn_id");
    cat_name = $(this).val();
    $("#" + btn_id).attr("category_name", cat_name);
  });

  // Date picker for Montlhy expenses
  $("body").delegate(".expenses_calender_icon", "click", function (e) {
    var last_index = parseInt($(this).attr("index"));
    var budgetDateId = "#expenses_add_budget_date" + last_index;

    // Show the budget_date input field
    $(budgetDateId).removeAttr("hidden");

    // Get Flatpickr instance of the budget_date input
    var flatpickrInstance = $(budgetDateId).flatpickr();

    // Open the Flatpickr calendar
    if (flatpickrInstance) {
      flatpickrInstance.open();
    }
    setTimeout(function () {
      // Add the 'hidden' attribute back to the #budget_date input (optional)
      $(budgetDateId).attr("hidden", true);
    }, 100);
  });

  // Add Non monthly Expense Budget Walkthrough
  $("body").delegate(
    ".update_non_monthly_expenses_bgt_walkthrough",
    "click",
    function (e) {
      e.preventDefault();
      non_monthly_expenses_index = $(this).attr("non_monthly_expenses_index");
      non_monthly_expenses_account_id = $(
        "#non_monthly_expenses_account_id"
      ).val();
      id = $(this).attr("non_monthly_expenses_id");
      budget_period = $(
        "#non_monthly_expenses_budget_period" + non_monthly_expenses_index
      ).val();
      budget_date = $(
        "#non_monthly_expenses_add_budget_date" + non_monthly_expenses_index
      ).val();
      user_budget_id = $(this).attr("user_budget");
      name = $(
        "#non_monthly_expenses_sources" + non_monthly_expenses_index
      ).val();
      exp_amount = $(
        "#non_monthly_expenses_expected_amount" + non_monthly_expenses_index
      ).val();
      actual_amount = $(
        "#non_monthly_expenses_actual_amount" + non_monthly_expenses_index
      ).val();
      // cat_name = $(this).attr('category_name')
      console.log("name===>", name);
      console.log("period======>", budget_period);
      console.log("expected amount======>", exp_amount);
      console.log("budget date======>", budget_date);
      if (name && exp_amount && actual_amount) {
        console.log($(".total_non_monthly_expenses_exp").val());
        total_exp_amount = 0;
        total_act_amount = 0;

        $(".total_non_monthly_expenses_exp").map(function () {
          total_exp_amount = total_exp_amount + parseFloat($(this).val());
        });

        $(".total_non_monthly_expenses_act").map(function () {
          total_act_amount = total_act_amount + parseFloat($(this).val());
        });

        $("#total_non_monthly_expenses_exp").text(total_exp_amount);
        $("#total_non_monthly_expenses_act").text(total_act_amount);

        var csrfmiddlewaretoken = getCookie("csrftoken");
        $.ajax({
          type: "POST",
          url: "/en/budgets/non_monthly_expenses/walk_through",
          data: {
            id: id,
            name: name,
            exp_amount: exp_amount,
            actual_amount: actual_amount,
            budget_period: budget_period,
            non_monthly_expenses_account_id: non_monthly_expenses_account_id,
            budget_date: budget_date,
            user_budget_id: user_budget_id,
            csrfmiddlewaretoken: csrfmiddlewaretoken,
          },
          success: function (response) {
            if (response.status == "true") {
              Swal.fire({
                title: "Saved Successfully",
                icon: "success",
                text: response.message,
                customClass: {
                  confirmButton: "btn btn-primary",
                },
                buttonsStyling: false,
              }).then(function () {
                // Reload the page & takes to non-monthly expenses section
                location.href =
                  "/en/budgets/walk_through/" +
                  user_budget_id +
                  "#non-monthly-expenses-section";
                location.reload();
              });
            } else {
              Swal.fire({
                title: "Saving Failed!",
                icon: "error",
                text: response.message,
                customClass: {
                  confirmButton: "btn btn-primary",
                },
                buttonsStyling: false,
              }).then(function () {
                // Reload the page
                location.href =
                  "/en/budgets/walk_through/" +
                  user_budget_id +
                  "#non-monthly-expenses-section";
                location.reload();
              });
            }
          },
        });
      } else {
        Swal.fire({
          title: "All fields are required",
          icon: "error",
          customClass: {
            confirmButton: "btn btn-primary",
          },
          buttonsStyling: false,
        });
      }
    }
  );

  // Add Other Non-Monthly Expenses
  $("body").delegate(".add_other_non_monthly_expenses", "click", function (e) {
    last_index = parseInt($(this).attr("last_index")) + 1;
    var user_budget = $(this).attr("user_budget");
    trHTML =
      "<tr>" +
      "<td><input type='text' value='Other' id='non_monthly_expenses_sources" +
      last_index +
      "' name='non_monthly_expenses_sources' class='form-control non_monthly_expenses_sources' required/></td>" +
      "<td><input type='number' value='0.0' id='non_monthly_expenses_expected_amount" +
      last_index +
      "' name='non_monthly_expenses_expected_amount' class='form-control total_non_monthly_expenses_exp' required/>" +
      "<input type='number' value='0.0' id='non_monthly_expenses_actual_amount" +
      last_index +
      "' name='non_monthly_expenses_amount' class='form-control total_non_monthly_expenses_act' required hidden/></td>" +
      "<td>" +
      "<select id='non_monthly_expenses_budget_period" +
      last_index +
      "' name='non_monthly_expenses_budget_period' class='form-control' required>" +
      "<option value='Monthly'>Monthly</option>" +
      "<option value='Yearly'>Yearly</option>" +
      "</select>" +
      "</td>" +
      "<td>" +
      "<i class='fa fa-calendar fa-1 non_monthly_expenses_calender_icon' index='" +
      last_index +
      "' id='non_monthly_expenses_calender_icon" +
      last_index +
      "'></i>" +
      "<input type='text' id='non_monthly_expenses_add_budget_date" +
      last_index +
      "' name='non_monthly_expenses_add_budget_date' class='form-control flatpickr-basic' hidden required>" +
      "</td>" +
      "<td><button class='btn btn-outline-secondary update_non_monthly_expenses_bgt_walkthrough' non_monthly_expenses_index='" +
      last_index +
      "' non_monthly_expenses_id='false' user_budget='" +
      user_budget +
      "'>Update</button></td>" +
      "</tr>";

    $(".total_non_monthly_expenses_row").before(trHTML);
    return false;
  });

  // Event binding for calendar icon click
  $("body").delegate(
    ".non_monthly_expenses_calender_icon",
    "click",
    function (e) {
      var last_index = parseInt($(this).attr("index"));
      var budgetDateId = "#non_monthly_expenses_add_budget_date" + last_index;

      // Show the budget_date input field
      $(budgetDateId).removeAttr("hidden");

      // Get Flatpickr instance of the budget_date input
      var flatpickrInstance = $(budgetDateId).flatpickr();

      // Open the Flatpickr calendar
      if (flatpickrInstance) {
        flatpickrInstance.open();
      }
      setTimeout(function () {
        // Add the 'hidden' attribute back to the #budget_date input (optional)
        $(budgetDateId).attr("hidden", true);
      }, 100);
    }
  );

  // Add Goals Budget Walkthrough
  $("body").delegate(".update_goals_bgt_walkthrough", "click", function (e) {
    e.preventDefault();
    goals_index = $(this).attr("goals_index");
    console.log("goals_index", goals_index);
    goals_account_id = $("#goals_account_id").val();
    user_budget_id = $(this).attr("user_budget");
    id = $(this).attr("goals_id");
    goal_date = $("#goals_add_budget_date" + goals_index).val();
    if ($("#goals_sources" + goals_index).val()) {
      name = $("#goals_sources" + goals_index).val();
    } else {
      name = $("#sub_category_name" + goals_index).val();
    }
    console.log("cat name", name);
    goal_amount = $("#goals_expected_amount" + goals_index).val();
    actual_amount = $("#goals_actual_amount" + goals_index).val();
    sub_category = $(this).attr("category_name");
    console.log("expected amount======>", goal_amount);
    if (name && goal_amount && actual_amount) {
      console.log($(".total_goals_exp").val());
      total_exp_amount = 0;
      total_act_amount = 0;

      $(".total_goals_exp").map(function () {
        total_exp_amount = total_exp_amount + parseFloat($(this).val());
      });

      $(".total_goals_act").map(function () {
        total_act_amount = total_act_amount + parseFloat($(this).val());
      });

      $("#total_goals_exp").text(total_exp_amount);
      $("#total_goals_act").text(total_act_amount);

      var csrfmiddlewaretoken = getCookie("csrftoken");
      $.ajax({
        type: "POST",
        url: "/en/budgets/goals/walk_through",
        data: {
          id: id,
          name: name,
          goal_amount: goal_amount,
          actual_amount: actual_amount,
          category: "Goals",
          goals_account_id: goals_account_id,
          goal_date: goal_date,
          sub_category_name: name,
          user_budget_id: user_budget_id,
          csrfmiddlewaretoken: csrfmiddlewaretoken,
        },
        success: function (response) {
          if (response.status == "true") {
            Swal.fire({
              title: "Saved Successfully",
              icon: "success",
              text: response.message,
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            }).then(function () {
              // Reload the page & takes to goals section
              location.href =
                "/en/budgets/walk_through/" + user_budget_id + "#goals-section";
              location.reload();
            });
          } else {
            Swal.fire({
              title: "Saving Failed!",
              icon: "error",
              text: response.message,
              customClass: {
                confirmButton: "btn btn-primary",
              },
              buttonsStyling: false,
            }).then(function () {
              // Reload the page
              location.href =
                "/en/budgets/walk_through/" + user_budget_id + "#goals-section";
              location.reload();
            });
          }
        },
      });
    } else {
      Swal.fire({
        title: "All fields are required",
        icon: "error",
        customClass: {
          confirmButton: "btn btn-primary",
        },
        buttonsStyling: false,
      });
    }
  });

  // Add Other Goals
  $("body").delegate(".add_other_goals", "click", function (e) {
    last_index = parseInt($(this).attr("last_index")) + 1;
    var user_budget = $(this).attr("user_budget");
    trHTML =
      "<tr>" +
      "<td>" +
      "<input list='browsers' type='text' class='form-control data_list_drop_down' id='sub_category_name" +
      last_index +
      "' name='sub_category_name' placeholder='Goal Name' required data-validation-required-message='This field is required'/>" +
      "<datalist id='browsers" +
      last_index +
      "' name=''>" +
      "{% for data in goal_category %}" +
      "<option value='{{data.name}}' data-id='" +
      last_index +
      "'>{{data.name}}</option>" +
      "{% endfor %}" +
      "</datalist>" +
      "</td>" +
      "<td><input type='number' value='0.0' id='goals_expected_amount" +
      last_index +
      "' name='goals_expected_amount' class='form-control total_goals_exp' required/>" +
      "<input type='number' value='0.0' id='goals_actual_amount" +
      last_index +
      "' name='goals_actual_amount' class='form-control total_goals_act' required hidden/></td>" +
      "<td>" +
      "<i class='fa fa-calendar fa-1 goal_calender_icon' index='" +
      last_index +
      "' id='goal_calender_icon" +
      last_index +
      "'></i>" +
      "<input type='text' id='goals_add_budget_date" +
      last_index +
      "' name='goals_add_budget_date' class='form-control flatpickr-basic' hidden required>" +
      "</td>" +
      "<td><button class='btn btn-outline-secondary update_goals_bgt_walkthrough' goals_index='" +
      last_index +
      "' goals_id='false' user_budget='" +
      user_budget +
      "'>Update</button></td></tr>";

    $(".total_goals_row").before(trHTML);
    return false;
  });

  // Event binding for calendar icon click
  $("body").delegate(".goal_calender_icon", "click", function (e) {
    var last_index = parseInt($(this).attr("index"));
    var budgetDateId = "#goals_add_budget_date" + last_index;
    // Show the budget_date input field
    $(budgetDateId).removeAttr("hidden");

    // Get Flatpickr instance of the budget_date input
    var flatpickrInstance = $(budgetDateId).flatpickr();

    // Open the Flatpickr calendar
    if (flatpickrInstance) {
      flatpickrInstance.open();
    }
    setTimeout(function () {
      // Add the 'hidden' attribute back to the #budget_date input (optional)
      $(budgetDateId).attr("hidden", true);
    }, 100);
  });

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Function for Budget Add Form modal
  $("body").delegate(".add-budget-btn", "click", function (e) {
    e.preventDefault();

    // Fetch category and subcategory from the button attributes
    var category = $(this).data("category");
    var subcategory = $(this).data("subcategory");
    var buttonId = $(this).data("button-id");

    // Set category and subcategory value
    $('#budgetForm [name="categories"]').val(category);
    $('#budgetForm [name="subcategory"]').val(subcategory);

    var budget_cat = "";
    if (category == "Bills & Subscriptions") {
      budget_cat = "bill";
    } else if (category == "Non-Monthly") {
      budget_cat = "non_monthly_expenses";
    } else if (category == "Income") {
      budget_cat = "income";
    } else if (category == "Goals") {
      budget_cat = "goals";
    } else {
      budget_cat = "expenses";
    }

    // Set the budget category ids and required params.
    $('#budgetForm [name="subcategory"]').attr(
      "id",
      budget_cat + "_sources" + buttonId
    );
    $('#budgetForm [name="budget-add-button"]')
      .attr({
        [budget_cat + "_index"]: buttonId,
        category_name: category,
        [budget_cat + "_id"]: "false",
      })
      .addClass("update_" + budget_cat + "_bgt_walkthrough");
    $('#budgetForm [name="budget_period"]').attr(
      "id",
      budget_cat + "_budget_period" + buttonId
    );
    $('#budgetForm [name="budget_date"]').attr(
      "id",
      budget_cat + "_add_budget_date" + buttonId
    );
    $('#budgetForm [name="expected_amount"]').attr(
      "id",
      budget_cat + "_expected_amount" + buttonId
    );
    $('#budgetForm [name="actual_amount"]').attr(
      "id",
      budget_cat + "_actual_amount" + buttonId
    );
    $('#budgetForm [name="account"]').attr("id", budget_cat + "_account_id");

    // Show the modal
    $("#budgetFormModal").modal("show");
  });

  // Function for Transaction Add form Modal
  $("body").delegate(".add-transaction-btn", "click", function (e) {
    e.preventDefault();

    var category = $(this).data("category");
    var subcategory = $(this).data("subcategory");
    var buttonId = $(this).data("button-id");
    var selected_budget = $(this).data("selected-bgt");

    $('#transactionForm [name="user_budget"]').val(selected_budget);

    // Set the value of the category select element
    $('#transactionForm [name="category"] option')
      .filter(function () {
        return $(this).text() === category;
      })
      .prop("selected", true)
      .trigger("change");

    setTimeout(function () {
      $("#transactionForm #subcategory option")
        .filter(function () {
          return $(this).text() === subcategory;
        })
        .prop("selected", true)
        .trigger("change");
    }, 500);

    $("#transactionFormModal").modal("show");
  });

  // Transaction form response function
  $("#transactionForm").submit(function (event) {
    event.preventDefault(); // Prevent the default form submission

    $.ajax({
      type: "POST",
      url: "/en/transaction_add/",
      data: $(this).serialize(),
      success: function (response) {
        if (response.status === "false") {
          Swal.fire({
            title: "Saving Failed!",
            icon: "error",
            text: response.message,
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          }).then(function () {
            // Reload the page
            location.reload();
          });
        } else {
          Swal.fire({
            title: "Saved Successfully",
            icon: "success",
            customClass: {
              confirmButton: "btn btn-primary",
            },
            buttonsStyling: false,
          }).then(function () {
            // Reload the page
            location.reload();
          });
        }
      },
      error: function (xhr, status, error) {
        // Handle AJAX error
        console.error(error);
      },
    });
  });

  // Goal suggestions
  $("body").delegate(".goal-add-btn", "click", function (e) {
    e.preventDefault();

    var goal_name = $(this).data("goal");
    // Set the selected value to Goal name
    $('#goalAddForm [name="sub_category_name"]')
      .val(goal_name)
      .trigger("change");
  });

  // Budget Walk-through suggestions
  $("body").delegate(".sub-cat-name", "click", function (e) {
    e.preventDefault();

    // Fetch the Category & Sub-category
    var name = $(this).data("name");
    var category = $(this).data("category");
    console.log("Name ==>", name, "Category==>", category);

    // This block fetches the last index from the btn and set the
    // selected suggestion values of category & sub-category name
    if (category === "Income") {
      last_index = parseInt($(".add_other_income").attr("last_index")) + 1;
      $(".add_other_income").click();
      input_id = "#income_sources" + last_index;
      $(input_id).val(name);
    } else if (category === "Bills & Subscriptions") {
      last_index = parseInt($(".add_other_bill").attr("last_index")) + 1;
      $(".add_other_bill").click();
      input_id = "#bill_sources" + last_index;
      $(input_id).val(name);
    } else if (category === "Non-Monthly") {
      last_index =
        parseInt($(".add_other_non_monthly_expenses").attr("last_index")) + 1;
      $(".add_other_non_monthly_expenses").click();
      input_id = "#non_monthly_expenses_sources" + last_index;
      $(input_id).val(name);
    } else if (category === "Goals") {
      last_index = parseInt($(".add_other_goals").attr("last_index")) + 1;
      $(".add_other_goals").click();
      input_id = "#sub_category_name" + last_index;
      $(input_id).val(name);
    } else {
      // Sets the values for expenses sections
      last_index = parseInt($(".add_other_expenses ").attr("last_index")) + 1;
      $(".add_other_expenses ").click();
      btn_id = "#other_exp_btn" + last_index;
      $(btn_id).attr("category_name", category);
      input_id = "#expenses_sources" + last_index;
      $(input_id).val(name);
      $(".other_exp_name").val(category);
    }
  });

  // Compare different budget tables dropdown
  // Dropdown function for Budget 1 Table
  $("body").delegate("#spentAmountDropdown", "change", function () {
    var select = $(this);
    var selectedValue = select.val();

    $(".spent-amount").each(function (index) {
      var element = $(this);
      var spentAmount;

      if (selectedValue === "monthly") {
        spentAmount = parseFloat(element.attr("data-monthly"));
      } else {
        spentAmount = parseFloat(element.attr("data-spent"));
      }

      element.text(spentAmount.toFixed(2));

      // Update the remaining balance
      var remainingBalance = element.attr("data-bgt") - spentAmount;
      $(".remaining-balance").eq(index).text(remainingBalance.toFixed(2));
    });
  });

  // Dropdown function for Budget 2 Table
  $("body").delegate("#spentAmountDropdown2", "change", function () {
    var select = $(this);
    var selectedValue = select.val();

    $(".spent-amount2").each(function (index) {
      var element = $(this);
      var spentAmount;

      if (selectedValue === "monthly2") {
        spentAmount = parseFloat(element.attr("data-monthly2"));
      } else {
        spentAmount = parseFloat(element.attr("data-spent2"));
      }

      element.text(spentAmount.toFixed(2));

      // Update the remaining balance
      var remainingBalance = element.attr("data-bgt2") - spentAmount;
      $(".remaining-balance2").eq(index).text(remainingBalance.toFixed(2));
    });
  });

  // Bill dropdown filter
  $("#bill_select").on("change", function (e) {
    $("#bill_filter_form").submit();
  });

  // Function for Mortgage chart view
  $(".chart-view-dropdown").on("change", function (e) {
    // Fetch the selected chart view
    let chart_view = $(this).val();

    // Remove tickAmount, if "Monthly View" selected
    if (chart_view === "Monthly View") {
      if (areaChart) {
        areaChart.updateOptions({
          xaxis: {
            categories: mortgage_date_data,
            tickAmount: undefined, // Removes tickAmount
          },
        });
      }
    }
    // If yearly view selected, reloads the page
    else {
      location.reload();
    }
  });

  /*
   * Right sidebar scripts handled here.
   * 1. Handled on Click events for sidebar items
   * 2. Open and close sidebar
   * 3. Handle AI Chat contents
   * 4. Handle Feedback contents
   * 5. Handle Notes contents
   * 6. Handle Interactive Lessons
   *
   */

  // List of sidebar items
  const sidebarItems = [
    {
      button: "#aiChatButton",
      content: "#aiChatContent",
      header: "AI Chat",
      description: "Start a conversation with AI",
    },
    {
      button: "#feedbackButton",
      content: "#feedbackContent",
      header: "Feedback",
      description: "Please provide proper information with feedback",
    },
    {
      button: "#notesButton",
      content: "#notesContent",
      header: "Notes",
      description: "Take a quick notes",
    },
    {
      button: "#lessonsButton",
      content: "#lessonsContent",
      header: "Interactive Lessons",
      description: "Page interactive lessons",
    },
  ];

  // Helper function to activate a sidebar item
  function activateButton(button, content) {
    //! reset all buttons and content
    sidebarItems.forEach((item) => {
      $(item.content).attr("data-visible", "false");
      $(item.button)
        .removeClass("btn-primary")
        .addClass("btn-outline-secondary")
        .attr("aria-expanded", "false");

      // set heading
      if (item.button === button) {
        $("#rightSidebarHeader").text(item.header);
        $("#rightSidebarDescription").text(item.description);
      }
    });

    // set the clicked button and content as active
    $(button)
      .removeClass("btn-outline-secondary")
      .addClass("btn-primary")
      .attr("aria-expanded", "true");
    $(content).attr("data-visible", "true");
  }

  // add click event listener for all buttons
  sidebarItems.forEach((item) => {
    $(item.button).on("click", () => {
      activateButton(item.button, item.content);
    });
  });

  // Activate AI Chat by default when opening the sidebar
  activateButton("#aiChatButton", "#aiChatContent");

  // Open and close sidebar
  $("#rightSettingsButton").click(() => {
    const visibility = $("#rightSettingBody").attr("data-visible");
    if (visibility === "false") {
      $("#rightSettingBody").attr("data-visible", "true");
      $("#rightSettingsButton").attr("aria-expanded", "true");
    }
  });

  $("#closeSidebar").click(() => {
    const visibility = $("#rightSettingBody").attr("data-visible");
    if (visibility === "true") {
      $("#rightSettingBody").attr("data-visible", "false");
      $("#rightSettingsButton").attr("aria-expanded", "false");
    }
  });

  // Helper function to push messages to chat window
  function pushUserChat(content, prepend) {
    const userAvatar = $('#chatContainer').attr('data-avatarUrl');
    const chatHTML = `
        <div class="chat chat-right">
            <div class="chat-avatar">
                <span class="avatar box-shadow-1 cursor-pointer">
                    <img src="${userAvatar}" alt="logo" height="36" width="36"  />
                </span>
            </div>
            <div class="chat-body">
                <div class="chat-content">
                    <p>${content}</p>
                </div>
            </div>
        </div>
    `;

    if (prepend) {
      $("#chatMsgContainer").prepend(chatHTML);
    } else {
      $("#chatMsgContainer").append(chatHTML);
    }
  }

  function pushAIChat(content, prepend) {
    const userAvatar = $('#chatContainer').attr('data-avatarUrl');
    const chatHTML = `
        <div class="chat chat-left">
            <div class="chat-avatar">
                <span class="avatar box-shadow-1 cursor-pointer">
                    <img src="${userAvatar}" alt="avatar"  height="36" width="36" />
                </span>
            </div>
            <div class="chat-body">
                <div class="chat-content">
                    <p>${content}</p>
                </div>
            </div>
        </div>`;

    if (prepend) {
      $("#chatMsgContainer").prepend(chatHTML);
    } else {
      $("#chatMsgContainer").append(chatHTML);
    }
  }

  // Helper function to show all chats loaded indicator
  function allChatsLoaded() {
    const chatHTML = `
            <p class="text-center"> No messages left</p>
        `;
    $("#chatContainer").prepend(chatHTML);
  }

  // Function to load all chats -> API call
  (function () {
    let page = 1;
    let loading = false;
    let has_more = true;

    function loadChats() {
      if (loading || !has_more) return;
      loading = true;

      // previous scroll height
      const chatContainer = $("#chatContainer");
      const previousScrollHeight = chatContainer[0]?.scrollHeight || 0;

      // Make ajax call
      $.ajax({
        url: $("#chatContainer").data("url"),
        type: "GET",
        data: {
          page,
        },
        dataType: "json",
        success: function (response) {
          const messages = response.messages;
          if (messages.length === 0 && page === 1) {
            pushAIChat(
              "Hi, I'm your personal AI assistant. How can I help you?",
              true
            );
          }

          messages.forEach((msg) => {
            if (msg.ai_msg) pushAIChat(msg.ai_msg, true);
            if (msg.user_msg) pushUserChat(msg.user_msg, true);
          });

          page++; // Increment page
          has_more = response.has_more;

          // Stop scrolling if no more data
          if (!has_more) {
            $("#chatContainer").off("scroll");
            allChatsLoaded();
          }

          // Adjust scroll position to maintain view
          const newScrollHeight = chatContainer[0]?.scrollHeight || 0;
          const scrollDiff = newScrollHeight - previousScrollHeight;
          chatContainer.scrollTop(scrollDiff);
          loading = false;
        },
        error: function (xhr, status, error) {
          console.log(error);
          loading = false;
        },
      });
    }

    // Initial chat load
    loadChats();

    // Scroll event to load more chats
    $("#chatContainer").on("scroll", function () {
      if ($("#chatContainer").scrollTop() === 0 && !loading) {
        loadChats();
      }
    });
  })();

  // Prevent 'Enter' key from going new line in user msg textarea
  $("#aiMsgInput").on("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      $("#sendMessageButton").click();
    }
  });

  // Send message to ai through post request
  $("#sendMessageButton").click(function (e) {
    e.preventDefault();
    const msg = $("#aiMsgInput").val();
    if (msg.trim() === "") return;
    // API call to send message
    $.ajax({
      method: "POST",
      url: $("#sendMessageButton").data("url"),
      data: {
        message: msg,
      },
      headers: {
        "X-CSRFToken": csrftoken,
      },
      dataType: "json",
      beforeSend: function () {
        pushUserChat(msg, false);
        $("#aiMsgInput").val("");
        $("#chatContainer").scrollTop($("#chatContainer")[0].scrollHeight);
      },
      success: function (response) {
        pushAIChat(response.ai_res, false);
        $("#chatContainer").scrollTop($("#chatContainer")[0].scrollHeight);
      },
      error: function (xhr, status, error) {
        console.log(error);
      },
    });
  });

  /*
   * Helper function to capture screenshot & implement edit by fabric.js
   */

  function captureScreenshotAndEdit(
    screenShotButton,
    uploadScreenShotButton,
    imageUploadNotification,
    imageInputID,
    fileName
  ) {
    let canvas;
    let img; // Store the original image reference
    let currentMode = null;
    let existingObjects = []; // To store non-image objects between modes
    let textBoxCounter = 0; // Track number of text boxes added

    // Generate file name
    const generateFileName = () => {
      const date = new Date();
      const year = date.getFullYear();
      const month = (date.getMonth() + 1).toString().padStart(2, "0");
      const day = date.getDate().toString().padStart(2, "0");
      const hours = date.getHours();
      const minutes = date.getMinutes().toString().padStart(2, "0");

      const period = hours >= 12 ? "pm" : "am";
      const formattedHours = (((hours + 11) % 12) + 1).toString();

      return `${fileName}_${year}${month}${day}_${formattedHours}_${minutes}${period}.png`;
    };

    // Initialize canvas
    function initCanvas(image, containerWidth, containerHeight) {
      img = image;
      const dimensions = calculateCanvasDimensions(containerWidth);
      const canvasEl = document.getElementById('snapEditCanvas');

      if (canvas) {
        canvas.dispose();
      }

      canvasEl.width = dimensions.width;
      canvasEl.height = dimensions.height;

      canvas = new fabric.Canvas(canvasEl, {
        preserveObjectStacking: true,
        selection: true,
        defaultCursor: 'default',
        backgroundColor: '#f8f9fa'
      });

      const fabricImage = new fabric.Image(img, {
        left: 0,
        top: 0,
        selectable: false,
        scaleX: dimensions.width / img.width,
        scaleY: dimensions.height / img.height,
        originX: 'left',
        originY: 'top'
      });

      canvas.setBackgroundImage(fabricImage, function () {
        // Restore existing objects (like textboxes)
        existingObjects.forEach(obj => canvas.add(obj));
        canvas.renderAll();
        setupTextEditing();
      });

      // Enable draw mode by default
      setTimeout(() => {
        setMode('draw');
      }, 100);

      // Add keyboard event listener for Delete key
      canvas.on('selection:created', handleSelection);
      canvas.on('selection:cleared', handleSelection);
      canvas.on('object:removed', handleSelection);

      function handleSelection() {
        if (canvas.getActiveObject()) {
          $(document).on("keydown.delete", function (e) {
            if (e.key === "Delete") {
              e.preventDefault(); // Prevent scrolling
              const activeObjects = canvas.getActiveObjects();

              activeObjects.forEach((obj) => {
                canvas.remove(obj);
                existingObjects = existingObjects.filter((o) => o !== obj);
              });

              canvas.discardActiveObject().renderAll();
              $(document).off("keydown.delete"); // Remove the handler after deletion
            }
          });
        } else {
          $(document).off("keydown.delete");
        }
      }
    }

    // Mode management function
    function setMode(newMode) {
      // Exit current mode
      switch (currentMode) {
        case 'draw':
          canvas.isDrawingMode = false;
          $("#enableDrawing").removeClass("btn-danger").addClass("btn-outline-success");
          break;
        case 'text':
          // No specific cleanup needed for text mode
          break;
        case 'blackbox':
        case 'whitebox':
          existingObjects = canvas.getObjects().filter(obj => obj.type === 'rect');
          break;
      }

      // Enter new mode
      switch (newMode) {
        case 'draw':
          canvas.isDrawingMode = true;
          canvas.freeDrawingBrush.width = 2;
          canvas.freeDrawingBrush.color = $("#textColor").val();
          $("#enableDrawing").removeClass("btn-outline-success").addClass("btn-danger");
          break;
        case 'text':
          // Add new text box without affecting existing ones
          addTextBox();
          break;
        case 'blackbox':
          addBox('#000000');
          break;
        case 'whitebox':
          addBox('#ffffff');
          break;
        case 'selection':
          canvas.isDrawingMode = false;
          canvas.selection = true;
          canvas.getObjects().forEach(obj => obj.selectable = true);
          break;
      }

      currentMode = newMode;
      updateButtonStates();
    }

    // Function to add a new text box
    function addTextBox() {
      textBoxCounter++;
      const text = new fabric.IText(`Text ${textBoxCounter}`, {
        left: 50 + (textBoxCounter * 20),
        top: 50 + (textBoxCounter * 20),
        fontFamily: 'Arial',
        fill: $('#textColor').val(),
        fontSize: parseInt($('#textSize').val()),
        hasControls: true,
        padding: 10,
        editable: true,
        borderColor: '#4285f4',
        cornerColor: '#4285f4',
        cornerSize: 10,
        transparentCorners: false,
        selectable: true
      });

      canvas.add(text);
      canvas.setActiveObject(text);
      canvas.bringToFront(text);

      // Focus on the new text box
      setTimeout(() => {
        text.enterEditing();
        text.selectAll();
        const textarea = text.hiddenTextarea;
        if (textarea) {
          textarea.focus();
          $(textarea).on('keydown', function (e) {
            e.stopPropagation();
          });
        }
      }, 100);
    }

    function updateButtonStates() {
      $("#enableSelection, #enableDrawing, #addText, #addBlackBox, #addWhiteBox").removeClass("active");
      if (currentMode === 'draw') {
        $("#enableDrawing").addClass("active");
      } else if (currentMode === 'text') {
        $("#addText").addClass("active");
      } else if (currentMode === 'blackbox') {
        $("#addBlackBox").addClass("active");
      } else if (currentMode === 'whitebox') {
        $("#addWhiteBox").addClass("active");
      }
    }

    $("#enableSelection").click(function () {
      setMode('selection');
    });

    function setupTextEditing() {
      // Fix for text editing in Bootstrap modal
      canvas.on('text:editing:entered', function (options) {
        $('.canvas-container').css('z-index', '1051');
        const text = options.target;
        const textarea = text.hiddenTextarea;

        if (textarea) {
          // Prevent event bubbling
          $(textarea).off('keydown').on('keydown', function (e) {
            e.stopPropagation();
            e.stopImmediatePropagation();
          });

          // Ensure focus
          setTimeout(() => {
            textarea.focus();
          }, 50);
        }
      });

      canvas.on('text:editing:exited', function () {
        $('.canvas-container').css('z-index', '');
      });
    }

    // Calculate canvas dimensions
    function calculateCanvasDimensions(containerWidth) {
      const maxWidth = Math.min(containerWidth - 40, img.width);
      const maxHeight = Math.min(window.innerHeight - 200, img.height);

      const aspectRatio = img.width / img.height;

      let width = maxWidth;
      let height = width / aspectRatio;

      if (height > maxHeight) {
        height = maxHeight;
        width = height * aspectRatio;
      }

      return { width, height };
    }

    // Show modal
    function showModal() {
      const modal = new bootstrap.Modal(document.getElementById('editorModal'), {
        backdrop: "static",
        keyboard: true,
        focus: false
      });
      modal.show();

      // Prevent Bootstrap from interfering with text editing
      $(document).on('focusin', function (e) {
        if ($(e.target).closest('.canvas-container').length &&
          $(e.target).is('textarea.fabric-textarea')) {
          e.stopPropagation();
        }
      });
    }

    // Event handlers
    screenShotButton.on("click", function () {
      const ignoreElementIds = ["rightSettingBody", "accSubmitError"];
      html2canvas(document.body, {
        ignoreElements: (element) => ignoreElementIds.includes(element.id),
        width: window.innerWidth,
        height: window.innerHeight,
        scale: 1,
        logging: false,
        useCORS: true
      }).then((snapshot) => {
        const image = new Image();
        image.src = snapshot.toDataURL("image/png");

        image.onload = function () {
          initCanvas(image, window.innerWidth, window.innerHeight);
          showModal();
        };
      }).catch(console.error);
    });

    uploadScreenShotButton.on("change", function (event) {
      const file = event.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          const image = new Image();
          image.src = e.target.result;

          image.onload = function () {
            initCanvas(image, window.innerWidth, window.innerHeight);
            showModal();
          };
        };
        reader.readAsDataURL(file);
      }
    });

    $("#downloadEditedImage").click(function () {
      const editedImage = canvas.toDataURL("image/png");
      const link = document.createElement("a");
      link.href = editedImage;
      link.download = generateFileName();
      link.click();
    });

    $("#enableDrawing").click(function () {
      if (currentMode !== 'draw') {
        setMode('draw');
      } else {
        setMode('selection');
      }
    });

    $("#clearCanvas").click(function () {
      const backgroundImage = canvas.backgroundImage;
      canvas.getObjects().forEach((obj) => {
        if (obj !== backgroundImage) {
          canvas.remove(obj);
        }
      });
      existingObjects = []; // Clear stored objects as well
      textBoxCounter = 0; // Reset text box counter
      canvas.renderAll();
    });

    $("#addText").click(function () {
      if (currentMode !== 'text') {
        setMode('text');
      } else {
        // If already in text mode, add another text box
        addTextBox();
      }
    });

    $("#textColor").change(function () {
      const activeObject = canvas.getActiveObject();
      if (activeObject?.type === 'i-text') {
        activeObject.set('fill', $(this).val());
        canvas.renderAll();
      }
      if (currentMode === "draw") {
        canvas.freeDrawingBrush.color = $(this).val();
      }
    });

    $("#textSize").change(function () {
      const activeObject = canvas.getActiveObject();
      if (activeObject?.type === 'i-text') {
        activeObject.set('fontSize', parseInt($(this).val()));
        canvas.renderAll();
      }
    });

    $("#addBlackBox").click(function () {
      setMode('blackbox');
    });

    $("#addWhiteBox").click(function () {
      setMode('whitebox');
    });

    function addBox(color) {
      const box = new fabric.Rect({
        left: 50,
        top: 50,
        width: 100,
        height: 50,
        fill: color,
        stroke: '#000000',
        strokeWidth: 1,
        selectable: true,
        hasControls: true
      });
      canvas.add(box);
      canvas.setActiveObject(box);
    }

    $("#closeEditorModal").click(function () {
      $('#editorModal').removeClass('show').css('display', 'none');
      $('.modal-backdrop').remove();
    });

    $("#saveEditedImage").click(function () {
      if (canvas) {
        const dataURL = canvas.toDataURL("image/png");
        const file = dataURLToFile(dataURL, generateFileName());

        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);

        const fileInput = document.querySelector(imageInputID);
        fileInput.files = dataTransfer.files;

        imageUploadNotification.removeClass("d-none");
        $('#editorModal').removeClass('show').css('display', 'none');
        $('.modal-backdrop').remove();
        canvas.clear();
        existingObjects = []; // Clear stored objects
        textBoxCounter = 0; // Reset text box counter
      }
    });

    function dataURLToFile(dataURL, filename) {
      const arr = dataURL.split(",");
      const mime = arr[0].match(/:(.*?);/)[1];
      const binary = atob(arr[1]);
      const array = [];
      for (let i = 0; i < binary.length; i++) {
        array.push(binary.charCodeAt(i));
      }
      return new File([new Uint8Array(array)], filename, { type: mime });
    }

    updateButtonStates();
  }


  // Initialize when DOM is ready
  $(document).ready(function () {
    // Make sure all required libraries are loaded
    if (typeof fabric !== 'undefined' && typeof html2canvas !== 'undefined' && typeof bootstrap !== 'undefined') {
      const screenShotButton = $("#takeScreenshot");
      const uploadScreenShotButton = $("#feedbackImg");
      const imageUploadNotification = $("#feedbackSnapAdded");
      const imageInputID = "#screenshotData";
      const fileName = "feedback_img";

      captureScreenshotAndEdit(
        screenShotButton,
        uploadScreenShotButton,
        imageUploadNotification,
        imageInputID,
        fileName
      );
    } else {
      console.error("Required libraries not loaded");
    }
  });

  // Submit feedback form
  (function () {
    // capture screenshot and Edit
    const screenShotButton = $("#takeScreenshot");
    const uploadScreenShotButton = $("#feedbackImg");
    const imageUploadNotification = $("#feedbackSnapAdded");
    const imageInputID = "#screenshotData";
    const fileName = "feedback_img";
    captureScreenshotAndEdit(
      screenShotButton,
      uploadScreenShotButton,
      imageUploadNotification,
      imageInputID,
      fileName
    );

    // Handle Form submission
    $("#feedbackForm").submit(function (e) {
      e.preventDefault();

      // validate form data and all requried fieds
      let isValid = true;

      $(this)
        .find("input[required], select[required], textarea[required]")
        .each(function () {
          const $field = $(this);
          if (!$field.val()) {
            // if field is invalid add error class and show message
            $field.addClass("is-invalid").removeClass("is-valid");
            isValid = false;
          } else {
            // if field is valid remove error class and hide message
            $field.removeClass("is-invalid").addClass("is-valid");
          }
        });

      // Live validation on input change
      $("input[required], select[required], textarea[required]").on(
        "input change",
        function () {
          const $field = $(this);

          if (!$field.val()) {
            $field.addClass("is-invalid").removeClass("is-valid");
          } else {
            $field.addClass("is-valid").removeClass("is-invalid");
          }
        }
      );
      // Form submission with validate data
      if (isValid) {
        const formData = new FormData(this);
        $.ajax({
          url: $(this).attr("action"),
          method: "POST",
          data: formData,
          processData: false,
          contentType: false,
          enctype: "multipart/form-data",
          success: function (response) {
            if (response.status === "success") {
              $("#feedbackForm")
                .find(".is-valid, .is-invalid")
                .removeClass("is-valid is-invalid");

              $("#feedbackForm")[0].reset();
              $("#feedbackSnapAdded").addClass("d-none");
              // show success message
              Swal.fire({
                title: response.message,
                icon: "success",
                customClass: {
                  confirmButton: "btn btn-primary",
                },
                buttonsStyling: false,
              });
              $("#closeSidebar").click();
            } else {
              // show error message
              Swal.fire({
                title: response.error,
                icon: "error",
                customClass: {
                  confirmButton: "btn btn-danger",
                },
                buttonsStyling: false,
              });
              $("#closeSidebar").click();
            }
          },
          error: function (xhr, status, error) {
            // Handle error response
            console.error("Error submitting feedback:", error);
          },
        });
      }
    });
  })();

  // Handle Notes Here
  (function () {
    function renderNotes(notes) {
      $("#notesContainer").empty();
      if (notes.length === 0) {
        $("#notesContainer").append(`<p>No notes found</p>`);
      }

      notes.forEach((note) => {
        $("#notesContainer").append(
          `
                <div class="h-100" id="accParent-${note.id}">
                    <div class="card">
                        <h2 class="mb-0" id="heading-${note.id}">
                            <button 
                                class="btn acc-custom-btn btn-outline-secondary btn-block text-left" 
                                type="button" 
                                data-toggle="collapse" 
                                data-target="#collapse${note.id}" 
                                aria-expanded="true" 
                                aria-controls="collapse${note.id}">
                                <div>
                                    <span class="float-left">${note.title}</span>
                                    <span class="float-right acc-arrow-icon text-primary">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-down-fill" viewBox="0 0 16 16">
                                            <path d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"/>
                                        </svg>
                                    </span>
                                </div>
                            </button>
                        </h2>

                        <div 
                            id="collapse${note.id}" 
                            class="collapse p-1 pb-0 mt-1 border rounded-sm" 
                            aria-labelledby="heading-${note.id}" 
                            data-parent="#accParent-${note.id}">
                            <div class="card text-white accordion-card-body">
                                <h6>${note.added_on}</h6>
                                ${note.notes}
                                <div class="d-flex justify-content-around mt-2">
                                    <button class="btn btn-danger delete-note-btn" data-title="${note.title}" data-id="${note.id}">
                                        Delete
                                    </button>
                                    <button class="btn btn-success edit-note-btn" data-title="${note.title}" data-id="${note.id}" data-notes="${note.notes}">
                                        Edit
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                `
        );
      });
    }

    function loadNotes() {
      $.ajax({
        type: "GET",
        url: $("#notesContainer").data("url"),
        dataType: "json",
        success: function (response) {
          if (response.success === "true") {
            if (response.data.length > 0) {
              renderNotes(response.data);
            } else renderNotes([]);
          }
        },
      });
    }

    loadNotes();

    function deleteNote(noteId, noteTitle) {
      $.ajax({
        type: "POST",
        url: $("#createNoteForm").attr("action"),
        data: {
          notes_method: "Delete",
          select_title: noteTitle,
          csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
        },
        success: function (response) {
          if (response.status === "Deleted Successfully") {
            Swal.fire({
              title: "Note deleted successfully!",
              icon: "success",
            });
            loadNotes(); // Reload notes to reflect the deletion
          } else {
            Swal.fire({
              title: response.status,
              icon: "error",
            });
          }
        },
        error: function (xhr, status, error) {
          console.error("Error deleting note:", error);
          Swal.fire({
            title: "Error deleting the note.",
            text: error,
            icon: "error",
          });
        },
      });
    }

    // Create note form submission
    $("#createNoteForm").submit(function (e) {
      e.preventDefault(); // Prevent the default form submission behavior

      let isValid = true;
      $(this)
        .find("input[required], textarea[required]")
        .each(function () {
          const $field = $(this);
          if (!$field.val()) {
            $field.addClass("is-invalid").removeClass("is-valid");
            isValid = false;
          } else {
            $field.removeClass("is-invalid").addClass("is-valid");
          }
        });

      if (isValid) {
        const formData = new FormData(this);
        formData.append("notes_method", "Add");

        $.ajax({
          url: $(this).attr("action"),
          method: "POST",
          data: formData,
          processData: false,
          contentType: false,
          success: function (response) {
            if (response.status === "Added") {
              Swal.fire({
                title: "Note added successfully!",
                icon: "success",
              });
              $("#createNoteForm").trigger("reset");
              $("#createNoteForm input, textarea").removeClass(
                "is-valid is-invalid"
              );
              $("#closeSidebar").click();
              loadNotes();
            } else {
              Swal.fire({
                title: response.status,
                icon: "error",
              });
            }
          },
          error: function (xhr, status, error) {
            console.error("Error submitting form:", error);
            Swal.fire({
              title: "Error submitting the form.",
              text: error,
              icon: "error",
            });
          },
        });
      }
    });

    // Handle delete note button click
    $("#notesContainer").on("click", ".delete-note-btn", function () {
      const noteId = $(this).data("id");
      const noteTitle = $(this).data("title");
      $("#closeSidebar").click();

      Swal.fire({
        title: "Are you sure?",
        text: "This will delete the note permanently!",
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Yes, delete it!",
      }).then((result) => {
        if (result.isConfirmed) {
          deleteNote(noteId, noteTitle);
        }
      });
    });

    // Handle edit note button click
    $("#notesContainer").on("click", ".edit-note-btn", function () {
      $("#closeSidebar").click();
      const noteTitle = $(this).data("title");
      const noteNotes = $(this).data("notes");
      $("#editNoteForm input[name=title]").val(noteTitle);
      $("#editNoteForm textarea[name=notes]").val(noteNotes);
      const modal = new bootstrap.Modal($("#editNoteModal").get(0), {
        backdrop: "static",
        keyboard: false,
      });
      modal.show();

      $("#editNoteForm").submit(function (e) {
        e.preventDefault();

        const formData = new FormData(this);
        formData.append("notes_method", "Update");
        formData.append("select_title", noteTitle);

        $.ajax({
          url: $(this).attr("action"),
          method: "POST",
          data: formData,
          processData: false,
          contentType: false,
          success: function (response) {
            if (response.status === "Updated") {
              Swal.fire({
                title: "Note updated successfully!",
                icon: "success",
              });
              modal.hide();
              loadNotes();
            } else {
              Swal.fire({
                title: response.status,
                icon: "error",
              });
              modal.hide();
            }
          },
        });
      });
    });
  })();

  // Helper function to render Lessons content
  function renderAccordion(data, curPath) {
    const html = `
        <div class="h-100" id="accParent-${data.number}">
            <div class="card">
                <h2 class="mb-0" id="heading-${data.number}">
                    <button 
                        class="btn acc-custom-btn ${curPath === data.queryParamValue
        ? "btn-outline-primary"
        : "btn-outline-secondary"
      } btn-block text-left" 
                        type="button" 
                        data-toggle="collapse" 
                        data-target="#collapse${data.number}" 
                        aria-expanded="true" 
                        aria-controls="collapse${data.number}">
                        <div>
                            <span class="float-left">${data.lesson_name}</span>
                            <span class="float-right acc-arrow-icon text-primary">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-down-fill" viewBox="0 0 16 16">
                                    <path d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"/>
                                </svg>
                            </span>
                        </div>
                    </button>
                </h2>

                <div 
                    id="collapse${data.number}" 
                    class="collapse pt-1" 
                    aria-labelledby="heading-${data.number}" 
                    data-parent="#accParent-${data.number}">
                    <div class="card text-white accordion-card-body ">
                        ${data.lesson_content} 
                    </div>
                </div>
            </div>
        </div>
        `;

    $("#lessonsContent").append(html);
  }

  // Backend call to fetch the data
  $.ajax({
    type: "GET",
    url: $("#lessonsContent").data("url"),
    dataType: "json",
    success: function (response) {
      if (response.status === "success") {
        const data = response.data;
        const curPath = $("#lessonsContent").data("current-path");
        data.forEach(function (item) {
          renderAccordion(item, curPath);
        });
      }
    },
  });

  // Accordion arrow rotation
  $(document).on("click", ".acc-custom-btn", function () {
    const $icon = $(this).find(".acc-arrow-icon svg");
    const isExpanded = $(this).attr("aria-expanded") === "true";
    if (isExpanded) {
      $icon.addClass("rotate-180deg");
    } else {
      $icon.removeClass("rotate-180deg");
    }
  });

  $("#errorLogsTable").DataTable({
    dom: '<"top"lf>t<"bottom"ip>',
    processing: true,
    serverSide: true,
    order: [[1, "desc"]],
    pageLength: 10,
    lengthMenu: [5, 10, 25, 50],
    responsive: true,
    ajax: {
      url: "/en/app-error-report/",
      type: "GET",
      data: function (d) {
        d.datatables = true;
        d.status = $("#filterByStatus").val();
      },
    },
    columns: [
      {
        data: null,
        orderable: false,
        render: function (data, type, row, meta) {
          return `<input type="checkbox" class="error_log_checkbox" value="${row.id}">`;
        },
      },
      { data: "code", orderable: true },
      { data: "timestamp", orderable: true },
      { data: "exception_type", orderable: false },
      { data: "request_path", orderable: false },
      { data: "error_message", orderable: false },
      { data: "count", orderable: true },
      {
        data: "status",
        orderable: false,
        render: function (data) {
          let statusClass = "";
          if (data === "open") statusClass = "badge badge-danger";
          else if (data === "resolved") statusClass = "badge badge-success";
          else if (data === "skip") statusClass = "badge badge-warning";
          else statusClass = "badge badge-secondary";
          return `<span class="${statusClass}">${data}</span>`;
        },
      },
      {
        data: null,
        orderable: false,
        render: function (data, type, row) {
          // Add an "eye" button for triggering the modal
          return `
                    <button type="button" class="btn btn-sm btn-primary view-details-btn" data-id="${row.id}" data-toggle="modal" data-target="#detailsModal">
                        <i class="fa fa-eye"></i>
                    </button>`;
        },
      },
    ],
  });

  // Filter by status event listener
  $("#filterByStatus").on("change", function () {
    $("#errorLogsTable").DataTable().ajax.reload();
  });

  // Handle "View Details" button click
  $(document).on("click", ".view-details-btn", function () {
    const rowId = $(this).data("id");

    // Fetch row details via AJAX
    $.ajax({
      url: `/en/app-error-report/details/${rowId}/`,
      type: "GET",
      success: function (response) {
        // Populate modal content
        $("#detailsModal .modal-title").text(
          `Details for Error #${response.id}`
        );
        $("#detailsModal .modal-body").html(`
                <p><strong>Status Code:</strong> ${response.code}</p>
                <p><strong>Timestamp:</strong> ${response.timestamp}</p>
                <p><strong>Error Type:</strong> ${response.exception_type}</p>
                <p><strong>Request Path:</strong> ${response.request_path}</p>
                <p><strong>Error Message:</strong> ${response.error_message}</p>
                <p><strong>Traceback:</strong> ${response.traceback}</p>
                <p><strong>Count:</strong> ${response.count}</p>
                <p><strong>Status:</strong> ${response.status}</p>
            `);
      },
      error: function () {
        $("#detailsModal .modal-body").html(
          "<p class='text-danger'>Failed to load details. Please try again.</p>"
        );
      },
    });
  });

  // Handle Error report table action
  (function () {
    const allCheckBox = $("#selectAllCheckbox");
    const actionSelector = $("#actionSelector");
    const statusSelector = $("#statusSelector");
    const statusSelectorContainer = $("#statusSelectorContainer");
    const handleErrorBtn = $("#handleErrorBtn");

    // Handle "Select All" checkbox
    allCheckBox.on("change", function () {
      const isChecked = $(this).prop("checked");
      $(".error_log_checkbox").prop("checked", isChecked);
    });

    // Update "Select All" checkbox based on individual row selection
    $("#errorLogsTable").on("change", ".error_log_checkbox", function () {
      const allCheckboxes = $(".error_log_checkbox").length;
      const checkedCheckboxes = $(".error_log_checkbox:checked").length;
      allCheckBox.prop("checked", allCheckboxes === checkedCheckboxes);
    });

    // Helper function to get selected rows
    function getSelectedRows() {
      return $(".error_log_checkbox:checked")
        .map(function () {
          return $(this).val();
        })
        .get();
    }

    // Reset all components
    function resetComponents() {
      // Clear dropdowns
      actionSelector.val("").trigger("change");
      statusSelector.val("").addClass("d-none").trigger("change");

      // Hide and reset the action button
      handleErrorBtn
        .addClass("d-none")
        .removeClass("btn-primary btn-danger")
        .text("");

      // Uncheck all checkboxes
      $(".error_log_checkbox").prop("checked", false);
      allCheckBox.prop("checked", false);
    }

    // Handle action selection
    actionSelector.on("change", function () {
      const selectedAction = $(this).val();
      if (selectedAction === "delete") {
        handleErrorBtn
          .removeClass("d-none btn-primary")
          .addClass("btn-danger")
          .text("Delete Selected");
        statusSelectorContainer.addClass("d-none");
      } else if (selectedAction === "update_status") {
        statusSelectorContainer.removeClass("d-none");
        handleErrorBtn.addClass("d-none");
        statusSelector.on("change", function () {
          const selectedStatus = $(this).val();
          if (selectedStatus === "") {
            handleErrorBtn.addClass("d-none");
          } else {
            handleErrorBtn
              .addClass("btn-primary")
              .removeClass("btn-danger d-none")
              .text("Change Status");
          }
        });
      } else {
        statusSelectorContainer.addClass("d-none");
        handleErrorBtn.addClass("d-none");
      }
    });

    // Handle button click
    $(document).on("click", "#handleErrorBtn", function () {
      const selectedRows = getSelectedRows();
      const action = actionSelector.val();
      const selectedStatus = statusSelector.val();

      // Handle validations
      if (selectedRows.length === 0) {
        Swal.fire({
          title: "Please select at least one row",
          icon: "error",
          customClass: { confirmButton: "btn btn-danger" },
          buttonsStyling: false,
        });
        return;
      }

      if (action === "update_status" && selectedStatus === "") {
        Swal.fire({
          title: "Please select a status to change",
          icon: "error",
          customClass: { confirmButton: "btn btn-danger" },
          buttonsStyling: false,
        });
        return;
      }

      // AJAX Request
      $.ajax({
        type: "POST",
        url: handleErrorBtn.data("url"),
        data: JSON.stringify({
          action: action,
          selected_ids: selectedRows,
          status: action === "update_status" ? selectedStatus : undefined,
          csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
        }),
        contentType: "application/json",
        success: function (response) {
          if (response.status === 200) {
            Swal.fire({
              title: response.message,
              icon: "success",
              customClass: { confirmButton: "btn btn-primary" },
              buttonsStyling: false,
            });

            // Reset components after success
            resetComponents();

            // Reload the table
            $("#errorLogsTable").DataTable().ajax.reload(null, false);
          } else {
            Swal.fire({
              title: response.message,
              icon: "error",
              customClass: { confirmButton: "btn btn-danger" },
              buttonsStyling: false,
            });
          }
        },
        error: function (xhr, status, error) {
          console.error("Error:", error);
          Swal.fire({
            title: "An error occurred. Please try again later.",
            icon: "error",
            customClass: { confirmButton: "btn btn-danger" },
            buttonsStyling: false,
          });
        },
      });
    });
  })();

  // Fetch Error Logs data
  function fetchErrorLogs() {
    const logContainer = $("#log-container");
    $.ajax({
      url: logContainer.data("url"),
      type: "GET",
      dataType: "json",
      success: function (response) {
        logContainer.empty();
        response.logs.forEach((log) => {
          // Determine log severity
          let logClass = "";
          if (log.includes("WARNING")) {
            logClass = "log-warning";
          } else if (log.includes("ERROR")) {
            logClass = "log-error";
          } else if (log.includes("CRITICAL")) {
            logClass = "log-critical";
          } else {
            logClass = "log-info"; // Default style for other levels
          }

          // Append log with corresponding class
          logContainer.append(`<div class="${logClass}">${log}</div>`);
        });
      },
      error: function (xhr, status, error) {
        console.error("Error fetching logs:", error);
        $("#log-container").html(
          "<div class='text-danger'>Error loading logs.</div>"
        );
      },
    });
  }
  // Fetch logs every 5 seconds
  if (window.location.pathname === '/en/app-error-report/' || window.location.pathname === '/app-error-report') {
    setInterval(fetchErrorLogs, 5000);
  }

  // Fetch logs on page load
  fetchErrorLogs();

  // Tour
  (function () {
    // Select the Tour Buttons
    const transactionTourBtn = $('#transactionTourBtn');
    const bankAcTourBtn = $("#bankAcTourBtn");

    // Define button classes
    const BACK_BTN_CLASS = 'btn btn-sm btn-outline-primary';
    const NEXT_BTN_CLASS = 'btn btn-sm btn-primary btn-next';

    function parseCSV(csvUrl) {
      return new Promise((resolve, reject) => {
        if (!csvUrl) {
          console.error('CSV URL is not provided.');
          reject('CSV URL is not provided.');
          return;
        }

        Papa.parse(csvUrl, {
          download: true,
          header: true,
          skipEmptyLines: true,
          transform: function (value, key) {
            if (key === "Step") {
              return value.replace(/\s+/g, '-'); // Replace spaces with hyphens
            }
            return value;
          },
          complete: function (results) {
            if (!results.data || !Array.isArray(results.data) || results.data.length === 0) {
              console.warn('No data found in CSV.');
              reject('No data found in CSV.');
              return;
            }

            resolve(results.data);
          },
          error: function (err) {
            console.error("Error parsing the CSV:", err);
            reject(err);
          }
        });
      });
    }

    function initializeTour() {
      const tour = new Shepherd.Tour({
        defaultStepOptions: {
          classes: 'shadow-md bg-purple-dark',
          scrollTo: true,
          cancelIcon: {
            enabled: true
          }
        },
        useModalOverlay: true
      });

      return tour;
    }

    // Define button configurations
    const buttonsConfig = {
      skip: {
        text: 'Skip',
        classes: BACK_BTN_CLASS,
        action: function (tour) {
          tour.cancel();
        }
      },
      back: {
        text: 'Back',
        classes: BACK_BTN_CLASS,
        action: function (tour) {
          tour.back();
        }
      },
      next: {
        text: 'Next',
        classes: NEXT_BTN_CLASS,
        action: function (tour) {
          tour.next();
        }
      },
      finish: {
        text: 'Finish',
        classes: NEXT_BTN_CLASS,
        action: function (tour) {
          tour.complete();
        }
      }
    };

    function truncateTitle(title) {
      if (title.length > 32) {
        return title.substring(0, 32) + '...';
      } else {
        return title;
      }
    }

    function addTourStep(tour, stepData, position, buttons) {

      tour.addStep({
        id: stepData.Step,
        title: truncateTitle(stepData.Title),
        text: `
        ${stepData.Tips ? `<h5 style="font-weight: bold; color: #7367F0">Tips:</h5>
        <p>${stepData.Tips}</p>` : ''}
        ${stepData["Example Task"] ? `<h5 style="font-weight: bold; color: #7367F0">Example Task:</h5>
        <p>${stepData["Example Task"]}</p>` : ''}
      `,
        attachTo: {
          element: `.${stepData.Step || 'content'}`,
          on: position
        },
        buttons: buttons.map(button => ({
          text: button.text,
          classes: button.classes,
          action: () => button.action(tour)
        })),
        scrollTo: true,
        scrollToHandler: (element) => {
          const headerOffset = 100; // Adjust based on sticky navbar
          const elementPosition = element.getBoundingClientRect().top + window.scrollY;
          const offsetPosition = elementPosition - headerOffset;

          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });
        },
      });
    }

    function configureBankAccountTour(tour, data) {
      data.forEach((stepData, index) => {
        let position = 'bottom';

        let buttons = [];
        if (index === 0) {
          // First step: Skip and Next
          buttons.push(buttonsConfig.skip, buttonsConfig.next);

        } else if (index === data.length - 1) {
          // Last step: Back and Finish
          buttons.push(buttonsConfig.back, buttonsConfig.finish);
        } else {
          // Middle steps: Back and Next
          buttons.push(buttonsConfig.back, buttonsConfig.next);
        }


        if (index < 3) position = 'right';
        if (index > 5) position = 'top';

        addTourStep(tour, stepData, position, buttons);
      });

      return tour;
    }

    function configureBillAndSubTour(tour, data) {
      data.forEach((stepData, index) => {
        let position = "right";
        let buttons = [];
        if (index === 0) {
          // First step: Skip and Next
          buttons.push(buttonsConfig.skip, buttonsConfig.next);

        } else if (index === data.length - 1) {
          // Last step: Back and Finish
          buttons.push(buttonsConfig.back, buttonsConfig.finish);
        } else {
          // Middle steps: Back and Next
          buttons.push(buttonsConfig.back, buttonsConfig.next);
        }

        if (index == 2) position = "top";

        addTourStep(tour, stepData, position, buttons);
      })
      return tour;
    }

    function configureTransactionTour(tour, data) {
      data.forEach((stepData, index) => {
        let position = 'right';

        let buttons = [];
        if (index === 0) {
          // First step: Skip and Next
          buttons.push(buttonsConfig.skip, buttonsConfig.next);
        } else if (index === data.length - 1) {
          // Last step: Back and Finish
          buttons.push(buttonsConfig.back, buttonsConfig.finish);
        } else {
          // Middle steps: Back and Next
          buttons.push(buttonsConfig.back, buttonsConfig.next);
        }
        // Customize position based on step index
        if (index === 4 || index === 8) {
          position = 'bottom';
        }
        if (index === 5 || index === 7) {
          position = 'left';
        }
        addTourStep(tour, stepData, position, buttons);
      });

      return tour;
    }

    function configureSampleBudgetTour(tour, data) {
      data.forEach((stepData, index) => {
        let position = 'bottom';

        let buttons = [];
        if (index === 0) {
          // First step: Skip and Next
          buttons.push(buttonsConfig.skip, buttonsConfig.next);
        } else if (index === data.length - 1) {
          // Last step: Back and Finish
          buttons.push(buttonsConfig.back, buttonsConfig.finish);
        } else {
          // Middle steps: Back and Next
          buttons.push(buttonsConfig.back, buttonsConfig.next);
        }
        // Customize position based on step index
        if (index == 1) position = "right";
        if (index == 4 || index == 5) position = "top";
        addTourStep(tour, stepData, position, buttons);
      });

      return tour;
    }

    function configureDashboardTour(tour, data) {
      data.forEach((stepData, index) => {
        let position = 'top';

        let buttons = [];
        if (index === 0) {
          // First step: Skip and Next
          buttons.push(buttonsConfig.skip, buttonsConfig.next);
        } else if (index === data.length - 1) {
          // Last step: Back and Finish
          buttons.push(buttonsConfig.back, buttonsConfig.finish);
        } else {
          // Middle steps: Back and Next
          buttons.push(buttonsConfig.back, buttonsConfig.next);
        }
        // Customize position based on step index
        if (index == 1) position = "right";
        if (index == 4 || index == 5) position = "top";
        addTourStep(tour, stepData, position, buttons);
      });
      return tour;
    }

    function configureMortgageCalculatorTour(tour, data) {
      data.forEach((stepData, index) => {
        let position = 'bottom';

        let buttons = [];
        if (index === 0) {
          // First step: Skip and Next
          buttons.push(buttonsConfig.skip, buttonsConfig.next);
          position = 'right';
        } else if (index === data.length - 1) {
          // Last step: Back and Finish
          buttons.push(buttonsConfig.back, buttonsConfig.finish);
          position = "top";
        } else {
          // Middle steps: Back and Next
          buttons.push(buttonsConfig.back, buttonsConfig.next);
        }

        if (index === 1) position = 'bottom';
        // Customize position based on step index
        addTourStep(tour, stepData, position, buttons);
      });
      return tour;
    }
    function configureGoalTour(tour, data) {
      data.forEach((stepData, index) => {
        let position = 'bottom';

        let buttons = [];
        if (index === 0) {
          // First step: Skip and Next
          buttons.push(buttonsConfig.skip, buttonsConfig.next);
          position = 'right';
        } else if (index === data.length - 1) {
          // Last step: Back and Finish
          buttons.push(buttonsConfig.back, buttonsConfig.finish);
          position = "top";
        } else {
          // Middle steps: Back and Next
          buttons.push(buttonsConfig.back, buttonsConfig.next);
        }

        if (index === 1) position = 'bottom';
        // Customize position based on step index
        addTourStep(tour, stepData, position, buttons);
      });
      return tour;
    }
    function configureCompareTargetBudgetTour(tour, data) {
      data.forEach((stepData, index) => {
        let position = 'bottom';

        let buttons = [];
        if (index === 0) {
          // First step: Skip and Next
          buttons.push(buttonsConfig.skip, buttonsConfig.next);
          position = 'right';
        } else if (index === data.length - 1) {
          // Last step: Back and Finish
          buttons.push(buttonsConfig.back, buttonsConfig.finish);
          position = "top";
        } else {
          // Middle steps: Back and Next
          buttons.push(buttonsConfig.back, buttonsConfig.next);
        }

        if (index === 1) position = 'bottom';
        // Customize position based on step index
        addTourStep(tour, stepData, position, buttons);
      });
      return tour;
    }
    function configureCompareBudgetTour(tour, data) {
      data.forEach((stepData, index) => {
        let position = 'bottom';

        let buttons = [];
        if (index === 0) {
          // First step: Skip and Next
          buttons.push(buttonsConfig.skip, buttonsConfig.next);
          position = 'right';
        } else if (index === data.length - 1) {
          // Last step: Back and Finish
          buttons.push(buttonsConfig.back, buttonsConfig.finish);
          position = "top";
        } else {
          // Middle steps: Back and Next
          buttons.push(buttonsConfig.back, buttonsConfig.next);
        }

        if (index === 1) position = 'bottom';
        // Customize position based on step index
        addTourStep(tour, stepData, position, buttons);
      });
      return tour;
    }
    function configureBudgetTour(tour, data) {
      data.forEach((stepData, index) => {
        let position = 'bottom';

        let buttons = [];
        if (index === 0) {
          // First step: Skip and Next
          buttons.push(buttonsConfig.skip, buttonsConfig.next);
          position = 'right';
        } else if (index === data.length - 1) {
          // Last step: Back and Finish
          buttons.push(buttonsConfig.back, buttonsConfig.finish);
          position = "top";
        } else {
          // Middle steps: Back and Next
          buttons.push(buttonsConfig.back, buttonsConfig.next);
        }

        if (index === 1) position = 'bottom';
        // Customize position based on step index
        addTourStep(tour, stepData, position, buttons);
      });
      return tour;
    }
    function configureCategoryTour(tour, data) {
      data.forEach((stepData, index) => {
        let position = 'bottom';

        let buttons = [];
        if (index === 0) {
          // First step: Skip and Next
          buttons.push(buttonsConfig.skip, buttonsConfig.next);
          position = 'right';
        } else if (index === data.length - 1) {
          // Last step: Back and Finish
          buttons.push(buttonsConfig.back, buttonsConfig.finish);
          position = "top";
        } else {
          // Middle steps: Back and Next
          buttons.push(buttonsConfig.back, buttonsConfig.next);
        }

        if (index === 1) position = 'bottom';
        // Customize position based on step index
        addTourStep(tour, stepData, position, buttons);
      });
      return tour;
    }


    // Attach event handler
    transactionTourBtn.click(async function () {
      const csvUrl = transactionTourBtn.data('csv');
      try {
        const data = await parseCSV(csvUrl);
        const tour = initializeTour();
        configureTransactionTour(tour, data).start();
      } catch (error) {
        console.error("Failed to start transaction tour:", error);
      }
    });

    bankAcTourBtn.click(async function () {
      const csvUrl = bankAcTourBtn.data('csv');
      try {
        const data = await parseCSV(csvUrl);
        const tour = initializeTour();
        configureBankAccountTour(tour, data).start();
      } catch (error) {
        console.error("Failed to start bank account tour:", error);
      }
    });

    $("#billAndSubsTourBtn").click(async function () {
      const csvUrl = $("#billAndSubsTourBtn").data('csv');
      try {
        const data = await parseCSV(csvUrl);
        const tour = initializeTour();
        configureBillAndSubTour(tour, data).start();
      } catch (error) {
        console.error("Failed to start bill and subs tour:", error);
      }
    });

    $("#sampleBudgetTourBtn").click(async function () {
      const csvUrl = $("#sampleBudgetTourBtn").data('csv');
      try {
        const data = await parseCSV(csvUrl);
        const tour = initializeTour();
        configureSampleBudgetTour(tour, data).start();
      } catch (error) {
        console.error("Failed to start bill and subs tour:", error);
      }
    });

    $("#dashboardTourBtn").click(async function () {
      const csvUrl = $("#dashboardTourBtn").data('csv');
      try {
        const data = await parseCSV(csvUrl);
        const tour = initializeTour();
        configureDashboardTour(tour, data).start();
      } catch (error) {
        console.error("Failed to start bill and subs tour:", error);
      }
    });

    $("#mortgageCalculatorTourBtn").click(async function () {
      const csvUrl = $("#mortgageCalculatorTourBtn").data('csv');
      try {
        const data = await parseCSV(csvUrl);
        const tour = initializeTour();
        configureMortgageCalculatorTour(tour, data).start();
      } catch (error) {
        console.error("Failed to start bill and subs tour:", error);
      }
    });

    $("#goalTourBtn").click(async function () {
      const csvUrl = $("#goalTourBtn").data('csv');
      try {
        const data = await parseCSV(csvUrl);
        const tour = initializeTour();
        configureGoalTour(tour, data).start();
      } catch (error) {
        console.error("Failed to start bill and subs tour:", error);
      }
    });
    $("#compareTargetBudgetBtn").click(async function () {
      const csvUrl = $("#compareTargetBudgetBtn").data('csv');
      try {
        const data = await parseCSV(csvUrl);
        const tour = initializeTour();
        configureCompareTargetBudgetTour(tour, data).start();
      } catch (error) {
        console.error("Failed to start bill and subs tour:", error);
      }
    });
    $("#compareBudgetTourBtn").click(async function () {
      const csvUrl = $("#compareBudgetTourBtn").data('csv');
      try {
        const data = await parseCSV(csvUrl);
        const tour = initializeTour();
        configureCompareBudgetTour(tour, data).start();
      } catch (error) {
        console.error("Failed to start bill and subs tour:", error);
      }
    });
    $("#budgetTourBtn").click(async function () {
      const csvUrl = $("#budgetTourBtn").data('csv');
      try {
        const data = await parseCSV(csvUrl);
        const tour = initializeTour();
        configureBudgetTour(tour, data).start();
      } catch (error) {
        console.error("Failed to start bill and subs tour:", error);
      }
    });
    $("#categoryTourBtn").click(async function () {
      const csvUrl = $("#categoryTourBtn").data('csv');
      try {
        const data = await parseCSV(csvUrl);
        const tour = initializeTour();
        configureCategoryTour(tour, data).start();
      } catch (error) {
        console.error("Failed to start bill and subs tour:", error);
      }
    });

  })();

  var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
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
