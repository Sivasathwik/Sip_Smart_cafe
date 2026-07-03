from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import *

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active', 'phone')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'first_name', 'last_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'phone', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

# Cart Admin
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'quantity', 'created_at')
    list_filter = ('created_at', 'item')
    search_fields = ('user__email', 'user__username', 'item__name')
    
# Order Admin  
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_price', 'order_type', 'payment_method', 'payment_status', 'status', 'created_at')
    list_filter = ('status', 'order_type', 'payment_method', 'payment_status', 'created_at')
    search_fields = ('user__email', 'user__username')
    
# OrderItem Admin
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'get_total_price')
    list_filter = ('item', 'order__created_at')
    search_fields = ('order__user__email', 'item__name')
    
    def get_total_price(self, obj):
        return obj.quantity * obj.item.price
    get_total_price.short_description = 'Total Price'

# MenuItem Admin
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'availability', 'added_by', 'image_preview', 'created_at')
    list_filter = ('availability', 'added_by', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'availability')
    fields = None  # Use fieldsets instead
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'availability')
        }),
        ('Images', {
            'fields': ('image', 'image_url', 'image_large_preview'),
            'description': 'Upload an image file OR provide an image URL'
        }),
        ('Management', {
            'fields': ('added_by',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('image_preview', 'image_large_preview', 'created_at', 'updated_at')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        elif obj.image_url:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image_url)
        else:
            return "No Image"
    image_preview.short_description = 'Image Preview'
    
    def image_large_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 200px;" />', obj.image.url)
        elif obj.image_url:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 200px;" />', obj.image_url)
        else:
            return "No Image Available"
    image_large_preview.short_description = 'Full Image Preview'
    
    def save_model(self, request, obj, form, change):
        if not obj.added_by:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)

# Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
