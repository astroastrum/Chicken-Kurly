from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from accounts.models import OrderItem
from .forms import *
from django.http import JsonResponse
from django.core.paginator import Paginator

from dotenv import load_dotenv
import os

# Create your views here.
def index(request):
    load_dotenv()  # .env 파일에서 환경 변수를 불러옵니다.
    ACCESS_TOKEN = os.getenv("API_TOKEN")
    products = Product.objects.order_by('-pk')
    products_name = Product.objects.order_by('product_name')
    categories = Product.objects.values('category').distinct()
    review = Review.objects.order_by('-pk')
    hits = Product.objects.order_by('-hit')
    sold = Product.objects.order_by('-sold_count')
    # print(categories)

    context = {
        'products': products,
        'review':review,
        'hits': hits,
        'sold': sold,
        'ACCESS_TOKEN': ACCESS_TOKEN,
        'categories': categories,
        'products_name': products_name,
        # 'image_cnt': products.image_set.count(), # index 페이지에서 carousel로 보여줄 때 사용
    }

    return render(request, 'products/index.html', context)


# admin의 판매 상품 등록
@login_required
def create(request):
    # 요청한 user의 is_superuser가 1이면(admin이면)
    if request.user.is_superuser == 1: 
        if request.method == 'POST':
            product_form = ProductForm(request.POST)
            # form에 image 폼 추가
            image_form = ImageForm(request.POST, request.FILES)
            tmp_images = request.FILES.getlist('image')
            
            # 상품 정보에 대한 폼과 이미지 폼이 유효하면
            if product_form.is_valid() and image_form.is_valid():
                product = product_form.save(commit=False)
                product.admin = request.user

                if tmp_images:
                    for img in tmp_images:
                        img_instance = Image(product=product, image=img)
                        product.save()
                        img_instance.save()

                product.save()
                return redirect('products:index')
        else:
            product_form = ProductForm()
            image_form = ImageForm()
            
        context = {
            'product_form': product_form,
            'image_form': image_form,
        }

        return render(request, 'products/create.html', context)
    
    else:
        return redirect('products:index')    # admin 아니면 index로 리다이렉트


def detail(request, product_pk):
    product = Product.objects.get(pk=product_pk)
    product_buy_form = ProductBuyForm()
    inquiry_form = InquiryForm()
    reply_form = ReplyForm()
    inquiries = product.inquiry_set.order_by('-pk') # 문의 최신순
    reviews = product.review_set.order_by('-pk') # 리뷰 최신순
    # print(reviews[3].reviewimage_set.all())

    # model에서 hit은 default=0으로 설정했고 한 번 볼 때마다 1 증가하도록
    product.hit += 1
    product.save()


    # 문의 페이지네이션
    inquiry_page = request.GET.get('inquiry_page', '1')
    inquiry_paginator = Paginator(inquiries, 5)
    inquiry_page_obj = inquiry_paginator.get_page(inquiry_page)

    
    # 후기 페이지네이션
    review_page = request.GET.get('review_page', '1')
    review_paginator = Paginator(reviews, 5)
    review_page_obj = review_paginator.get_page(review_page)
    context = {
        'product': product,
        'image_cnt': product.image_set.count(),
        'product_buy_form': product_buy_form,
        'inquiry_form': inquiry_form,
        'reply_form': reply_form,
        'inquiries': inquiries,
        'inquiries': inquiry_page_obj,  # 문의 페이지네이션
        'reviews': review_page_obj, # 후기 페이지네이션
    }

    return render(request, 'products/detail.html', context)


def update(request, product_pk):
    product = Product.objects.get(pk=product_pk)
    images = Image.objects.filter(product_id=product_pk)
    
    # 요청한 user의 is_superuser가 1이면(admin이면)
    if request.user.is_superuser == 1:
        if request.method == 'POST':
            product_form = ProductForm(request.POST, instance=product)
            image_form = ImageForm(request.POST, request.FILES) 
            tmp_images = request.FILES.getlist('image') # TemporaryUploadedFile 객체 리스트

            # 기존 이미지 삭제
            for img in images:
                if img:
                    img.delete()

            # 상품 정보 폼과 이미지 폼이 유효하면
            if product_form.is_valid() and image_form.is_valid():
                product = product_form.save(commit=False)

                if tmp_images:
                    for img in tmp_images:
                        img_instance = Image(product=product, image=img)
                        product.save()
                        img_instance.save()

                product.save()
                # 상품 상세 보기 페이지로
                return redirect('products:detail', product_pk)
        
        else:
            product_form = ProductForm(instance=product)
            if images:
                image_form = ImageForm(instance=images[0])
            else:
                image_form = ImageForm()
            
        context = {
            'product_form': product_form,
            'image_form': image_form,
        }

        return render(request, 'products/create.html', context)
    
    else:
        return redirect('products:detail', product_pk) 


