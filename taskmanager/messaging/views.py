from django.shortcuts import render, redirect, get_list_or_404
from .models import Message
from tasks.models import CustomUser
from .forms import MessageForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q


# Create your views here.
@login_required
def inbox(request):
    
    messages = Message.objects.filter(recipient = request.user)
    return render(request, 'messaging/inbox.html', {'messages': messages})


from django.shortcuts import get_object_or_404

@login_required
def message_detail(request, message_id):
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    
    if not message.is_read:
        message.is_read = True
        message.save()
        
    return render(request, 'messaging/message_detail.html', {'message': message})


@login_required
def compose_message(request):
    
    form = MessageForm()
    if request.user.user_type == '1' or request.user.user_type == 'admin':
        form.fields['recipient'].queryset = CustomUser.objects.filter(Q(user_type = '2') | Q(user_type = 'employee'))
    elif request.user.user_type == '2' or request.user.user_type == 'employee':
        form.fields['recipient'].queryset = CustomUser.objects.filter(Q(user_type = '1') | Q(user_type = 'admin'))
        
        
    if request.method == 'POST':
        form = MessageForm(request.POST)
        
        if request.user.user_type == '1' or request.user.user_type == 'admin':
            form.fields['recipient'].queryset = CustomUser.objects.filter(Q(user_type = '2') | Q(user_type ='employee'))
        elif request.user.user_type == '2' or request.user.user_type == 'employee':
            form.fields['recipient'].queryset = CustomUser.objects.filter(Q(user_type = '1') | Q(user_type ='admin'))
            
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return redirect('messaging:inbox')
        

    return render(request, 'messaging/compose_message.html', {'form': form})
        
    