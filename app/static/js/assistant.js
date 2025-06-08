// Получаем элементы DOM
const assistantButtonElement = document.querySelector("#assistant-button");
const assistantPanel = document.querySelector(".assistant-panel");
const newChatButton = document.getElementById("new-chat-button");
const chatList = document.querySelector(".chat-list");

const messagesContainer = document.querySelector(".messages-container");
const messagesDiv = messagesContainer.querySelector(".messages");
const chatInput = document.querySelector(".chat-input textarea");
const sendButton = document.getElementById("send-button");
const messageLoadingIndicator = messagesContainer.querySelector(".message-loading-indicator");

let currentChatId = null;
let isAssistantResponding = false;
let activeThinkingChatId = null;

// Глобальный список чатов
let chatsCache = [];

// Кастомный tooltip для названия чата
let chatTooltip = null;
function showChatTooltip(target, text) {
  if (!chatTooltip) {
    chatTooltip = document.createElement('div');
    chatTooltip.className = 'custom-tooltip';
    chatTooltip.appendChild(document.createTextNode(''));
    const arrow = document.createElement('div');
    arrow.className = 'custom-tooltip-arrow';
    chatTooltip.appendChild(arrow);
    document.body.appendChild(chatTooltip);
  }
  chatTooltip.childNodes[0].nodeValue = text;
  chatTooltip.classList.add('visible');
  // Позиционируем tooltip по центру и выше над элементом
  const rect = target.getBoundingClientRect();
  chatTooltip.style.left = (rect.left + rect.width / 2 + window.scrollX) + 'px';
  chatTooltip.style.top = (rect.top + window.scrollY - 32) + 'px';
}
function hideChatTooltip() {
  if (chatTooltip) {
    chatTooltip.classList.remove('visible');
  }
}
document.addEventListener('mouseover', function(e) {
  if (e.target.classList.contains('chat-item-title')) {
    showChatTooltip(e.target, e.target.textContent);
  }
});
document.addEventListener('mouseout', function(e) {
  if (e.target.classList.contains('chat-item-title')) {
    hideChatTooltip();
  }
});

// Функция отображения сообщения
function displayMessage(content, role) {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${role}`;
  
  const roleLabel = document.createElement("div");
  roleLabel.className = "message-role";
  roleLabel.textContent = role === "user" ? "Вы" : "Ассистент";
  
  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";
  contentDiv.innerHTML = content;
  
  messageDiv.appendChild(roleLabel);
  messageDiv.appendChild(contentDiv);
  messagesDiv.appendChild(messageDiv);
  
  // Прокрутка к последнему сообщению
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Загрузка списка чатов
async function loadChats() {
  try {
    const response = await fetch('/assistant/chats');
    const data = await response.json();
    chatsCache = data.chats;
    chatList.innerHTML = '';
    data.chats.forEach(chat => {
      chatList.appendChild(createChatElement(chat));
    });
  } catch (error) {
    console.error('Error loading chats:', error);
  }
}

// Обновление заголовка чата из локального списка
function updateChatTitleFromCache(chatId) {
  const chat = chatsCache.find(c => c.id === chatId);
  document.getElementById('current-chat-title').textContent = chat ? chat.name : 'Новый чат';
}

// Модальное окно для переименования чата
function showRenameChatModal(event, chatId, oldName) {
  event.stopPropagation();
  const modal = document.createElement("div");
  modal.className = "delete-confirmation-modal";
  modal.innerHTML = `
    <div class="delete-confirmation-content">
      <h3>Переименовать чат</h3>
      <input type="text" class="rename-chat-input" value="${oldName}" maxlength="50" style="width:100%;margin-bottom:16px;padding:8px;border-radius:6px;border:1px solid #444;background:#222;color:#fff;" />
      <div class="delete-confirmation-buttons">
        <button class="cancel-button">Отмена</button>
        <button class="delete-button">Переименовать</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  const input = modal.querySelector('.rename-chat-input');
  input.focus();
  input.select();
  modal.querySelector('.cancel-button').onclick = () => modal.remove();
  modal.querySelector('.delete-button').onclick = async () => {
    const newName = input.value.trim();
    if (newName && newName !== oldName) {
      await renameChat(null, chatId, newName);
    }
    modal.remove();
  };
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      modal.querySelector('.delete-button').click();
    }
    if (e.key === 'Escape') {
      modal.remove();
    }
  });
  modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
}

