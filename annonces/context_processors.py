def moderation_access(request):
    user = getattr(request, "user", None)
    can_access_moderation = False
    unread_notifications_count = 0
    unread_messages_count = 0
    compare_count = len(request.session.get("compare_logements", [])) if hasattr(request, "session") else 0
    if user and user.is_authenticated:
        can_access_moderation = user.is_superuser or user.groups.filter(name="Mod\u00e9rateurs").exists()
        unread_notifications_count = user.notifications.filter(is_read=False).count()
        unread_messages_count = user.received_logement_messages.filter(is_read=False).count()
    return {
        "can_access_moderation": can_access_moderation,
        "unread_notifications_count": unread_notifications_count,
        "unread_messages_count": unread_messages_count,
        "compare_count": compare_count,
    }
