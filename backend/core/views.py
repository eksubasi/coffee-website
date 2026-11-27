from django.db import DatabaseError, connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def database_is_reachable() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return False
    return True


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    reachable = database_is_reachable()

    return Response(
        {
            "status": "ok" if reachable else "unavailable",
            "db": reachable,
        },
        status=200 if reachable else 503,
    )
