// Sidebar buttons
const settingButton = document.querySelector("#rightSettingsButton");
const sidebarBody = document.querySelector("#rightSettingBody");
const closeButton = document.querySelector("#closeSidebar");
const chatContainer = document.querySelector("#aiChatContainer");

// Sidebar buttons
const aiChatButton = document.querySelector("#aiChatButton");
const feedbackButton = document.querySelector("#feedbackButton");
const notesButton = document.querySelector("#notesButton");
const lessonsButton = document.querySelector("#lessonsButton");

// Sidebar content areas
const aiChatContent = document.querySelector("#aiChatContent");
const feedbackContent = document.querySelector("#feedbackContent");
const notesContent = document.querySelector("#notesContent");
const lessonsContent = document.querySelector("#lessonsContent");

// Sidebar options and their content
const sidebarItems = [
  {
    button: aiChatButton,
    content: aiChatContent,
    header: "AI Chat",
    description: "Start a conversation with AI",
  },
  {
    button: feedbackButton,
    content: feedbackContent,
    header: "Feedback",
    description: "Give feedback or report an issue",
  },
  {
    button: notesButton,
    content: notesContent,
    header: "Notes",
    description: "Take a quick notes",
  },
  {
    button: lessonsButton,
    content: lessonsContent,
    header: "Interactive Lessons",
    description: "Page interactive lessons",
  },
];

// Function to activate a button and its corresponding content
const activateButton = (button, content) => {
  // Reset all buttons and content
  sidebarItems.forEach((item) => {
    item.content.setAttribute("data-visible", "false");
    item.button.classList.remove("btn-primary");
    item.button.classList.add("btn-outline-secondary");
    item.button.setAttribute("aria-expanded", "false");
    // set heading
    if (item.button === button) {
      $("#rightSidebarHeader").text(item.header);
      $("#rightSidebarDescription").text(item.description);
    }
  });

  // Set the clicked button and content as active
  button.classList.remove("btn-outline-secondary");
  button.classList.add("btn-primary");
  button.setAttribute("aria-expanded", "true");
  content.setAttribute("data-visible", "true");
};

// Add click event listeners to the buttons
sidebarItems.forEach(({ button, content }) => {
  button.addEventListener("click", () => {
    activateButton(button, content);
  });
});

// Open the sidebar when the settings button is clicked
settingButton.addEventListener("click", () => {
  const visibility = sidebarBody.getAttribute("data-visible");
  if (visibility === "false") {
    sidebarBody.setAttribute("data-visible", "true");
    settingButton.setAttribute("aria-expanded", "true");

    // Activate AI Chat by default when opening the sidebar
    activateButton(aiChatButton, aiChatContent);
  }
});

// Close the sidebar when the close button is clicked
closeButton.addEventListener("click", () => {
  const visibility = sidebarBody.getAttribute("data-visible");
  if (visibility === "true") {
    sidebarBody.setAttribute("data-visible", "false");
    settingButton.setAttribute("aria-expanded", "false");
  }
});

/*
 * Handle chat history.
 * Load 5 messages initially.
 * Load older messages if user scrolls.
 * Each scroll will load 5 messages.
 * Each messages contains user & AI both response.
 */

// Push user chat
const pushUserChat = (content, prepend) => {
  const chatHTML = `
        <div class="chat">
            <div class="chat-avatar">
                <span class="avatar box-shadow-1 cursor-pointer">
                    <img src="{% static 'app-assets/images/icons/vuejs.svg' %}" alt="avatar" height="36" width="36" />
                </span>
            </div>
            <div class="chat-body">
                <div class="chat-content">
                    <p>${content}</p>
                </div>
            </div>
        </div>
    `;
  if (prepend) $("#chatMsgContainer").prepend(chatHTML);
  else $("#chatMsgContainer").append(chatHTML);
};

