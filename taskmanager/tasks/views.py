from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from collections import Counter
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import *
from .forms import *
from messaging.models import Message
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
# from .tasks import send_email_task # Uncomment if you are using Celery

def is_ajax(request):
    """ Helper function to check if the request is an AJAX request """
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

def serialize_task(task):
    return {
        'id': task.id,
        'task_name': task.task_name,
        'description': task.description or "",
        'assigned_to': task.assigned_to.username if task.assigned_to else "N/A",
        'assigned_to_id': task.assigned_to.id if task.assigned_to else None,
        'email': task.email,
        'priority': task.priority,
        'priority_class': 'danger' if task.priority == 'High' else ('warning text-dark' if task.priority == 'Medium' else 'success'),
        'status': task.status,
        'due_date': task.due_date.strftime('%Y-%m-%d'),
        'comment': task.comment or "",
        'upload': task.upload.url if task.upload else None,
    }
    
def home(request):
    return render(request, "home.html")

@login_required
def task_list(request):
    # Determine base template
    if request.user.is_authenticated and (
        request.user.user_type == '1' or str(request.user.user_type).lower() == 'admin'
    ):
        base_template = 'admin/admin_base.html'
    elif request.user.is_authenticated and (
        request.user.user_type == '2' or str(request.user.user_type).lower() == 'employee'
    ):
        base_template = 'admin/admin_base.html'
    else:
        base_template = 'base.html'


    tasks = Task.objects.all()
    form = TaskForm()

    # Get status choices from model
    status_choices = Task._meta.get_field('status').choices

    context = {
        'tasks': tasks,
        'form': form,
        'base_template': base_template,
        'status_choices': status_choices,
    }

    return render(request, 'task_list.html', context)

@login_required
def jqgrid_tasks(request):
    """ This view provides data specifically for the JQGrid plugin. """
    page = int(request.GET.get('page', 1))
    rows = int(request.GET.get('rows', 10))
    
    tasks = Task.objects.all().order_by('-id')
    if request.user.user_type == '2' or request.user.user_type == 'employee':
        tasks = tasks.filter(assigned_to=request.user)

    # Filtering logic
    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(Q(task_name__icontains=search_query) | Q(assigned_to__username__icontains=search_query) | Q(email__icontains=search_query))
    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    
    # Sorting
    sidx = request.GET.get('sidx', 'created_date')
    sord = request.GET.get('sord', 'desc')
    if sidx:
        order = f'-{sidx}' if sord == 'desc' else sidx
        tasks = tasks.order_by(order)

    # Pagination
    paginator = Paginator(tasks, rows)
    total_records = paginator.count
    total_pages = paginator.num_pages
    paged_tasks = paginator.get_page(page)
    
    response_rows = []
    for task in paged_tasks:
        response_rows.append({
            'id': task.id,
            'task_name': task.task_name,
            'assigned_to': task.assigned_to.username if task.assigned_to else "N/A",
            'email': task.email,
            'priority': task.priority,
            'status': task.status,
            'due_date': task.due_date.strftime('%Y-%m-%d'),
        })

    response = {
        'page': page,
        'total': total_pages,
        'records': total_records,
        'rows': response_rows
    }
    return JsonResponse(response)


@login_required
@staff_member_required
def task_create(request):
    """Handles the creation of a new task via an AJAX POST request."""
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save()

            subject = f'New Task Assigned: {task.task_name}'
            attachment_url = None
            if task.upload:
                attachment_url = request.build_absolute_uri(task.upload.url)

            email_context = {
                'task': task,
                'attachment_url': attachment_url,
            }
            
            html_message = render_to_string('email_notification.html', email_context)
            plain_message = strip_tags(html_message)
            from_email = 'your-email@example.com' # Change this
            to_email = task.email

            if to_email:
                send_mail(
                    subject,
                    plain_message,
                    from_email,
                    [to_email],
                    html_message=html_message
                )
            
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if is_ajax(request):
        status_choices = Task._meta.get_field('status').choices
        return JsonResponse({'success': True, 'task': serialize_task(task), 'status_choices': status_choices})
    return JsonResponse({'success': False}, status=400)

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not (request.user.is_staff or task.assigned_to == request.user):
         raise PermissionDenied
    if request.method == "POST":
        form = TaskEditForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False}, status=400)

@login_required
def update_task_status(request, pk):
    """
    Handles status and comment updates from employees and sends a notification to admins.
    This creates a message that will be visible in the "Work Updates" section.
    """
    if not is_ajax(request) or request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

    task = get_object_or_404(Task, pk=pk)
    
    if task.assigned_to != request.user and not request.user.is_staff:
         raise PermissionDenied

    new_status = request.POST.get('status')
    comment = request.POST.get('comment', '')

    if not new_status:
        return JsonResponse({'success': False, 'error': 'Status not provided'}, status=400)

    task.status = new_status
    task.comment = comment
    task.save()

    if request.user.user_type == '2' or request.user.user_type == 'employee':
        admins = CustomUser.objects.filter(Q(user_type='1') | Q(user_type='admin'))
        for admin in admins:
            Message.objects.create(
                sender=request.user,
                recipient=admin,
                subject=f"Task Updated: {task.task_name}",
                body=f"The task '{task.task_name}' has been updated by {request.user.username}.\n\nNew Status: {new_status}\n\nComment:\n{comment}"
            )

    return JsonResponse({'success': True})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not request.user.is_staff:
         raise PermissionDenied
    if request.method == 'POST':
        task.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


