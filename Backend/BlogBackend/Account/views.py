from django.shortcuts import render, redirect
from django.http import HttpResponse 
from django.contrib.auth import login, authenticate,logout
from Account.forms import RegistrationForm,AccountAuthenticationForm,AccountUpdateForm
from .models import Account
import json
import cv2

def RegisterUser(request,*args,**kwargs):
    user = request.user 
    if user.is_authenticated: 
        return HttpResponse(f"You are already authenticated as {user.email}.")
    context={}
    
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email').lower()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            account = authenticate(email=email,password=raw_password)
            login(request,account)
            destination = kwargs.get("next")
            if destination:
                return redirect(destination)
            return redirect("home")
        else:
            context['registration_form'] = form
    else:
        return render(request,'account/register.html',context)   

# Create your views here.
def LoginView(request):
    context = {}
    user = request.user
    if user.is_authenticated:
        return redirect("home")
    destination = get_redirect_if_exists(request)
    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email=email,password=password)
            if user:
                login(request,user)
                destination = get_redirect_if_exists(request)
                if destination:
                   return redirect(destination)
                return redirect("home")
        else:
            context['login_form'] = form  
    return render(request,"account/login.html",context)

def get_redirect_if_exists(request):
    redirect = None
    if request.GET:
        if request.GET.get("next"):
            redirect(request.GET.get("next"))
        return redirect

def home(request):
    user = request.user
    context = {}
    return render(request, 'home.html',context)

def AccountView(request,*args,**kwargs):
    context = {}
    user_id = kwargs.get("user_id")
    try:
        account = Account.objects.get(pk=user_id)
    except Account.DoesNotExist:
        return HttpResponse("that user doesn't exist.")
    try:
        account = Account.objects.get(pk=user_id)
    except Account.DoesNotExist:
        raise HttpResponse("something went wrong.")
    if account.pk == request.user.pk:
        context['is_self'] = True
    else:
        context["is_self"] = False
    form = AccountUpdateForm(
        initial = {
        "id":account.pk,
        "email":account.email,
        "username": account.username,
        "profile_image": account.profile_image,
        "hide_email": account.hide_email,
        "name": account.name,
        "surname":account.surname,
        }
        )
    context['form'] = form 
    return render(request,'account/account.html',context)

def edit_account(request,*args,**kwargs):
    if not request.user.is_authenticated:
       return redirect("login")
    user_id = kwargs.get("user_id") 
    try:
        account = Account.objects.get(pk=user_id)
    except Account.DoesNotExist:
        raise HttpResponse("something went wrong.")
    if account.pk !=request.user.pk:
        return HttpResponse("You cannot edit someone elses profile.")
    if request.POST:
        form = AccountUpdateForm(request.POST,request.FILES,instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("account:view", user_id=account.pk)
        else:
            # form = AccountUpdateForm(request.POST,instance=request.user,
            #       initial = {
            #         "id":account.pk,
            #         "email":account.email,
            #         "username": account.username,
            #         "profile_image": account.profile_image,
            #         "hide_email": account.hide_email
            #       }
            # )
            # context['form'] = 
            redirect(f"account/{user_id}")
            
    else:
       redirect(f'account/{user_id}')

def logout_view(request):
    logout(request)
    return redirect("login")

def delete_picture(request,*args,**kwargs):
    user = request.user
    payload={}
    if request.method == "GET" and user.is_authenticated:
        user_id = kwargs.get("user_id")
        if user_id:
            try:
                account = Account.objects.get(pk=user_id)
            except Account.DoesNotExist:
                payload['response'] = "user does not exist"
            image = account.profile_image
            image.delete()
            payload["response"] = "successfully deleted profile image."
        else:
            payload["response"] = " invalid request"
    else:
        payload["response"] = "you must be authenticated to do this"
    return HttpResponse(json.dumps(payload),content_type="application/json")

def save_temp_profile_image_from_base64String(imageString,user):
    INCORRECT_PADDING_EXCEPTION = "Incorrect padding"
    try:
        if not os.path.exists(settings.TEMP):
            os.mkdir(settings.TEMP)
        if not os.path.exists(f"{settings.TEMP}/{user.pk}"):
            os.mkdir(f"{settings.TEMP}/{user.pk}")
        url = os.path.join(f"{settings.TEMP}\{user.pk}",TEMP_PROFILE_IMAGE_NAME)
        storage = FileSystemStorage(location=url)
        image = base64.b64decode(imageString)
        with storage.open('', 'wb+') as destination:
            destination.write(image)
            destination.close()
        return url
    except Exception as e:
        print(f"exception:{e}")
		# workaround for an issue I found
        if f"{e}" == INCORRECT_PADDING_EXCEPTION:
            imageString += "=" * ((4 - len(imageString) % 4) % 4)
            return save_temp_profile_image_from_base64String(imageString, user)
    return None


    
def crop_image(request, *args, **kwargs):
    payload = {}
    user = request.user
    if request.POST and user.is_authenticated:
        try:
            imageString = request.POST.get("image")
            url = save_temp_profile_image_from_base64String(imageString, user)
            img = cv2.imread(url)

            cropX = int(float(str(request.POST.get("cropX"))))
            cropY = int(float(str(request.POST.get("cropY"))))
            cropWidth = int(float(str(request.POST.get("cropWidth"))))
            cropHeight = int(float(str(request.POST.get("cropHeight"))))
            if cropX <= 0:
                cropX = 0
            elif cropY <= 0:
                cropY = 0
            crop_img = img[cropY:cropY+cropHeight, cropX:cropX+cropWidth]

            cv2.imwrite(url, crop_img)

			# delete the old image
            user.profile_image.delete()

			# Save the cropped image to user model
            user.profile_image.save("profile_image.png", files.File(open(url, 'rb')))
            user.save()

            payload['result'] = "success"
            payload['cropped_profile_image'] = user.profile_image.url

			# delete temp file
            os.remove(url)
			
        except Exception as e:
            print(f"exception:{e}")
            payload['result'] = "error"
            payload['exception'] = f"{e}"
    return HttpResponse(json.dumps(payload), content_type="application/json")