# 찜
def ddib(request, product_pk):
    product = Product.objects.get(pk=product_pk)
    ddib = Ddib.objects.get(user=request.user) # user와 ddib 1:1
    ddib_items = ddib.ddibitem_set.all()
    # print(ddib_items[0])

    for item in ddib_items: # 
        if product == item.product:
            item.delete() # 찜 목록에서 item을 지우고
            is_ddib = False
            break

    else: # 찜한 상태가 아니라면
        DdibItem.objects.create(ddib=ddib, product=product)
        is_ddib = True
    context = {
        "is_ddib": is_ddib
        }
    # return redirect('products:detail', product_pk)
    return JsonResponse(context)

@login_required
def cart(request, product_pk):
    product = Product.objects.get(pk=product_pk)

    # 유저 회원가입 시 장바구니가 자동으로 생성됨.
    # 로그인 한 유저면 카트 인스턴스를 생성함.
    cart = Cart.objects.get(user=request.user)

    does_exist = False
    
    if request.method == 'POST':
        # 구매 수량 입력 후 장바구니
        product_buy_form = ProductBuyForm(request.POST)

        if product_buy_form.is_valid():
            form = product_buy_form.save(commit=False)

            cart_items = cart.cartitem_set.all()

            # 이미 같은 상품이 있으면, 수량 추가
            for item in cart_items:
                if product == item.product:
                    item.quantity += form.quantity
                    item.save()
                    does_exist = True
                    break
            else:
                CartItem.objects.create(cart=cart, product=product, quantity=form.quantity)

    data = {
        'doesExist': does_exist,
    }

    return JsonResponse(data)


# 후기 작성
@login_required
def review_create(request, product_pk):
    product = Product.objects.get(pk=product_pk)
    if request.method == 'POST':
        review_form = ReviewForm(request.POST)
        # form에 review_image 폼 추가
        review_image_form = ReviewImageForm(request.POST, request.FILES)
        tmp_img = request.FILES.getlist('review_img')
                
        # 리뷰 작성에 대한 폼과 이미지 폼이 유효하면
        if review_form.is_valid() and review_image_form.is_valid():
            review = review_form.save(commit=False)
            review.user = request.user
            review.product = product

            if tmp_img:
                for img in tmp_img:
                    img_instance = ReviewImage(review=review, review_img=img)
                    review.save()
                    img_instance.save()

            review.save()
            # messages.success(request, '후기가 정상적으로 수정되었습니다..')
            return redirect('products:detail', product_pk)
    else:
        review_form = ReviewForm()
        review_image_form = ReviewImageForm()
                
    context = {
        'review_form': review_form,
        'review_image_form': review_image_form
    }

    return render(request, 'products/review.html', context)

# 후기 수정
@login_required
def review_update(request, product_pk, review_pk):
    product = Product.objects.get(pk=product_pk)
    review = get_object_or_404(Review, pk=review_pk)

    review_images = ReviewImage.objects.filter(pk=review_pk)

    if request.user == review.user:
        if request.method == 'POST':
            review_form = ReviewForm(request.POST, instance=review)
            # form에 review_image 폼 추가
            review_image_form = ReviewImageForm(request.POST, request.FILES)
            tmp_img = request.FILES.getlist('review_img')
                    
            for img in review_images:
                if img:
                    img.delete()

            # 리뷰 작성에 대한 폼과 이미지 폼이 유효하면
            if review_form.is_valid() and review_image_form.is_valid():
                review = review_form.save(commit=False)

                review.user = request.user
                review.product = product

                if tmp_img:
                    for img in tmp_img:
                        img_instance = ReviewImage(review=review, review_img=img)
                        review.save()
                        img_instance.save()

                review.save()
                # messages.success(request, '후기 수정이 완료되었습니다.')
                # 후기 목록이 포함된 상품 상세 보기 페이지로
                return redirect('products:detail', product_pk)
        else:
            review_form = ReviewForm(instance=review)
            if review_images:
                review_image_form = ReviewImageForm(instance=review_images[0])
            else:
                review_image_form = ReviewImageForm()
            
        context = {
            'review_form': review_form,
            'review_image_form': review_image_form,
            'review': review,
        }

        return render(request, 'products/review_update.html', context)
    
    else:
        return redirect('products:detail', product_pk) 

