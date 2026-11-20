from django.urls import path

from .views import (ConversationCreateView,ConversationTicketView,csrf_token,)

urlpatterns = [
    path("support/csrf", csrf_token, name="support-csrf"),
    path(
        "support/conversations",
        ConversationCreateView.as_view(),
        name="support-create",
    ),
    path(
        "support/conversations/<uuid:pk>/ticket",
        ConversationTicketView.as_view(),
        name="support-ticket",
    ),
]