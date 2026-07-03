from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    # Admin Action APIs
    path('admin/orders/update-status/', views.update_order_status, name='update_order_status'),
    path('admin/menu/toggle-availability/', views.toggle_menu_availability, name='toggle_menu_availability'),
    path('admin/menu/update-price/', views.update_menu_price, name='update_menu_price'),
    path('admin/menu/add-item/', views.add_menu_item, name='add_menu_item'),
    path('admin/menu/edit-item/', views.edit_menu_item, name='edit_menu_item'),
    path('test-add/', views.test_add, name='test_add'),
    # Regular URLs
    path('menu/', views.menu_items, name='menu_items'),
    path('cart/', views.cart, name='cart'),
    path('order/', views.order, name='order'),
    path('signup/', views.signup, name='signup'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user/orders/', views.user_orders, name='user_orders'),
]
