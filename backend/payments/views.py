from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCustomer

from .cards import card_token
from .models import PaymentToken
from .serializers import MockPaymentSerializer


@method_decorator(sensitive_post_parameters("card_number", "cvv"), name="dispatch")
class MockPaymentView(APIView):
    """Simulated bank: validates the card and always approves.

    The CVV is validated and then discarded; the card number is reduced to
    its last four digits and a hash before anything is stored.
    """

    permission_classes = [IsCustomer]

    @method_decorator(sensitive_variables("serializer", "card_number"))
    def post(self, request):
        serializer = MockPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card_number = serializer.validated_data["card_number"]

        payment_token, _ = PaymentToken.objects.get_or_create(
            user=request.user,
            token=card_token(card_number),
            defaults={"last4": card_number[-4:]},
        )
        return Response(
            {
                "status": "approved",
                "payment_token": payment_token.token,
                "last4": payment_token.last4,
            },
            status=status.HTTP_201_CREATED,
        )
