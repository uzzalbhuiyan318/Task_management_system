from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Task
from .forms import TaskForm
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
        'assigned_to': task.assigned_to,
        'email': task.email,
        'priority': task.priority,
        'priority_class': priority_class,
        'status': task.status,
        'due_date': task.due_date.strftime('%Y-%m-%d'),
    }

def task_list(request):
    """ This view renders the main page with the JQGrid structure. """
    form = TaskForm()
    return render(request, 'task_list.html', {'form': form})

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
                task.assigned_to,
                task.email,
                task.priority,
                task.status,
                task.due_date.strftime('%Y-%m-%d'),
                task.id
            ]} for task in paged_tasks
        ]
    }
    return JsonResponse(response)

def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            # if task.email:
            #     task_context = serialize_task(task)
            #     send_email_task.delay(f'New Task: {task.task_name}', task.email, task_context)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False}, status=400)

def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if is_ajax(request):
        return JsonResponse({'success': True, 'task': serialize_task(task)})
    return JsonResponse({'success': False}, status=400)

def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False}, status=400)

def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        task.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)