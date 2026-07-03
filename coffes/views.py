from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import * 
from django.shortcuts import render, redirect
import json


def make_unique_username(name, email):
    base = (name or email.split('@')[0]).strip().replace(' ', '_').lower()
    base = ''.join(ch for ch in base if ch.isalnum() or ch in '._-') or 'user'
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        counter += 1
        username = f'{base}_{counter}'
    return username

# Menu API - Updated for template and API support
@csrf_exempt
def menu_items(request):
    if request.method == 'GET':
        items = MenuItem.objects.filter(availability=True).order_by('name')
        
        # Check if it's an API request or template request
        if request.content_type == 'application/json' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            # API request - return JSON
            items_data = list(items.values())
            return JsonResponse({'menu': items_data})
        else:
            # Template request - render HTML
            context = {
                'menu_items': items,
                'user': request.user if request.user.is_authenticated else None
            }
            return render(request, 'menu.html', context)

# Cart API - Updated for better user handling
@csrf_exempt
@login_required
def cart(request):
    user = request.user
    if request.method == 'GET':
        # Handle both API and template requests
        if request.content_type == 'application/json' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            # API request - return JSON
            cart_items = Cart.objects.filter(user=user).select_related('item')
            cart_data = []
            total_price = 0
            for cart_item in cart_items:
                item_total = cart_item.quantity * cart_item.item.price
                total_price += item_total
                cart_data.append({
                    'id': cart_item.id,
                    'item_name': cart_item.item.name,
                    'item_price': float(cart_item.item.price),
                    'quantity': cart_item.quantity,
                    'total_price': float(item_total)
                })
            return JsonResponse({'cart': cart_data, 'total_price': float(total_price), 'user': user.email})
        else:
            # Template request - render HTML
            cart_items = Cart.objects.filter(user=user).select_related('item')
            total_price = sum(cart_item.quantity * cart_item.item.price for cart_item in cart_items)
            context = {
                'cart_items': cart_items,
                'total_price': total_price,
                'user': user
            }
            return render(request, 'cart.html', context)
            
    elif request.method == 'POST':
        # Handle adding items to cart
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = data.get('quantity', 1)
        else:
            # Form data
            item_id = request.POST.get('item_id')
            quantity = int(request.POST.get('quantity', 1))
            
        try:
            item = MenuItem.objects.get(id=item_id, availability=True)
            cart_item, created = Cart.objects.get_or_create(
                user=user, 
                item=item,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            if request.content_type == 'application/json':
                return JsonResponse({'success': True, 'message': f'{item.name} added to cart'})
            else:
                messages.success(request, f'{item.name} added to your cart.')
                return redirect('menu_items')
                
        except MenuItem.DoesNotExist:
            if request.content_type == 'application/json':
                return JsonResponse({'error': 'Menu item not found'}, status=404)
            else:
                return redirect('menu_items')
                
    elif request.method == 'DELETE':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        try:
            Cart.objects.filter(user=user, item_id=item_id).delete()
            return JsonResponse({'success': True, 'message': 'Item removed from cart'})
        except:
            return JsonResponse({'error': 'Failed to remove item'}, status=400)

# Order API
@csrf_exempt
@login_required
def order(request):
    user = request.user
    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = json.loads(request.body or '{}')
            order_type = data.get('order_type', 'Take Away')
            payment_method = data.get('payment_method', 'COD')
        else:
            order_type = request.POST.get('order_type', 'Take Away')
            payment_method = request.POST.get('payment_method', 'COD')

        cart_items = Cart.objects.filter(user=user).select_related('item')
        if not cart_items.exists():
            if request.content_type == 'application/json':
                return JsonResponse({'error': 'Cart is empty'}, status=400)
            messages.error(request, 'Your cart is empty.')
            return redirect('cart')

        total_price = sum([ci.item.price * ci.quantity for ci in cart_items])
        payment_status = 'Pending' if payment_method == 'COD' else 'Paid'
        order = Order.objects.create(
            user=user,
            total_price=total_price,
            order_type=order_type,
            payment_method=payment_method,
            payment_status=payment_status,
        )
        for ci in cart_items:
            OrderItem.objects.create(order=order, item=ci.item, quantity=ci.quantity)
        cart_items.delete()
        if request.content_type != 'application/json':
            messages.success(request, f'Order #{order.id} placed successfully. Payment: {order.get_payment_method_display()}.')
            return redirect('cart')
        return JsonResponse({'success': True, 'order_id': order.id})

# User Auth APIs
@csrf_exempt
def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html')
    elif request.method == 'POST':
        # Check if it's JSON data (API) or form data (template)
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            full_name = (data.get('username') or '').strip()
            password = data.get('password')
            email = (data.get('email') or '').strip().lower()
            phone = data.get('phone')
            account_type = data.get('account_type', 'user')
            is_admin = data.get('is_admin', False) or account_type == 'admin'
        else:
            # Form data from template
            full_name = (request.POST.get('fullname') or '').strip()
            email = (request.POST.get('email') or '').strip().lower()
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            phone = request.POST.get('phone', '')
            account_type = request.POST.get('account_type', 'user')
            is_admin = account_type == 'admin'
            
            # Validate passwords match
            if password1 != password2:
                return render(request, 'signup.html', {'error': 'Passwords do not match'})
            password = password1

        username = make_unique_username(full_name, email)

        if User.objects.filter(email__iexact=email).exists():
            if request.content_type == 'application/json':
                return JsonResponse({'error': 'Email already exists'}, status=400)
            else:
                return render(request, 'signin.html', {
                    'error': 'This email is already registered. Please sign in below.',
                    'email': email,
                    'account_type': account_type,
                })
        
        # Create user with admin privileges if specified
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            phone=phone,
            first_name=full_name,
        )
        if is_admin:
            user.is_staff = True
            user.is_superuser = True
            user.save()
        
        # For template form submission, redirect to login page with success message
        if request.content_type != 'application/json':
            return render(request, 'signin.html', {
                'success': 'Account created successfully! Please login to continue.',
                'email': email,
                'account_type': account_type,
            })
        
        return JsonResponse({'success': True})

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        password = request.POST.get('password')
        account_type = request.POST.get('account_type', 'user')
        
        # Authenticate using email (custom backend will handle this)
        user = authenticate(request, username=email, password=password)
            
        if user is not None:
            if account_type == 'admin' and not user.is_staff:
                return render(request, 'signin.html', {
                    'error': 'This is a user account. Please choose User login.',
                    'email': email,
                    'account_type': account_type,
                })
            login(request, user)
            # Redirect based on user type
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('home')
        else:
            return render(request, 'signin.html', {'error': 'Invalid credentials'})
    else:
        # For GET requests, render the beautiful signin template
        return render(request, 'signin.html')

