function updateUnreadCount() {
  const unreadCount = notifications.filter(n => !n.read).length;
  const badge = document.querySelector('.notification-badge');
  if (badge) {
    badge.textContent = unreadCount;
    badge.style.display = unreadCount > 0 ? 'flex' : 'none';
  }
}

function toggleDropdown() {
  const dropdown = document.querySelector('.notification-dropdown');
  dropdown.classList.toggle('open');
  // Убираем обновление счетчика при открытии/закрытии
}

function markAsRead(notification) {
  if (!notification.read) {
    notification.read = true;
    saveNotifications();
    updateUnreadCount();
  }
}

function markAllAsRead() {
  notifications.forEach(n => n.read = true);
  saveNotifications();
  updateUnreadCount();
}

// Обработчик клика вне дропдауна
document.addEventListener('click', function(event) {
  const dropdown = document.querySelector('.notification-dropdown');
  const bell = document.querySelector('.notification-bell');
  
  if (dropdown && dropdown.classList.contains('open') && 
      !dropdown.contains(event.target) && 
      !bell.contains(event.target)) {
    dropdown.classList.remove('open');
  }
}); 