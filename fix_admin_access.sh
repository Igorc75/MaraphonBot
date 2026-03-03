#!/bin/bash

echo "Исправляем проверки прав администратора..."

# 1. topic_add.py
sed -i 's/if update.effective_chat.type != "private" or update.effective_user.id not in Config.ADMIN_IDS:/if update.effective_chat.type != "private":\n    if not await is_chat_admin(update, context):/g' admin/topic_add.py
sed -i '/^from .keyboards import/a from admin.auth import is_chat_admin' admin/topic_add.py

# 2. topics_list.py
sed -i 's/if update.effective_chat.type != "private" or update.effective_user.id not in Config.ADMIN_IDS:/if update.effective_chat.type != "private":\n    if not await is_chat_admin(update, context):/g' admin/topics_list.py
sed -i '/^from .keyboards import/a from admin.auth import is_chat_admin' admin/topics_list.py

# 3. topic_delete.py
sed -i 's/if update.effective_chat.type != "private" or update.effective_user.id not in Config.ADMIN_IDS:/if update.effective_chat.type != "private":\n    if not await is_chat_admin(update, context):/g' admin/topic_delete.py
sed -i '/^from .keyboards import/a from admin.auth import is_chat_admin' admin/topic_delete.py

# 4. topic_edit.py
sed -i 's/if update.effective_chat.type != "private" or update.effective_user.id not in Config.ADMIN_IDS:/if update.effective_chat.type != "private":\n    if not await is_chat_admin(update, context):/g' admin/topic_edit.py
sed -i 's/if update.effective_user.id not in Config.ADMIN_IDS:/if not await is_chat_admin(update, context):/g' admin/topic_edit.py
sed -i '/^from .keyboards import/a from admin.auth import is_chat_admin' admin/topic_edit.py

# 5. stats.py
sed -i 's/if update.effective_chat.type != "private" or update.effective_user.id not in Config.ADMIN_IDS:/if update.effective_chat.type != "private":\n    if not await is_chat_admin(update, context):/g' admin/stats.py
sed -i '/^from .keyboards import/a from admin.auth import is_chat_admin' admin/stats.py

# 6. settings.py
sed -i 's/if update.effective_user.id not in Config.ADMIN_IDS:/if not await is_chat_admin(update, context):/g' admin/settings.py
sed -i 's/if update.effective_user.id not in Config.ADMIN_IDS or update.effective_chat.type != "private":/if update.effective_chat.type != "private":\n    if not await is_chat_admin(update, context):/g' admin/settings.py
sed -i '/^from .keyboards import/a from admin.auth import is_chat_admin' admin/settings.py

# 7. admin_manager.py
sed -i 's/if update.effective_user.id not in Config.ADMIN_IDS:/if not await is_chat_admin(update, context):/g' admin/admin_manager.py
sed -i '/^from .keyboards import/a from admin.auth import is_chat_admin' admin/admin_manager.py

echo "✅ Готово! Теперь перезапустите бота: sudo systemctl restart maraphonbot.service"