// Функции для показа/скрытия индикатора загрузки
function showLoadingIndicator() {
  messageLoadingIndicator.style.display = "block";
}
function hideLoadingIndicator() {
  messageLoadingIndicator.style.display = "none";
}

async function handleSendMessage() {
  const text = chatInput.value.trim();
  if (text === "" || isAssistantResponding) return;

  let context = null;
  const path = window.location.pathname;
  if (/^\/theory\/\d+/.test(path) || /^\/theory\/edit\/\d+/.test(path) || /^\/theory\/create\/\d+/.test(path)) {
    // Находим глобальную переменную delta, если есть (theory.html)
    if (typeof delta !== "undefined") {
      try {
        context = JSON.stringify(delta); // отправляем как строку
      } catch (e) {
        context = null;
      }
    }
    // На edit-странице можно забрать через quill.getContents()
    if (typeof quill !== "undefined") {
      try {
        context = JSON.stringify(quill.getContents());
      } catch (e) {
        context = null;
      }
    }
  }

  if (!currentChatId) {
    try {
      const response = await fetch('/assistant/chats/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: text.substring(0, 30) + '...' })
      });
      const data = await response.json();
      currentChatId = data.id;
      await loadChats();
      updateChatTitleFromCache(currentChatId);
    } catch (error) {
      console.error('Error creating chat:', error);
      return;
    }
  }

  isAssistantResponding = true;
  sendButton.classList.add("disabled");
  chatInput.disabled = true;
  activeThinkingChatId = currentChatId;
  showLoadingIndicator();

  chatInput.value = "";

  try {
    // Сохраняем сообщение пользователя в базе
    await fetch(`/assistant/save_message/${currentChatId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: text }),
    });

    // После сохранения — сразу перезагружаем историю (покажет и новое сообщение)
    await loadChatHistory(currentChatId);

    const payload = { prompt: text };
    if (context) payload.context = context;

    const response = await fetch(`/assistant/ask/${currentChatId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    // После ответа ассистента — снова перезагружаем историю (покажет и ответ)
    await loadChatHistory(currentChatId);

    if (!response.ok) {
      const errorData = await response.json();
      displayMessage(`Ошибка ассистента: ${errorData.error}`, "system-info");
    }
  } catch (error) {
    console.error("Error:", error);
    displayMessage("Ошибка соединения", "system-info");
  } finally {
    isAssistantResponding = false;
    if (currentChatId === activeThinkingChatId) {
      hideLoadingIndicator();
    }
    activeThinkingChatId = null;
    sendButton.classList.remove("disabled");
    chatInput.disabled = false;
    chatInput.focus();
  }
}

// При переключении чата показываем индикатор только если ассистент думает в этом чате
async function selectChat(chatId) {
  currentChatId = chatId;
  if (activeThinkingChatId === chatId) {
    showLoadingIndicator();
  } else {
    hideLoadingIndicator();
  }
  await loadChats();
  await loadChatHistory(chatId);
  updateChatTitleFromCache(chatId);
}

// Функция для создания элемента чата
function createChatElement(chat) {
  const chatElement = document.createElement("div");
  chatElement.className = `chat-item ${currentChatId === chat.id ? 'active' : ''}`;
  chatElement.setAttribute('data-chat-id', chat.id);
  
  const titleSpan = document.createElement("span");
  titleSpan.className = "chat-item-title";
  titleSpan.textContent = chat.name;
  titleSpan.title = chat.name;
  
  const actionsDiv = document.createElement("div");
  actionsDiv.className = "chat-item-actions";
  actionsDiv.innerHTML = `
    <button class="chat-item-action" onclick="showRenameChatModal(event, ${chat.id}, '${chat.name.replace(/'/g, "&#39;")}')" title="Переименовать чат">
      <i class="fas fa-edit"></i>
    </button>
    <button class="chat-item-action" onclick="showDeleteConfirmation(event, ${chat.id})" title="Удалить чат">
      <i class="fas fa-trash"></i>
    </button>
  `;

  chatElement.appendChild(titleSpan);
  chatElement.appendChild(actionsDiv);
  chatElement.onclick = (e) => {
    if (e.target === chatElement || e.target === titleSpan) {
      selectChat(chat.id);
    }
  };
  
  return chatElement;
}

// Обработчик для открытия панели ассистента
assistantButtonElement.addEventListener("click", async () => {
  assistantPanel.classList.add("visible");
  await loadChats();
  if (currentChatId) {
    await updateChatTitleFromCache(currentChatId);
  } else {
    document.getElementById('current-chat-title').textContent = 'Новый чат';
  }
  chatInput.focus();
});

// Обработчик для закрытия панели ассистента
document.querySelector('.close-button').addEventListener('click', () => {
  assistantPanel.classList.remove('visible');
});

// Закрытие по клику вне окна
assistantPanel.addEventListener("click", (e) => {
  if (e.target === assistantPanel) {
    assistantPanel.classList.remove("visible");
  }
});

// Обработчик для кнопки нового чата
newChatButton.onclick = async () => {
  currentChatId = null;
  document.getElementById('current-chat-title').textContent = 'Новый чат';
  messagesDiv.innerHTML = '';
  await loadChats();
  chatInput.focus();
};

// Обработчики для отправки сообщений
sendButton.addEventListener("click", handleSendMessage);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSendMessage();
  }
});