// push ai chat
const pushAIChat = (content, prepend) => {
  const chatHTML = `
        <div class="chat chat-left">
            <div class="chat-avatar">
                <span class="avatar box-shadow-1 cursor-pointer">
                    <img src="{% static 'app-assets/images/icons/vuejs.svg' %}" alt="avatar"  height="36" width="36" />
                </span>
            </div>
            <div class="chat-body">
                <div class="chat-content">
                    <p>${content}</p>
                </div>
            </div>
        </div>`;
  if (prepend) $("#chatMsgContainer").prepend(chatHTML);
  else $("#chatMsgContainer").append(chatHTML);
};

const allChatsLoaded = () => {
  const html = `
     <p class="text-center"> No messages left</p>
    `;
  $("#chatContainer").prepend(html);
};

$(document).ready(function () {
  let page = 1; // start from page 1
  let loading = false;
  let has_more = true;

  function loadChats() {
    if (loading || !has_more) return;
    loading = true;

    // previous scroll height
    const chatContainer = $("#chatContainer");
    const previousScrollHeight = chatContainer[0].scrollHeight;

    $.ajax({
      url: `/chats/load-messages`,
      type: "GET",
      data: {
        page,
      },
      dataType: "json",
      success: function (data) {
        if (data.messages.length > 0) {
          // Prepend older messages at the top
          data.messages.forEach((msg) => {
            if (msg.ai_msg) pushAIChat(msg.ai_msg, true);
            if (msg.user_msg) pushUserChat(msg.user_msg, true);
          });

          page++; // inc page
          has_more = data.has_more;

          // stop scrolling as there's no data left
          if (!has_more) {
            $("#chatContainer").off("scroll");
            allChatsLoaded();
          }

          // Adjust scroll position to stay at the top of the previous messages
          const newScrollHeight = chatContainer[0].scrollHeight;
          const scrollDiff = newScrollHeight - previousScrollHeight;
          chatContainer.scrollTop(scrollDiff);
          loading = false;
        }
      },
      error: function () {
        loading = false;
      },
    });
  }

  // initial chat load
  loadChats();

  // Detect scroll event to load more chats
  $("#chatContainer").on("scroll", function () {
    if ($("#chatContainer").scrollTop() === 0 && !loading) {
      loadChats();
    }
  });
});

/*
 * Send message to ai through post req
 * For unsuccessfull response generate a regenerate button
 * For susscessfull response show it on chats
 */

// text area enter
$(document).ready(function () {
  $("#aiMsgInput").on("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault(); // Prevent adding a newline
      $("#sendMessageButton").click(); // Trigger the button click event
    }
  });
});

$(document).on("click", "#sendMessageButton", function (e) {
  e.preventDefault();
  const csrfmiddlewaretoken = document.querySelector(
    "[name=csrfmiddlewaretoken]"
  ).value;
  const message = $("#aiMsgInput").val();
  if (message.trim() === "") return;
  $.ajax({
    type: "post",
    url: "chats/send-message/",
    data: {
      message,
      csrfmiddlewaretoken,
    },
    dataType: "json",
    beforeSend: function () {
      pushUserChat(message, false);
      $("#aiMsgInput").val("");
      $("#chatContainer").scrollTop($("#chatContainer")[0].scrollHeight);
    },
    success: function (response) {
      // console.log(response);
      pushAIChat(response.ai_res, false);
      $("#chatContainer").scrollTop($("#chatContainer")[0].scrollHeight);
    },
  });
});

/*
 * Fetch Documentation
 */

const renderAccordion = (data) => {
  const html = `
        <div class="h-100" id="accParent-${data.number}">
            <div class="card">
                <h2 class="mb-0" id="heading-${data.number}">
                    <button 
                        class="btn btn-outline-primary btn-block text-left" 
                        type="button" 
                        data-toggle="collapse" 
                        data-target="#collapse${data.number}" 
                        aria-expanded="true" 
                        aria-controls="collapse${data.number}">
                        ${data.lesson_name}
                    </button>
                </h2>

                <div 
                    id="collapse${data.number}" 
                    class="collapse pt-1" 
                    aria-labelledby="heading-${data.number}" 
                    data-parent="#accParent-${data.number}">
                    <div class="card text-white accordion-card-body theme-scrollbar">
                        ${data.lesson_content}
                    </div>
                </div>
            </div>
        </div>
    `;

  $("#lessonsContent").append(html);
};

