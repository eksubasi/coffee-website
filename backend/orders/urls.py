from django.urls import path

from . import views

urlpatterns = [
    path("orders", views.CustomerOrderListView.as_view(), name="order-list"),
    path("orders/<int:pk>", views.CustomerOrderDetailView.as_view(), name="order-detail"),
    path("deliveries", views.DeliveryListView.as_view(), name="delivery-list"),
    path(
        "deliveries/<int:pk>/complete",
        views.DeliveryCompleteView.as_view(),
        name="delivery-complete",
    ),
    path("orders/<int:pk>/status", views.OrderStatusView.as_view(), name="order-status"),
]