// Функция показа диалога подтверждения удаления
function showDeleteConfirmation(event, chatId) {
  event.stopPropagation();
  
  // Модальное окно удаления чата
  const modal = document.createElement("div");
  modal.className = "delete-confirmation-modal";
  modal.innerHTML = `
    <div class="delete-confirmation-content">
      <p>Удалить чат?</p>
      <div class="delete-confirmation-buttons">
        <button class="cancel-button">Отмена</button>
        <button class="delete-button">Удалить</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // Обработчики кнопок
  const cancelButton = modal.querySelector(".cancel-button");
  const deleteButton = modal.querySelector(".delete-button");
  
  cancelButton.onclick = () => {
    modal.remove();
  };
  
  deleteButton.onclick = async () => {
    await deleteChat(event, chatId);
    modal.remove();
  };
  
  // Закрытие по клику вне окна
  modal.onclick = (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  };
}

// Функция удаления чата
async function deleteChat(event, chatId) {
  event.stopPropagation();
  try {
    await fetch(`/assistant/chats/${chatId}`, { method: 'DELETE' });
    if (currentChatId === chatId) {
      currentChatId = null;
      messagesDiv.innerHTML = '';
      document.getElementById('current-chat-title').textContent = 'Новый чат';
    }
    await loadChats();
  } catch (error) {
    console.error('Error deleting chat:', error);
  }
}

// После переименования чата
async function renameChat(event, chatId, newName) {
  if (event) event.stopPropagation();
  try {
    const response = await fetch(`/assistant/chats/${chatId}/rename`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName })
    });
    await loadChats();
    updateChatTitleFromCache(chatId);
  } catch (error) {
    console.error('Error renaming chat:', error);
  }
}

// Модифицированная функция загрузки истории чата
async function loadChatHistory(chatId = currentChatId) {
  if (!chatId) {
    messagesDiv.innerHTML = '';
    document.getElementById('current-chat-title').textContent = 'Новый чат';
    return;
  }
  
  messagesDiv.innerHTML = '';
  try {
    const response = await fetch(`/assistant/history/${chatId}`);
    if (!response.ok) {
      console.error("Failed to load chat history:", response.statusText);
      displayMessage(`Ошибка: ${response.statusText}`, "system-info");
      return;
    }
    const data = await response.json();
    if (data.history && data.history.length > 0) {
      data.history.forEach((msg) => {
        displayMessage(msg.content, (msg.role === 'user' || msg.role === 'human') ? 'user' : msg.role);
      });
    }
  } catch (error) {
    console.error("Error fetching chat history:", error);
    displayMessage(`Ошибка`, "system-info");
  }
}