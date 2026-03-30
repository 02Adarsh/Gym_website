from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from authapp.models import Contact,MembershipPlan,Trainer,Enrollement,Gallery,Attendance
import qrcode
from django.http import HttpResponse
from django.utils import timezone
import hashlib
from django.conf import settings
from datetime import date

# Create your views here.
def Home(request):
    return render(request, "index.html")

def gallery(request):
    posts=Gallery.objects.all
    context={"posts":posts}
    return render(request, "gallery.html",context)

def attendance(request):
    if not request.user.is_authenticated:
        messages.warning(request,"Please login and Try again")
        return redirect('/handlelogin')
    SelectTrainer=Trainer.objects.all()
    context={"SelectTrainer":SelectTrainer}
    if request.method == "POST":
        PhoneNumber=request.POST.get('PhoneNumber')
        Login=request.POST.get('Logintime')
        Logout=request.POST.get('Logout')
        SelectWorkout=request.POST.get('SelectWorkout')
        TrainedBy=request.POST.get('SelectTrainer')
        query=Attendance(PhoneNumber=PhoneNumber,Login=Login,Logout=Logout,SelectWorkout=SelectWorkout,TrainedBy=TrainedBy)
        query.save()
        messages.warning(request,"Attendance Applied Successfully")
        return redirect('/attendance')

    return render(request, "attendance.html",context)

def profile(request):
    if not request.user.is_authenticated:
        messages.warning(request,"Please login and Try again")
        return redirect('/handlelogin')
    user_name=request.user.username
    posts=Enrollement.objects.filter(FullName=user_name)
    attendance=Attendance.objects.filter(PhoneNumber__in=posts.values_list('PhoneNumber', flat=True))
    context={"posts":posts,"attendance":attendance}
    print(posts)
    return render(request, "profile.html",context)

def signup(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('pass1')
        pass2 = request.POST.get('pass2')

        if pass1 != pass2:
            messages.info(request, "Password is not matching")
            return redirect('signup')
          
        if User.objects.filter(username=username).exists():
            messages.warning(request, "Username is taken")
            return redirect('signup')

        myuser = User.objects.create_user(username, email, pass1)
        myuser.save()

        messages.success(request, "User created, please login")
        return redirect('handlelogin')   
    return render(request, "signup.html")

def handlelogin(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('pass1')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login Successful")
            return redirect('Home')
        else:
            messages.error(request, "Invalid Username or Password")
            return redirect('handlelogin')   

    return render(request, "handlelogin.html")   

    return render(request,"handlelogin.html")
    
def handlelogout(request):
    logout(request)
    messages.success(request, "Logout Success")
    return redirect('handlelogin')   

def contact(request):
    if request.method=="POST":
        name = request.POST.get('username')
        email = request.POST.get('email')
        number = request.POST.get('number')
        desc= request.POST.get('desc')
        myquery=Contact(name=name,email=email,phonenumber=number,description=desc)
        myquery.save()

        messages.info(request,"Thanks for contacting us we will get back you soon")
        return redirect('/contact')
    
    return render(request,"contact.html") 

def enroll(request):
    if not request.user.is_authenticated:
        messages.warning(request,"Please login and Try again")
        return redirect('/handlelogin')
    Membership=MembershipPlan.objects.all()
    SelectTrainer=Trainer.objects.all()
    context={"Membership":Membership,"SelectTrainer":SelectTrainer}
    if request.method=="POST":
        FullName=request.user.username
        Email=request.POST.get('Email')
        PhoneNumber=request.POST.get('PhoneNumber')
        Gender=request.POST.get('Gender')
        Dob=request.POST.get('Dob')
        SelectMembershipplan=request.POST.get('SelectMembershipplan')
        SelectTrainer=request.POST.get('SelectTrainer')
        Reference=request.POST.get('Reference')
        Address=request.POST.get('Address')
        query=Enrollement(FullName=FullName,Email=Email,PhoneNumber=PhoneNumber,Gender=Gender,Dob=Dob,
        SelectMembershipplan=SelectMembershipplan,SelectTrainer=SelectTrainer,
        Reference=Reference,Address=Address)
        query.save()
        messages.success(request,"Thanks for the Enrollment")
        return redirect('/join')
    return render(request, "enroll.html",context)


#qr code-------------------

def generate_qr(request):
    if not request.user.is_authenticated:
        return redirect('/handlelogin')

    today = date.today()

    raw_data = f"{today}{settings.QR_SECRET_KEY}"
    token = hashlib.sha256(raw_data.encode()).hexdigest()

    # 🔥 IMPORTANT CHANGE
    host = request.get_host()
    url = f"http://{host}/qr-attendance/?token={token}"

    import qrcode
    from django.http import HttpResponse

    img = qrcode.make(url)

    response = HttpResponse(content_type='image/png')
    img.save(response, "PNG")

    return response

def qr_attendance(request):
    if not request.user.is_authenticated:
        return redirect('/handlelogin')

    token = request.GET.get('token')

    if not token:
        return HttpResponse("No Token Found ❌")

    today = date.today()
    raw_data = f"{today}{settings.QR_SECRET_KEY}"
    valid_token = hashlib.sha256(raw_data.encode()).hexdigest()

    # 🔥 DEBUG PRINT (important)
    print("Received Token:", token)
    print("Valid Token:", valid_token)

    if token != valid_token:
        return HttpResponse("Invalid or Expired QR ❌")

    user_name = request.user.username
    user_data = Enrollement.objects.filter(FullName=user_name).first()

    if not user_data:
        return HttpResponse("User not enrolled ❌")

    phone = user_data.PhoneNumber

    already = Attendance.objects.filter(
        PhoneNumber=phone,
        Selectdate__date=today
    ).exists()

    if already:
        return HttpResponse("Attendance already marked today ✅")

    Attendance.objects.create(
        PhoneNumber=phone,
        Login=str(timezone.now().time()),
        Logout="",
        SelectWorkout="QR Scan",
        TrainedBy="Self"
    )

    return HttpResponse("Attendance Marked Successfully ✅")