from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from collections import Counter
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from .models import *
from .forms import *
from messaging.models import Message
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Case, When, IntegerField
# from .tasks import send_email_task # Uncomment if you are using Celery

# The above disables false positives for Django model dynamic attributes (objects, _meta, DoesNotExist, etc.)

def is_ajax(request):
    """ Helper function to check if the request is an AJAX request """
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

def add_priority_sorting(queryset):

    return queryset.annotate(
        priority_order=Case(
            When(priority='High', then=1),
            When(priority='Medium', then=2),
            When(priority='Low', then=3),
            default=4,
            output_field=IntegerField()
        )
    )

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
        'due_date': task.due_date.strftime('%Y-%m-%d'),  # 📅 FIXED: YYYY-MM-DD format for HTML5 date inputs
        'due_date_display': task.due_date.strftime('%d-%m-%Y'),  # For display purposes
        'comment': task.comment or "",
        'upload': task.upload.url if task.upload else None,
    }
    
def home(request):
    # If user is already logged in, redirect them to their appropriate dashboard
    if request.user.is_authenticated:
        if request.user.user_type in ['admin', '1']:
            return redirect("tasks:AdminDashboard")
        elif request.user.user_type in ['employee', '2']:
            return redirect("tasks:employeeDashboard")
    
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

    # � TASK RETRIEVAL WITH PRIORITY SORTING: Get tasks with proper priority ordering
    if request.user.is_authenticated and (
        request.user.user_type == '2' or str(request.user.user_type).lower() == 'employee'
    ):
        # For employees: Show only their assigned tasks, sorted by priority then due date (earliest first)
        tasks = add_priority_sorting(Task.objects.filter(assigned_to=request.user)).order_by('priority_order', 'due_date')
    else:
        # For admins: Show all tasks with priority sorting then due date (earliest first)
        tasks = add_priority_sorting(Task.objects.all()).order_by('priority_order', 'due_date')

    form = TaskForm()

    # � EMPLOYEE TASK SEEN TRACKING: Mark employee tasks as seen
    if request.user.is_authenticated and (
        request.user.user_type == '2' or str(request.user.user_type).lower() == 'employee'
    ):
        Task.objects.filter(
            assigned_to=request.user,
            employee_seen=False
        ).update(employee_seen=True)

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
    rows = int(request.GET.get('rows', 15))

    # � PRIORITY SORTING SETUP: Add priority ordering annotation
    tasks = add_priority_sorting(Task.objects.all())

    # � EMPLOYEE FILTERING: Only show tasks assigned to employee
    if request.user.user_type == '2' or request.user.user_type == 'employee':
        tasks = tasks.filter(assigned_to=request.user)

    # � SEARCH FILTERING: Search by task name, assignee, or email
    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(Q(task_name__icontains=search_query) | Q(assigned_to__username__icontains=search_query) | Q(email__icontains=search_query))

    # � STATUS FILTERING: Filter by task status
    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    # � PRIORITY FILTERING: Filter by task priority
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    # � SORTING LOGIC: Enhanced with priority sorting
    sidx = request.GET.get('sidx', 'priority_order')  # Default to priority sorting
    sord = request.GET.get('sord', 'asc')  # Ascending for priority (High=1, Medium=2, Low=3)

    if sidx == 'priority':
        # If sorting by priority, use our custom priority_order field
        sidx = 'priority_order'

    if sidx:
        order = f'-{sidx}' if sord == 'desc' else sidx
        # Always add secondary sort by creation date for consistent ordering
        if sidx == 'priority_order':
            tasks = tasks.order_by(order, 'due_date')
        else:
            tasks = tasks.order_by(order)
    else:
        # Default sorting: Priority first, then by due date (earliest first)
        tasks = tasks.order_by('priority_order', 'due_date')

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
             # 📅 DATE FORMAT: YYYY-MM-DD for JQGrid table display or JG Grid Row
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
def task_create(request):
    """Handles the creation of a new task via an AJAX POST request."""
    if request.method == 'POST':
        # Debug: Print form data to console
        print("📝 Task Creation Debug:")
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")

        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save()
            print(f"✅ Task created successfully: {task.task_name}")

            # Email notification (with error handling)
            try:
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
                from_email = settings.EMAIL_HOST_USER
                to_email = task.email

                if to_email:
                    send_mail(
                        subject,
                        plain_message,
                        from_email,
                        [to_email],
                        html_message=html_message
                    )
                    print(f"📧 Email sent to: {to_email}")
            except Exception as e:
                print(f"⚠️ Email sending failed: {e}")
                # Don't fail task creation if email fails

            return JsonResponse({'success': True})
        else:
            print(f"❌ Form validation errors: {form.errors}")
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@login_required
def get_employee_email(request, employee_id):
    """Get employee email by ID for auto-populating email field"""
    if is_ajax(request):
        try:
            employee = CustomUser.objects.get(id=employee_id, user_type__in=['employee', '2'])
            return JsonResponse({
                'success': True, 
                'email': employee.email,
                'username': employee.username
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Employee not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

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
    if not (request.user.user_type == 'admin' or request.user.user_type == '1' or task.assigned_to == request.user):
        raise PermissionDenied
    if request.method == "POST":
        # Debug: Print form data to console
        print(f"📝 Task Update Debug for Task ID {pk}:")
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        
        form = TaskEditForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            updated_task = form.save()
            print(f"✅ Task updated successfully: {updated_task.task_name}")
            return JsonResponse({'success': True})
        else:
            print(f"❌ TaskEditForm validation errors: {form.errors}")
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False}, status=400)

