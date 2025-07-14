from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import *
from .forms import TaskForm, TaskEditForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
# from .tasks import send_email_task # Uncomment if you are using Celery

def is_ajax(request):
    """ Helper function to check if the request is an AJAX request """
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

def serialize_task(task):
    """ Helper function to convert a Task object to a dictionary """
    priority_class = 'success'
    if task.priority == 'High':
        priority_class = 'danger'
    elif task.priority == 'Medium':
        priority_class = 'warning text-dark'
    
    return {
        'id': task.id,
        # **FIX:** Changed 'name' to 'task_name' to match JavaScript expectations
        'task_name': task.task_name,
        'description': task.description or "",
        'assigned_to': task.assigned_to.username if task.assigned_to else "N/A",
        'email': task.email,
        'priority': task.priority,
        'priority_class': priority_class,
        'status': task.status,
        'due_date': task.due_date.strftime('%Y-%m-%d'),
    }
    
def home(request):
    return render(request, "home.html")

@login_required
def task_list(request):
    """ This view renders the main page with the JQGrid structure. """
    form = TaskForm()
    return render(request, 'task_list.html', {'form': form})

@login_required
def jqgrid_tasks(request):
    """ This view provides data specifically for the JQGrid plugin. """
    page = int(request.GET.get('page', 1))
    rows = int(request.GET.get('rows', 10))
    
    tasks = Task.objects.all()

    # Filtering logic
    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(Q(task_name__icontains=search_query) | Q(assigned_to__icontains=search_query) | Q(email__icontains=search_query))
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
    
    response = {
        'page': page,
        'total': total_pages,
        'records': total_records,
        'rows': [
            { 'id': task.id, 'cell': [
                task.task_name,
                task.assigned_to.username,
                task.email,
                task.priority,
                task.status,
                task.due_date.strftime('%Y-%m-%d'),
                task.id
            ]} for task in paged_tasks
        ]
    }
    return JsonResponse(response)

@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            # --- Start of Email Sending Logic ---
            subject = f'New Task Assigned: {task.task_name}'

            # Render the HTML template with task context
            html_message = render_to_string('email_notification.html', {'task': task})

            # Create a plain text version of the email for compatibility
            plain_message = strip_tags(html_message)

            from_email = 'uzzalbhuiyan905@gmail.com'
            to_email = task.email 

            if to_email: 
                send_mail(
                    subject,
                    plain_message,
                    from_email,
                    [to_email],
                    html_message=html_message
                )
            # --- End of Email Sending Logic ---
            
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False}, status=400)

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if is_ajax(request):
        return JsonResponse({'success': True, 'task': serialize_task(task)})
    return JsonResponse({'success': False}, status=400)

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        form = TaskEditForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False}, status=400)

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        task.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


def registration(request):
    
    if request.method == 'POST':
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
                username = username,
                email = email,
                password = password,
                user_type= user_type,
                gender = gender,
                age = age,
                contact_no = contact_no,
                profile_pic = profile_pic,
            )
                
            return redirect("tasks:loginPage")
    
    return render(request, "registration.html" )


def loginPage(request):
    if request.method == 'POST':
        user_name = request.POST.get("username")
        pass_word = request.POST.get("password")
        
        try:
            user = authenticate(request, username=user_name, password = pass_word)
            
            if user is not None:
                login(request, user)
                return redirect("tasks:task_list")
            else:
                return redirect("tasks:registration")
        
        except CustomUser.DoesNotExist:
            return redirect("tasks:task_list")
    
    
    return render(request, 'loginPage.html')


def logoutPage(request):
    
    logout(request)
    
    return render(request, "registration.html")