$(document).ready(function () {
  $.ajax({
    type: "get",
    url: "/documentation/",
    dataType: "json",
    success: function (response) {
      response.forEach((data) => {
        renderAccordion(data);
      });
    },
  });
});

/*
 * Handle feedback screenshot
 * Taking screenshot using html2canvas
 * Editing screenshot using fabric.js
 */

// Fabric.js canvas initialization
$(document).ready(function () {
  let canvas;

  // Function to initialize and set up the canvas
  function initializeCanvas(img, containerWidth, containerHeight) {
    const canvasElement = document.getElementById("snapEditCanvas");

    let canvasWidth, canvasHeight;

    if (containerWidth > 1200) {
      canvasWidth = 800;
      canvasHeight = 500;
    } else if (containerWidth > 768) {
      canvasWidth = 600;
      canvasHeight = 400;
    } else {
      canvasWidth = 400;
      canvasHeight = 300;
    }

    canvasElement.width = canvasWidth;
    canvasElement.height = canvasHeight;

    canvas = new fabric.Canvas("snapEditCanvas");

    const fabricImage = new fabric.Image(img, {
      left: 0,
      top: 0,
      selectable: false,
      scaleX: canvasWidth / img.width,
      scaleY: canvasHeight / img.height,
    });

    canvas.setWidth(canvasWidth);
    canvas.setHeight(canvasHeight);
    canvas.setBackgroundImage(fabricImage, canvas.renderAll.bind(canvas));
  }

  // Take Screenshot and Initialize Fabric.js
  $("#takeScreenshot").on("click", function () {
    html2canvas(document.body, {
      ignoreElements: function (element) {
        return element.id === "rightSettingBody";
      },
      width: window.innerWidth,
      height: window.innerHeight,
    })
      .then((snap) => {
        const imgData = snap.toDataURL("image/png");
        const img = new Image();
        img.src = imgData;

        img.onload = function () {
          const containerWidth = window.innerWidth;
          const containerHeight = window.innerHeight;
          initializeCanvas(img, containerWidth, containerHeight);
        };

        const modal = new bootstrap.Modal($("#staticBackdrop").get(0), {
          backdrop: "static",
          keyboard: false,
        });
        modal.show();
      })
      .catch((error) => {
        console.error("Error taking screenshot:", error);
      });
  });

  // Save Edited Image
  $("#saveEditedImage").on("click", function () {
    const editedImage = canvas.toDataURL({ format: "png" });

    const link = document.createElement("a");
    link.href = editedImage;
    link.download = "edited-screenshot.png";
    link.click();
  });

  // Drawing Mode
  $("#enableDrawing").on("click", function () {
    canvas.isDrawingMode = !canvas.isDrawingMode;
    if (canvas.isDrawingMode) {
      canvas.freeDrawingBrush.width = 2;
      canvas.freeDrawingBrush.color = "#ff0000";
      $(this).removeClass("btn-outline-success");
      $(this).addClass("btn-outline-danger");
    } else {
      $(this).removeClass("btn-outline-danger");
      $(this).addClass("btn-outline-success");
    }
  });


  // Clear Canvas
  $("#clearCanvas").on("click", function () {
    const objects = canvas.getObjects(); // Get all objects on the canvas
    objects.forEach((obj) => {
      if (obj !== canvas.backgroundImage) {
        canvas.remove(obj); // Remove all objects except the background image
      }
    });
    canvas.renderAll(); // Re-render the canvas
  });

});
