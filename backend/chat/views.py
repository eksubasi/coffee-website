from django.core import signing
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User

from .models import Conversation
from .services import can_access, guest_key


@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"csrf_token": get_token(request)})


class ConversationCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if request.user.is_authenticated:
            if request.user.role != User.Role.CUSTOMER:
                raise PermissionDenied("Only customers can start a conversation.")

            conversation = Conversation.objects.create(user=request.user)
        else:
            SessionAuthentication().enforce_csrf(request)

            if not request.session.session_key:
                request.session.create()

            conversation = Conversation.objects.create(
                guest_key=guest_key(request.session),
            )

        return Response({"id": str(conversation.pk)}, status=201)


class ConversationTicketView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        if not request.user.is_authenticated:
            SessionAuthentication().enforce_csrf(request)

        conversation = get_object_or_404(Conversation, pk=pk)
        key = guest_key(request.session)

        if not can_access(conversation, request.user, key):
            raise PermissionDenied("You cannot access this conversation.")

        payload = {
            "conversation_id": str(conversation.pk),
            "user_id": (
                request.user.pk if request.user.is_authenticated else None
            ),
            "guest_key": key if not request.user.is_authenticated else "",
        }

        ticket = signing.dumps(payload, salt="chat.websocket")
        return Response(
            {
                "ticket": ticket,
                "expires_in": 60,
                "ws_path": f"/ws/support/{conversation.pk}/",
            },
            headers={"Cache-Control": "no-store"},
        )