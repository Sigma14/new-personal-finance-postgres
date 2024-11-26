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
  { button: aiChatButton, content: aiChatContent },
  { button: feedbackButton, content: feedbackContent },
  { button: notesButton, content: notesContent },
  { button: lessonsButton, content: lessonsContent },
];

// Function to activate a button and its corresponding content
const activateButton = (button, content) => {
  // Reset all buttons and content
  sidebarItems.forEach((item) => {
    item.content.setAttribute("data-visible", "false");
    item.button.classList.remove("btn-primary");
    item.button.classList.add("btn-outline-secondary");
    item.button.setAttribute("aria-expanded", "false");
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
      console.log(response);
      response.forEach((data) => {
        renderAccordion(data);
      });
    },
  });
});
