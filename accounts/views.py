from django.shortcuts import render, redirect, get_object_or_404
from .forms import SignupForm
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import login as auth_login
from django.contrib.auth import get_user_model
from django.contrib.auth import logout as auth_logout
from .forms import CustomUserChangeForm, ProfileForm
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from products.models import Cart, Ddib
from .models import OrderItem

from .forms import ImageForm, OrderItemForm
from django.contrib import messages
from products.models import Image



# Create your views here.
def signup(request):
    if request.method == "POST":
        forms = SignupForm(request.POST, request.FILES)
        if forms.is_valid():
            user = forms.save()
            Cart.objects.create(user=user)
            Ddib.objects.create(user=user)
            return redirect("articles:index")
    else:
        forms = SignupForm()
    context = {
        "forms": forms,
    }
    return render(request, "accounts/signup.html", context)


def index(request):
    members = get_user_model().objects.all()
    return render(request, "accounts/index.html")


def login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect(request.GET.get("next") or "articles:index")
    else:
        form = AuthenticationForm()
    context = {"forms": form}
    return render(request, "accounts/login.html", context)


def logout(request):
    auth_logout(request)
    return redirect("accounts:index")


@login_required
def update(request):
    if request.method == "POST":
        forms = CustomUserChangeForm(request.POST, instance=request.user)
        if forms.is_valid():
            forms.save()
            
            return redirect("accounts:profile", request.user.pk)
    else:
        forms = CustomUserChangeForm(instance=request.user)
    context = {
        "forms": forms,
    }
    return render(request, "accounts/update.html", context)


@login_required
def change_password(request):
    if request.method == "POST":
        forms = PasswordChangeForm(request.user, request.POST)
        if forms.is_valid():
            forms.save()
            return redirect("accounts:profile")
    else:
        forms = PasswordChangeForm(request.user)
    context = {
        "forms": forms,
    }
    return render(request, "accounts/change_password.html", context)


def profile(request, user_pk):
    OrderItems = OrderItem.objects.order_by('-pk')
    order_items = OrderItem.objects.filter(user=request.user)
   
    person = get_user_model()
    person = get_object_or_404(person, pk=user_pk)
    context = {
        "OrderItems": OrderItems,
        "person": person,
        'order_items': order_items,
        
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_update(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile", request.user.pk)
    else:
        form = ProfileForm(instance=request.user)
    return render(
        request,
        "accounts/profile_update.html",
        {
            "form": form,
        },
    )


@login_required
def follow(request, user_pk):
    person = get_user_model().objects.get(pk=user_pk)
    if person != request.user:
        if person.followers.filter(pk=request.user.pk).exists():
            person.followers.remove(request.user)
        else:
            person.followers.add(request.user)
        return redirect("accounts:profile", user_pk)
    else:
        return HttpResponseForbidden()


@login_required
def delete(request):
    request.user.delete()
    auth_logout(request)
    return redirect("accounts:login")


# admin의 판매 상품 등록
@login_required
def create(request):
    # 요청한 user의 is_superuser가 1이면(admin이면)
    if request.user.is_superuser == 1: 
        if request.method == 'POST':
            OrderItem_form = OrderItemForm(request.POST, request.FILES)
            # form에 image 폼 추가      
            # 상품 정보에 대한 폼과 이미지 폼이 유효하면
            if OrderItem_form.is_valid():
                OrderItem = OrderItem_form.save(commit=False)
                OrderItem.admin = request.user
                OrderItem.user = request.user
                OrderItem.save()
                messages.success(request, '상품 등록이 완료되었습니다.')
                return redirect('accounts:profile', request.user.pk)
        else:
            OrderItem_form = OrderItemForm()         
        context = {
            'OrderItem_form': OrderItem_form,
            
        }

        return render(request, 'accounts/create.html', context)
    
    else:
        return redirect('products:index')    # admin 아니면 index로 리다이렉트


# 로그인한 유저의 장바구니 페이지
@login_required
def cart(request):
    cart = Cart.objects.get(user=request.user)

    cart_items = cart.cartitem_set.all()

    context = {
        'cart_items': cart_items,
    }

    return render(request, 'accounts/cart.html', context)