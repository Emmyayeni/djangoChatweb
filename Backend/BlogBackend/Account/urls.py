from django.urls import path 

from Account.views import (
   edit_account,
   AccountView,
   delete_picture,
   
    # account_view,
    # edit_account,
    crop_image,
    # test

)

app_name = "account"

urlpatterns = [
    path('<user_id>',AccountView,name='view'),
    path('<user_id>/edit',edit_account,name='edit'),
    path('<user_id>/delete_image',delete_picture,name="delete_image"),
    # path('',test,name='view'),
    # path('<user_id>/edit',edit_account,name='edit'),
    path('<user_id>/edit/cropImage',crop_image,name='crop_image'),
]
