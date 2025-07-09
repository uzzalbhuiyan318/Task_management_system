from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import tasks
from .forms import TaskForm
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

# Helper function to convert a task object into a dictionary for JSON
def serialize_task(task):
    """Converts a Task model instance into a JSON-friendly dictionary."""
    priority_class = 'success'
    if task.priority == 'High':
        priority_class = 'danger'
    elif task.priority == 'Medium':
        priority_class = 'warning text-dark'
    
    return {
        'id': task.id,
        'name': task.task_name,
        'description': task.description or "",
        'assigned_to': task.assigned_to,
        'email': task.email,
        'priority': task.priority,
        'priority_class': priority_class,
        'status': task.status,
        'due_date': task.due_date.strftime('%Y-%m-%d'),
        'created_date': task.created_date.strftime('%B %d, %Y, %I:%M %p')
    }
    
    
def task_list(request):
    tasks_list = tasks.objects.all().order_by('-created_date') # Order by most recent

    # --- (All your filter and search logic remains exactly the same here) ---
    search_query = request.GET.get('search', '')
    if search_query:
        tasks_list = tasks_list.filter(Q(task_name__icontains=search_query) | Q(assigned_to__icontains=search_query))
    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks_list = tasks_list.filter(status=status_filter)
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        tasks_list = tasks_list.filter(priority=priority_filter)
        
        
    start_date_filter = request.GET.get('start_date', '')
    end_date_filter = request.GET.get('end_date', '')
    if start_date_filter and end_date_filter:
        tasks_list = tasks_list.filter(due_date__range=[start_date_filter, end_date_filter])

    # Sorting (Bonus)
    sort_by = request.GET.get('sort', 'due_date')
    tasks_list = tasks_list.order_by(sort_by)
    
    paginator = Paginator(tasks_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Add an empty form instance to the context for the modal
    form = TaskForm()

    context = {
        'page_obj': page_obj,
        'form': form # Pass the form to the template
    }
    return render(request, 'task_list.html', context)


def task_create(request):
    """Handles creation of a new task, supporting AJAX."""
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
            if is_ajax(request):
                return JsonResponse({'success': True, 'task': serialize_task(task)})
            return redirect("task_list")
        else:
            if is_ajax(request):
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    # For a non-AJAX invalid form or a GET request, show the full page form
    return render(request, 'task_form.html', {'form': TaskForm()})
    # If GET request, show the form page (for non-JS users or direct access)
    form = TaskForm()
    return render(request, 'task_form.html', {'form': form})


def task_detail(request, pk):
    """Handles viewing a single task, supporting AJAX."""
    task = get_object_or_404(tasks, pk=pk)
    if is_ajax(request):
        # For AJAX requests, return task data as JSON
        return JsonResponse({'success': True, 'task': serialize_task(task)})
    # For regular requests, render the HTML page
    return render(request, 'task_detail.html', {'task': task})

def task_update(request, pk):
    """Handles updating a task, supporting AJAX."""
    task = get_object_or_404(tasks, pk=pk)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save()
            if is_ajax(request):
                return JsonResponse({'success': True, 'task': serialize_task(updated_task)})
            return redirect('task_list')
        else:
            if is_ajax(request):
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    # For a regular GET request
    form = TaskForm(instance=task)
    return render(request, 'task_form.html', {'form': form, 'task': task})

def task_delete(request, pk):
    """Handles deleting a task, supporting AJAX."""
    task = get_object_or_404(tasks, pk=pk)
    if request.method == 'POST':
        task.delete()
        if is_ajax(request):
            return JsonResponse({'success': True})
        return redirect('task_list')
    
    # For a regular GET request
    return render(request, 'task_confirm_delete.html', {'task': task})