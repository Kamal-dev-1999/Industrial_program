from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
from .models import Notes
from .encrypt_util import encrypt, decrypt
from .forms import RegistrationForm, LoginForm, UpdatePasswordForm , AddNotesForm , NoteForm
from .models import UserPassword
from .utils import generate_random_password
from django.shortcuts import get_object_or_404 , get_list_or_404

# home page
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home_page(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % ('/', request.path))
    return render(request, 'pages/home.html')


# user login
class UserLoginView(LoginView):
    form_class = LoginForm
    template_name = 'pages/index.html'


def user_login_view(request):
    if request.user.is_authenticated:
        return redirect('/home')
    return UserLoginView.as_view()(request)


# register new user
def register_page(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account registered successfully. Please log in to your account.")
        else:
            print("Registration failed!")
    else:
        form = RegistrationForm()

    context = {'form': form}
    return render(request, 'pages/register.html', context)


# logout
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout_view(request):
    if not request.user.is_authenticated:
        return redirect('/')
    logout(request)
    return redirect('/')


# add new password
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_new_password(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % ('/', request.path))
    if request.method == 'POST':
        try:
            username = request.POST['username']
            password = encrypt(request.POST['password'])
            application_type = request.POST['application_type']
            if application_type == 'Website':
                website_name = request.POST['website_name']
                website_url = request.POST['website_url']
                UserPassword.objects.create(username=username, password=password, application_type=application_type,
                                            website_name=website_name, website_url=website_url, user=request.user)
                messages.success(request, f"New password added for {website_name}")
            elif application_type == 'Desktop application':
                application_name = request.POST['application_name']
                UserPassword.objects.create(username=username, password=password, application_type=application_type,
                                            application_name=application_name, user=request.user)
                messages.success(request, f"New password added for {application_name}.")
            elif application_type == 'Game':
                game_name = request.POST['game_name']
                game_developer = request.POST['game_developer']
                UserPassword.objects.create(username=username, password=password, application_type=application_type,
                                            game_name=game_name, game_developer=game_developer, user=request.user)
                messages.success(request, f"New password added for {game_name}.")
            return HttpResponseRedirect("/add-password")
        except Exception as error:
            print("Error: ", error)

    return render(request, 'pages/add-password.html')


# edit password
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_password(request, pk):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % ('/', request.path))
    user_password = UserPassword.objects.get(id=pk)
    user_password.password = decrypt(user_password.password)
    form = UpdatePasswordForm(instance=user_password)

    if request.method == 'POST':
        if 'delete' in request.POST:
            # delete password
            user_password.delete()
            return redirect('/manage-passwords')
        form = UpdatePasswordForm(request.POST, instance=user_password)

        if form.is_valid():
            try:
                user_password.password = encrypt(user_password.password)
                form.save()
                messages.success(request, "Password updated.")
                user_password.password = decrypt(user_password.password)
                return HttpResponseRedirect(request.path)
            except ValidationError as e:
                form.add_error(None, e)

    context = {'form': form}
    return render(request, 'pages/edit-password.html', context)


# search password
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def search(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % ('/', request.path))
    
    logged_in_user = request.user
    logged_in_user_pws = UserPassword.objects.filter(user=logged_in_user)

    if request.method == "POST":
        searched = request.POST.get("password_search", "").strip()
        
        # Prepare a query for filtering
        if searched:
            user_pw = logged_in_user_pws.filter(
                Q(website_name__icontains=searched) |
                Q(application_name__icontains=searched) |
                Q(game_name__icontains=searched) |
                Q(username__icontains=searched) |  # Add username search
                Q(website_url__icontains=searched) |  # Add website URL search
                Q(created_by__icontains=searched)  # Add created_by search
            ).values()
            
            if user_pw.exists():
                return render(request, "pages/search.html", {'passwords': user_pw})
            else:
                messages.error(request, "---YOUR SEARCH RESULT DOESN'T EXIST---")
    
    return render(request, "pages/search.html", {'pws': logged_in_user_pws})


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def search(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % ('/', request.path))
    
    logged_in_user = request.user
    logged_in_user_pws = UserPassword.objects.filter(user=logged_in_user)

    if request.method == "POST":
        searched = request.POST.get("password_search", "").strip()
        
        # Prepare a query for filtering
        if searched:
            user_pw = logged_in_user_pws.filter(
                Q(website_name__icontains=searched) |
                Q(application_name__icontains=searched) |
                Q(game_name__icontains=searched) |
                Q(username__icontains=searched) |  # Include username search
                Q(website_url__icontains=searched)  # Include website URL search
            ).values()
            
            if user_pw.exists():
                return render(request, "pages/search.html", {'passwords': user_pw})
            else:
                messages.error(request, "---YOUR SEARCH RESULT DOESN'T EXIST---")
    
    return render(request, "pages/search.html", {'pws': logged_in_user_pws})


# all passwords
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def manage_passwords(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % ('/', request.path))
    sort_order = 'asc'
    logged_in_user = request.user
    user_passwords = UserPassword.objects.filter(user=logged_in_user)
    if request.GET.get('sort_order'):
        sort_order = request.GET.get('sort_order', 'desc')
        user_passwords = user_passwords.order_by('-date_created' if sort_order == 'desc' else 'date_created')
    if not user_passwords:
        return render(request, 'pages/manage-passwords.html',
                      {'no_password': "No password available. Please add password."})
    return render(request, 'pages/manage-passwords.html', {'all_passwords': user_passwords, 'sort_order': sort_order})

# generate random password
def generate_password(request):
    password = generate_random_password()
    return JsonResponse({'password': password})




# note manager 

def note_view(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % ('/', request.path))
    logged_in_user = request.user
    notes = Notes.objects.filter(user=logged_in_user)
    
    
def add_note(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % ('/', request.path))
    
    if request.method == "POST":
        form = AddNotesForm(request.POST)
        if form.is_valid():
            # Automatically associate the logged-in user with the note
            note = form.save(commit=False)
            note.user = request.user  # Assign the logged-in user
            note.save()
            messages.success(request, "Note added successfully.")
            return redirect('/notes')  # Redirect to the notes list view
        else:
            messages.error(request, "Error adding note. Please check the form and try again.")
    else:
        form = AddNotesForm()

    context = {
        'form': form,
    }
    return render(request, 'pages/add_note.html', context)
    
    
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def notes_list_view(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % ('/', request.path))

    logged_in_user = request.user
    notes = Notes.objects.filter(user=logged_in_user)
    
    context = {
        'notes': notes
    }
    return render(request, 'pages/notes_list.html', context)


def edit_note(request, note_id):
    note = get_object_or_404(Notes, id=note_id)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('notes_list')  # Redirect to the notes list view after saving
    else:
        form = NoteForm(instance=note)

    return render(request, 'pages/edit_note.html', {'form': form, 'note': note})


# views.py
def delete_note(request, note_id):
    note = get_object_or_404(Notes, id=note_id)

    if request.method == 'POST':
        note.delete()
        return redirect('notes_list')  # Redirect to the notes list view after deleting

    return render(request, 'pages/delete_note.html', {'note': note})


def note_detail(request, note_id):
    note = get_object_or_404(Notes, id=note_id)
    return render(request, 'pages/note_detail.html', {'note': note})
