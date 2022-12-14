from django.urls import path
from . import views


app_name = 'articles'

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create, name='create'),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/delete/", views.delete, name="delete"),
    path("<int:pk>/update/", views.update, name="update"),
    path("comment/<int:pk>/", views.c_create, name="c_create"),
    path("comment/<int:c_pk>/delete/<int:a_pk>", views.c_delete, name="c_delete"),
    path("like/<int:pk>/", views.like, name="like"),
    path("c_like/<int:c_pk>/", views.c_like, name="c_like"),
    path("rec_like/<int:c_pk>/<int:a_pk>", views.rec_like, name="rec_like"),
    path("rec_create/<int:c_pk>/<int:a_pk>", views.rec_create, name="rec_create"),
    path("rec_detail_create/<int:c_pk>/<int:a_pk>", views.rec_detail_create, name="rec_detail_create"),
    path("rec_detail/<int:c_pk>/<int:a_pk>", views.rec_detail, name="rec_detail"),
    path("search/", views.search, name="search"),
    path("recomment/<int:c_pk>/delete/<int:a_pk>", views.recomment_delete, name="recomment_delete"),    
    path("rec_delete/<int:rec_pk>/<int:c_pk>/<int:a_pk>", views.rec_delete, name="rec_delete"),    
] 