def registration(request):
    if request.method == 'POST':
        # ... (your existing registration logic)
        user_type = request.POST.get("user_type")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        gender = request.POST.get("gender")
        age = request.POST.get("age")
        contact_no = request.POST.get("contact_no")
        profile_pic = request.FILES.get("profile_pic")
        
        if password == confirm_password:
            user = CustomUser.objects.create_user(
                username = username, email = email, password = password,
                user_type= user_type, gender = gender, age = age,
                contact_no = contact_no, profile_pic = profile_pic,
            )
            if user_type == 'employee':
                   EmployeeProfile.objects.create(username=user)
            elif user_type == 'admin':
                   AdminProfile.objects.create(username=user)
            return redirect("tasks:loginPage")
    
    return render(request, "registration.html" )


def loginPage(request):
    if request.method == 'POST':
        # ... (your existing login logic)
        user_name = request.POST.get("username")
        pass_word = request.POST.get("password")
        
        try:
            user = authenticate(request, username=user_name, password = pass_word)
            if user is not None:
                login(request, user)
                if user.is_authenticated and (user.user_type == '1' or user.user_type == 'admin'):
                    return redirect("tasks:AdminDashboard")
                elif user.is_authenticated and (user.user_type == '2' or user.user_type == 'employee'):
                    return redirect("tasks:employeeDashboard")
                else:
                    return redirect("tasks:home")
            else:
                return render(request, 'loginPage.html', {'error': 'Invalid credentials'})
        except CustomUser.DoesNotExist:
            return redirect("tasks:registration")
    
    return render(request, 'loginPage.html')


def logoutPage(request):
    logout(request)
    return redirect("tasks:loginPage")


@login_required
def AdminProfilePage(request):
    profile = None
    try:
        if request.user.user_type == 'admin':
            profile = request.user.admin
        elif request.user.user_type == 'employee':
            profile = request.user.employee.first()
    except (AdminProfile.DoesNotExist, EmployeeProfile.DoesNotExist):
        pass
        
    return render(request, "admin/AdminProfilePage.html", {'profile': profile})

@login_required
def edit_profile(request):
    user = request.user
    profile = None
    ProfileForm = None

    if user.is_superuser or ((user.user_type == 'admin') or (user.user_type == '1')):
        profile, _ = AdminProfile.objects.get_or_create(username=user)
        ProfileForm = EditAdminForm
    elif user.user_type == 'employee' or user.user_type == '2':
        profile, _ = EmployeeProfile.objects.get_or_create(username=user)
        ProfileForm = EditEmployeeForm
    else:
        return redirect('tasks:home') 

    if request.method == 'POST':
        user_form = ProfileEditForm(request.POST, request.FILES, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            if user.user_type == 'admin' or user.user_type == '1':
                return redirect('tasks:AdminProfilePage')
            elif user.user_type == 'employee' or user.user_type == '2':
                return redirect('tasks:employeeProfilePage')
    else:
        user_form = ProfileEditForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })
       
def login_required_view(request):
    return render(request, 'login_required_view.html')


# .....................................................
# DASHBOARD AND PANEL VIEWS
# ......................................................

def admin_base(request):
    return render(request, "admin/admin_base.html")

@staff_member_required
def AdminDashboard(request):
    # ... (your existing AdminDashboard logic)
    status_list = Task.objects.values_list('status', flat=True)
    status_count = Counter(status_list)
    priority_list = Task.objects.values_list('priority', flat=True)
    priority_count = Counter(priority_list)
    total_tasks = Task.objects.count()

    context = {
        'total_tasks': total_tasks,
        'pending': status_count.get('Pending', 0),
        'inprogress': status_count.get('In Progress', 0),
        'completed': status_count.get('Completed', 0),
        'high': priority_count.get('High', 0),
        'medium': priority_count.get('Medium', 0),
        'low': priority_count.get('Low', 0),
    }

    return render(request, 'admin/AdminDashboard.html', context)

@login_required
def employeeProfilePage(request):
    profile = None
    try:
        profile = request.user.employee.first()
    except EmployeeProfile.DoesNotExist:
        pass
    return render(request, 'employee/employeeProfilePage.html', {'profile': profile})

@login_required
def employeeDashboard(request):
    # ... (your existing employeeDashboard logic)
    user = request.user
    user_tasks = Task.objects.filter(assigned_to=user)
    
    total_tasks = user_tasks.count()
    status_list = user_tasks.values_list('status', flat=True)
    status_count = Counter(status_list)
    priority_list = user_tasks.values_list('priority', flat=True)
    priority_count = Counter(priority_list)

    context = {
        'total_tasks': total_tasks,
        'pending': status_count.get('Pending', 0),
        'inprogress': status_count.get('In Progress', 0),
        'completed': status_count.get('Completed', 0),
        'high': priority_count.get('High', 0),
        'medium': priority_count.get('Medium', 0),
        'low': priority_count.get('Low', 0),
    }

    return render(request, 'employee/employeeDashboard.html', context)


# .....................................................
# NEW VIEWS FOR WORK UPDATES
# ......................................................

@staff_member_required
def work_updates(request):

    update_messages = Message.objects.filter(
        recipient=request.user,
        subject__startswith='Task Updated:'
    ).order_by('-id')

    unread_updates = update_messages.filter(is_read=False)

    if unread_updates.exists():
        unread_updates.update(is_read=True)

    context = {
        'updates': update_messages
    }
    return render(request, 'work_updates.html', context)

@login_required
def work_update_count(request):
    """
    Provides the count of unread work updates for the sidebar badge.
    """
    if not request.user.is_staff:
        return JsonResponse({'update_count': 0})
    
    # Counts unread messages that are specifically work updates
    # This assumes your Message model has an 'is_read' boolean field.
    count = Message.objects.filter(
        recipient=request.user,
        subject__startswith='Task Updated:',
        is_read=False
    ).count()
    
    return JsonResponse({'update_count': count})