@login_required
def update_task_status(request, pk):

    if not is_ajax(request) or request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

    task = get_object_or_404(Task, pk=pk)

    if task.assigned_to != request.user and not (request.user.user_type == 'admin' or request.user.user_type == '1'):
        raise PermissionDenied

    new_status = request.POST.get('status')
    comment = request.POST.get('comment', '')

    if not new_status:
        return JsonResponse({'success': False, 'error': 'Status not provided'}, status=400)

    # Store the previous status
    previous_status = task.status

    # Create a WorkUpdate record for admin review
    work_update = WorkUpdate.objects.create(
        task=task,
        employee=request.user,
        previous_status=previous_status,
        new_status=new_status,
        employee_comment=comment,
        review_status='pending'
    )

    # If the user is an admin, auto-approve the update
    if request.user.user_type == 'admin' or request.user.user_type == '1':
        work_update.review_status = 'approved'
        work_update.reviewed_by = request.user
        work_update.reviewed_at = timezone.now()
        work_update.save()
        
        # Apply the changes to the task
        task.status = new_status
        task.comment = comment
        task.save()
    else:
        # For employees: temporarily apply the change (will be reverted if rejected)
        task.status = new_status
        task.comment = comment
        task.save()

    return JsonResponse({'success': True})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not (request.user.user_type == 'admin' or request.user.user_type == '1'):
        raise PermissionDenied
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

        import re
        errors = []

        if not username:
            errors.append("Username is required.")
        if not email:
            errors.append("Email is required.")
        else:
            # Basic email format validation
            email_regex = r'^([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+)\.([a-zA-Z0-9-.]+)$'
            if not re.match(email_regex, email):
                errors.append("Please enter a valid email address.")

        if not password:
            errors.append("Password is required.")

        # Check password match only if both provided
        if password and confirm_password and password != confirm_password:
            errors.append("Password and Confirm Password do not match.")
        if password and len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if password and not any(char.isdigit() for char in password):
            errors.append("Password must contain at least one digit.")
        if password and not any(char.isalpha() for char in password):
            errors.append("Password must contain at least one letter.")
        if password and not any(char in '!@#$%^&*()_+-=[]{};:\'",.<>?/`~' for char in password):
            errors.append("Password must contain at least one special character.")
        if password and not any(char.isupper() for char in password):
            errors.append("Password must contain at least one uppercase letter.")
            
        # Age veryfication
        if age:
            try:
                age = int(age)
                if age < 15 or age > 70:
                    errors.append("Age must be between 15 and 70.")
            except ValueError: 
                errors.append("Age must be a valid number.")

        # Contact number validation: if provided, it must be exactly 11 digits
        if contact_no:
            # allow digits only (basic check)
            digits = ''.join(filter(str.isdigit, contact_no))
            if len(digits) != 11:
                errors.append("Contact number must be 11 digits.")
        else:
            errors.append("Contact number is required.")
            

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, "registration.html")
            
        user = CustomUser.objects.create_user(
                username = username, email = email, password = password,
                user_type= user_type, gender = gender, age = age,       
                contact_no = contact_no, profile_pic = profile_pic,
                ) 
        if user_type == 'employee':
            EmployeeProfile.objects.create(username=user)
        elif user_type == 'admin':
            AdminProfile.objects.create(username=user)
        
        messages.success(request, "Account created successfully! Please login.")
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
                
                # Check for admin user (handle both string and numeric types)
                if user.is_authenticated and (user.user_type == 'admin' or user.user_type == '1'):
                    return redirect("tasks:AdminDashboard")
                # Check for employee user (handle both string and numeric types)
                elif user.is_authenticated and (user.user_type == 'employee' or user.user_type == '2'):
                    return redirect("tasks:employeeDashboard")
                else:
                    # If user type is not recognized, default to employee dashboard for safety
                    return redirect("tasks:employeeDashboard")
            else:
                messages.error(request, 'Invalid username or password. Please try again.')
                return render(request, 'loginPage.html')
        except Exception as e:
            messages.error(request, 'An error occurred during login. Please try again.')
            return render(request, 'loginPage.html')
    
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