@csrf_exempt
def forgot_password(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        password1 = request.POST.get('password1') or ''
        password2 = request.POST.get('password2') or ''

        if not email or not password1 or not password2:
            return render(request, 'forgot_password.html', {'error': 'Please fill all fields.'})
        if password1 != password2:
            return render(request, 'forgot_password.html', {'error': 'Passwords do not match.'})

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return render(request, 'forgot_password.html', {'error': 'No account found with this email.'})

        user.set_password(password1)
        user.save()
        return render(request, 'signin.html', {'success': 'Password reset successfully. Please sign in.'})

    return render(request, 'forgot_password.html')

@csrf_exempt
def logout_view(request):
    logout(request)
    if request.content_type == 'application/json':
        return JsonResponse({'success': True})
    return redirect('login')

# Home Page - Sip Smart
@login_required
def home(request):
    user = request.user
    context = {
        'user': user,
        'is_admin': user.is_staff,  # Admin check
        'coffee_shop_name': 'Sip Smart'
    }
    return render(request, 'home.html', context)

# Admin Dashboard - Sip Smart
@login_required
def admin_dashboard(request):
    # Check if user is admin
    if not request.user.is_staff:
        return redirect('home')  # Redirect non-admin users to home
    
    # Get admin statistics
    total_users = User.objects.filter(is_staff=False).count()
    total_admins = User.objects.filter(is_staff=True).count()
    all_menu_items = MenuItem.objects.all()
    total_menu_items = all_menu_items.count()
    available_items = all_menu_items.filter(availability=True).count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='Pending').count()
    preparing_orders = Order.objects.filter(status='Preparing').count()
    ready_orders = Order.objects.filter(status='Ready').count()
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    menu_items = all_menu_items.order_by('name')
    
    context = {
        'user': request.user,
        'total_users': total_users,
        'total_admins': total_admins,
        'total_menu_items': total_menu_items,
        'available_items': available_items,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'recent_orders': recent_orders,
        'menu_items': menu_items,
    }
    return render(request, 'admin_dashboard.html', context)