# 후기 삭제
@login_required
def review_delete(request, product_pk, review_pk):
    review = get_object_or_404(Review, pk=review_pk)

    if request.user == review.user:
        review.delete()

    return redirect('products:detail', product_pk)

# 상품 문의 등록
@login_required
def create_inquiry(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    inquiry_form = InquiryForm(request.POST)    # POST 아닌 건 detail에

    # inquiry_pk = -1
    # inquiry_user = ''
    # inquiry_created_at = ''
    # inquiry_title = ''
    # inquiry_content = ''
    # product_image_url = product.image_set.all()[0].image.url
    # product_name = product.product_name
    # product_content = product.content

    if inquiry_form.is_valid():
        inquiry = inquiry_form.save(commit=False)
        inquiry.user = request.user
        inquiry.product = product
        inquiry.save()

        # inquiry_pk = inquiry.pk
        # inquiry_user = inquiry.user.username
        # inquiry_created_at = inquiry.created_at.strftime('%Y.%m.%d')
        # inquiry_title = inquiry.title
        # inquiry_content = inquiry.content


    # 페이지네이션하고 비동기 같이 하니까 이상해서 제거..ㅠㅠ
    # data = {
    #     'inquiryPk': inquiry_pk,
    #     'inquiryUser': inquiry_user,
    #     'inquiryCreatedAt': inquiry_created_at,
    #     'inquiryTitle': inquiry_title,
    #     'inquiryContent': inquiry_content,
    #     'productImageUrl': product_image_url,
    #     'productName': product_name,
    #     'productContent': product_content,
    # }

    # return JsonResponse(data)

    return redirect('products:detail', product_pk)


# 상품 문의 수정
# 정석은 모달 하나만
# 지금은 input 태그로..
@login_required
def update_inquiry(request, product_pk, inquiry_pk):
    product = get_object_or_404(Product, pk=product_pk)
    inquiry = get_object_or_404(Inquiry, pk=inquiry_pk)

    inquiry_title = ''
    inquiry_content = ''

    if request.user == inquiry.user:
        # 모델폼이 아니어도 유효성검사가 된다.
        if request.method == 'POST':
            inquiry_form = InquiryForm(request.POST, instance=inquiry)    # POST 아닌 건 detail에
            if inquiry_form.is_valid():
                new_inquiry = inquiry_form.save(commit=False)
                new_inquiry.user = request.user
                new_inquiry.product = product
                new_inquiry.save()

                inquiry_title = new_inquiry.title
                inquiry_content = new_inquiry.content

        else:
            inquiry_form = InquiryForm(instance=inquiry)

    data = {
        'inquiryTitle': inquiry_title,
        'inquiryContent': inquiry_content,
        'inquiry': inquiry,
    }

    # return redirect('products:detail', product_pk)
    return JsonResponse(data)


# 상품 문의 삭제
@login_required
def delete_inquiry(request, product_pk, inquiry_pk):
    inquiry = get_object_or_404(Inquiry, pk=inquiry_pk)

    is_deleted = -1 # False

    if request.user == inquiry.user:
        inquiry.delete()
        is_deleted = inquiry.pk

    data = {
        'isDeleted': is_deleted,
    }

    # return redirect('products:detail', product_pk)
    return JsonResponse(data)


@login_required
def create_reply(request, product_pk, inquiry_pk):
    product = get_object_or_404(Product, pk=product_pk)
    inquiry = get_object_or_404(Inquiry, pk=inquiry_pk)
    reply_form = ReplyForm(request.POST)    # POST 아닌 건 detail에

    reply_content = ''

    if request.user.is_superuser == 1:
        if reply_form.is_valid():
            reply = reply_form.save(commit=False)
            reply.user = request.user
            reply.inquiry = inquiry
            reply.product = product
            reply.save()
            reply_content = reply.content

    data = {
        'replyContent': reply_content,
    }

    # return redirect('products:detail', product_pk)
    return JsonResponse(data)


@login_required
def payment(request, product_pk):
    product = Product.objects.get(pk=product_pk)

    imp_uid = request.POST.get('imp_uid')
    merchant_uid = request.POST.get('merchant_uid')
    quantity = request.POST.get('quantity')
    total_price = product.price * int(quantity)

    # 위의 정보를 바탕으로 주문서 작성
    OrderItem.objects.create(product=product, quantity=quantity, user=request.user, imp_uid=imp_uid, merchant_uid=merchant_uid, price=total_price)
    product.sold_count += 1
    product.save()

    return redirect('products:detail', product_pk)