# admin dashboard logic here

@staff_member_required
@login_required
def AdminDashboard(request):
    # � BASIC COUNTS: Get total tasks and employees (no filtering)
    total_tasks = Task.objects.count()
    total_employees = CustomUser.objects.filter(user_type='employee').count()

    # � STATUS FILTERING: Count tasks by status for dashboard widgets
    pending = Task.objects.filter(status='Pending').count()
    inprogress = Task.objects.filter(status='In Progress').count()
    completed = Task.objects.filter(status='Completed').count()

    # � PRIORITY FILTERING: Count tasks by priority for dashboard charts
    high_priority = Task.objects.filter(priority='High').count()
    medium_priority = Task.objects.filter(priority='Medium').count()
    low_priority = Task.objects.filter(priority='Low').count()

    # Employee performance statistics
    employees_with_tasks = CustomUser.objects.filter(
        user_type='employee',
        Task__isnull=False
    ).distinct().count()

    # Recent activity (tasks created in last 7 days)
    from datetime import datetime, timedelta
    last_week = datetime.now() - timedelta(days=7)
    recent_tasks = Task.objects.filter(created_date__gte=last_week).count()

    # 📅 OVERDUE DATE FILTERING: Find tasks past due date for dashboard statistics
    from datetime import date
    overdue_tasks = Task.objects.filter(
        due_date__lt=date.today(),  # 📅 DATE COMPARISON: Tasks with due_date before today
        status__in=['Pending', 'In Progress']
    ).count()

    # Work updates pending review
    pending_reviews = WorkUpdate.objects.filter(review_status='pending').count()

    context = {
        'total_tasks': total_tasks,
        'total_employees': total_employees,
        'pending': pending,
        'inprogress': inprogress,
        'completed': completed,
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'low_priority': low_priority,
        'employees_with_tasks': employees_with_tasks,
        'recent_tasks': recent_tasks,
        'overdue_tasks': overdue_tasks,
        'pending_reviews': pending_reviews,
    }
    return render(request, 'admin/AdminDashboard.html', context)

@login_required
@login_required
def employeeProfilePage(request):
    profile = None
    try:
        # Try to get the employee profile
        profile = request.user.employee.first()
    except (EmployeeProfile.DoesNotExist, AttributeError):
        # If profile doesn't exist, create one
        if request.user.user_type in ['employee', '2']:
            profile = EmployeeProfile.objects.create(username=request.user)
        else:
            profile = None
    
    return render(request, 'employee/employeeProfilePage.html', {'profile': profile})

@login_required
def employeeDashboard(request):
    user = request.user

    # � EMPLOYEE TASK FILTERING WITH PRIORITY SORTING: Get only current employee's assigned tasks
    user_tasks = add_priority_sorting(Task.objects.filter(assigned_to=user)).order_by('priority_order', '-due_date')

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
        'user_tasks': user_tasks,  # Add sorted tasks to context for display
    }

    return render(request, 'employee/employeeDashboard.html', context)


# .....................................................
# NEW VIEWS FOR WORK UPDATES
# ......................................................

@login_required
def work_updates(request):
    if not (request.user.user_type == 'admin' or request.user.user_type == '1'):
        return redirect('tasks:home')

    # � CHRONOLOGICAL FILTERING: Get all work updates ordered by newest first
    updates = WorkUpdate.objects.all().order_by('-created_at')

    context = {
        'work_updates': updates
    }
    return render(request, 'work_updates.html', context)

@login_required
def work_update_count(request):
    """
    Provides the count of new/unseen work updates for admin notification badge.
    """
    if request.user.user_type == 'admin' or request.user.user_type == '1':
        # Admin: count pending work updates needing review
        count = WorkUpdate.objects.filter(review_status='pending').count()
    elif request.user.user_type == 'employee' or request.user.user_type == '2':
        # Employee: count reviewed work updates not yet seen by employee
        count = WorkUpdate.objects.filter(
            employee=request.user,
            review_status__in=['approved', 'rejected'],
            employee_seen=False
        ).count()
    else:
        count = 0
    
    return JsonResponse({'update_count': count})


