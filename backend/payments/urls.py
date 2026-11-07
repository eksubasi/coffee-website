from django.urls import path

from . import views

urlpatterns = [
    path("mock", views.MockPaymentView.as_view(), name="payments-mock"),
]