# Admin Actions - Update Order Status
@csrf_exempt
@login_required
def update_order_status(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_status = data.get('status')
            
            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Order #{order_id} updated to {new_status}',
                'new_status': new_status
            })
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# Admin Actions - Toggle Menu Item Availability
@csrf_exempt
@login_required
def toggle_menu_availability(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            new_availability = data.get('availability')
            
            item = MenuItem.objects.get(id=item_id)
            item.availability = new_availability
            item.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'{item.name} {"enabled" if new_availability else "disabled"}',
                'new_availability': new_availability
            })
        except MenuItem.DoesNotExist:
            return JsonResponse({'error': 'Menu item not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# Admin Actions - Update Menu Item Price
@csrf_exempt
@login_required
def update_menu_price(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            new_price = float(data.get('price'))
            
            item = MenuItem.objects.get(id=item_id)
            item.price = new_price
            item.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'{item.name} price updated to ${new_price}',
                'new_price': new_price
            })
        except MenuItem.DoesNotExist:
            return JsonResponse({'error': 'Menu item not found'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Invalid price format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# Admin Actions - Add New Menu Item
@csrf_exempt
@login_required
def add_menu_item(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            # Always handle as form data since we're using FormData in JavaScript
            name = request.POST.get('name')
            description = request.POST.get('description')
            price_str = request.POST.get('price')
            image = request.FILES.get('image')
            image_url = request.POST.get('image_url', '')
            
            if not name or not description or not price_str:
                return JsonResponse({'error': 'Name, description, and price are required'}, status=400)
            
            try:
                price = float(price_str)
            except ValueError:
                return JsonResponse({'error': 'Invalid price format'}, status=400)
            
            # Create the menu item with the current user as added_by
            item = MenuItem.objects.create(
                name=name,
                description=description,
                price=price,
                image=image,
                image_url=image_url,
                availability=True,
                added_by=request.user
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'{name} added to menu',
                'item': {
                    'id': item.id,
                    'name': item.name,
                    'description': item.description,
                    'price': float(item.price),
                    'availability': item.availability,
                    'image_url': item.image_display_url,
                    'added_by': item.added_by.email if item.added_by else 'System'
                }
            })
        except ValueError as e:
            print(f"ValueError in add_menu_item: {str(e)}")
            return JsonResponse({'error': f'Invalid price format: {str(e)}'}, status=400)
        except Exception as e:
            print(f"Error in add_menu_item: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'Error adding item: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# Admin Actions - Edit Menu Item
@csrf_exempt
@login_required
def edit_menu_item(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            # Get item ID from form data
            item_id = request.POST.get('item_id')
            if not item_id:
                return JsonResponse({'error': 'Item ID is required'}, status=400)
            
            try:
                item = MenuItem.objects.get(id=item_id)
            except MenuItem.DoesNotExist:
                return JsonResponse({'error': 'Menu item not found'}, status=404)
            
            # Update fields if provided
            name = request.POST.get('name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            image = request.FILES.get('image')
            image_url = request.POST.get('image_url', '')
            
            if name:
                item.name = name
            if description:
                item.description = description
            if price:
                item.price = float(price)
            if image:
                item.image = image
            if image_url:
                item.image_url = image_url
            
            item.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'{item.name} updated successfully',
                'item': {
                    'id': item.id,
                    'name': item.name,
                    'description': item.description,
                    'price': float(item.price),
                    'availability': item.availability,
                    'image_url': item.image_display_url,
                    'added_by': item.added_by.email if item.added_by else 'System'
                }
            })
        except ValueError:
            return JsonResponse({'error': 'Invalid price format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# User Order History
@login_required
def user_orders(request):
    user = request.user
    orders = list(Order.objects.filter(user=user).values())
    return JsonResponse({'orders': orders})

# Test view for debugging
@login_required
def test_add(request):
    if request.method == 'GET':
        return render(request, 'test_add.html')
    else:
        return add_menu_item(request)