@login_required
def task_notification_count(request):
    """
    Provides the count of new/unseen tasks for employee notification badge.
    Only for employees - shows count of tasks assigned but not yet seen.
    """
    if request.user.user_type == 'employee' or request.user.user_type == '2':
        # Employee: count unseen tasks assigned to them
        count = Task.objects.filter(
            assigned_to=request.user,
            employee_seen=False
        ).count()
    else:
        # Admins don't need task notifications, they create tasks
        count = 0

    return JsonResponse({'task_count': count})





@login_required
def approve_work_update(request, update_id):
    """
    Approve a work update and confirm the status change to the task
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    work_update = get_object_or_404(WorkUpdate, id=update_id)
    admin_reply = request.POST.get('admin_reply', '')
    
    # Update the work update record
    work_update.review_status = 'approved'
    work_update.reviewed_by = request.user
    work_update.admin_reply = admin_reply
    work_update.reviewed_at = timezone.now()
    work_update.employee_seen = False  # Employee needs to see the admin's decision
    work_update.save()
    
    # Ensure the task status reflects the approved change
    task = work_update.task
    task.status = work_update.new_status
    if work_update.employee_comment:
        task.comment = work_update.employee_comment
    task.save()
    
    return JsonResponse({'success': True, 'message': 'Work update approved successfully'})


@login_required
def reject_work_update(request, update_id):
    """
    Reject a work update and revert task to its previous status
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    work_update = get_object_or_404(WorkUpdate, id=update_id)
    admin_reply = request.POST.get('admin_reply', '')
    
    # Update the work update record
    work_update.review_status = 'rejected'
    work_update.reviewed_by = request.user
    work_update.admin_reply = admin_reply
    work_update.reviewed_at = timezone.now()
    work_update.employee_seen = False  # Employee needs to see the admin's decision
    work_update.save()
    
    # Revert the task to its previous status
    task = work_update.task
    if work_update.previous_status:
        task.status = work_update.previous_status
        task.save()
    
    return JsonResponse({'success': True, 'message': 'Work update rejected and task reverted to previous status'})

@login_required
def employee_work_updates(request):
    """
    Display work updates submitted by the current employee with admin responses
    """
    work_updates = WorkUpdate.objects.filter(
        employee=request.user
    ).select_related('task', 'reviewed_by').order_by('-created_at')

    # Mark all reviewed updates as seen by the employee
    WorkUpdate.objects.filter(
        employee=request.user,
        review_status__in=['approved', 'rejected'],
        employee_seen=False
    ).update(employee_seen=True)

    context = {
        'work_updates': work_updates
    }
    return render(request, 'employee/employee_work_updates.html', context)


@login_required
def mark_work_update_seen(request, update_id):
    """
    Mark a specific work update as seen by the employee
    """
    if request.method == 'POST':
        try:
            work_update = get_object_or_404(WorkUpdate, id=update_id, employee=request.user)
            work_update.employee_seen = True
            work_update.save()
            return JsonResponse({'success': True, 'message': 'Work update marked as seen'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def mark_task_seen(request, task_id):
    """
    Mark a specific task as seen by the employee
    """
    if request.method == 'POST':
        try:
            task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
            task.employee_seen = True
            task.save()
            return JsonResponse({'success': True, 'message': 'Task marked as seen'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def aboutUs(request):
    return render(request, 'aboutUs.html')



# Contact Message logic start here
def contactPage(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                message=message
            )
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('tasks:contactPage')
        else:
            messages.error(request, 'Please fill in all required fields.')

    return render(request, 'contactPage.html')


@login_required
def all_contact_messages(request):
    """Display all contact messages for admin"""
    messages = ContactMessage.objects.all().order_by('-timestamp')
    
    # Mark all messages as read when admin views them
    ContactMessage.objects.filter(is_read=False).update(is_read=True)
    
    context = {
        'contact_messages': messages
    }
    return render(request, 'admin/contact_messages.html', context)


@login_required
def mark_message_read(request, message_id):
    """Mark a specific contact message as read"""
    if request.method == 'POST':
        try:
            message = ContactMessage.objects.get(id=message_id)
            message.is_read = True
            message.save()
            return JsonResponse({'success': True})
        except ContactMessage.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def contact_message_count(request):
    """API endpoint to get unread contact message count for notification badge"""
    if request.user.user_type == 'admin':
        unread_count = ContactMessage.objects.filter(is_read=False).count()
        return JsonResponse({'unread_count': unread_count})
    return JsonResponse({'unread_count': 0})


def formHandler(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if name and email and message:
            testForm.objects.create(
                name=name,
                email=email,
                message=message
            )
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('tasks:home')
        else:
            messages.error(request, 'Please fill in all required fields.')

    return render(request, 'formHandler.html')