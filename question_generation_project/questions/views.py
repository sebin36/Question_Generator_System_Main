from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt
from huggingface_hub import InferenceClient
from django.contrib.auth.decorators import login_required
from .models import QuestionGenerationHistory



def welcome(request):
    if request.user.is_authenticated:
        first_name = request.user.first_name
        last_name = request.user.last_name
    else:
        first_name = None
        last_name = None

    return render(request, 'welcome.html', {
        'first_name': first_name,
        'last_name': last_name,
    })

def user_logout(request):
    logout(request)
    return redirect('welcome')


# Initialize the Hugging Face Inference Client
client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.3", 
    token="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",
)


# Function to generate multiple questions from context
def generate_questions_from_context(context):
    try:
        prompt = f"Generate 10 questions based on the following context:\n\n{context}"
        
        # Generate the response using the Hugging Face model
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        # Extract the generated content from the response
        generated_text = response.choices[0].message["content"]

        # Split the response into individual questions (assuming they are delimited by new lines or periods)
        questions_text = [q.strip() for q in generated_text.split('\n') if q]

        # Replace periods with question marks at the end of each question
        questions = [
            q[:-1] + '?' if q.endswith('.') else q for q in questions_text
        ]
        
        return questions
    
    except Exception as e:
        return [f"An error occurred: {e}"]
    

@login_required
def view_history(request):
    if request.method == 'GET':
        histories = QuestionGenerationHistory.objects.all().order_by('-generated_at')
        
        history_data = []
        for history in histories:
            history_item = {
                'context': history.context,
                'questions': history.questions,
                'generated_at': history.generated_at.isoformat(),
                'url': f"/history/{history.id}/"  # Example URL; adjust as needed
            }
            history_data.append(history_item)
        
        return JsonResponse({'history': history_data})
    
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

# Detailed History View (Optional)
@login_required
def history_detail(request, history_id):
    try:
        history = QuestionGenerationHistory.objects.get(id=history_id)
    except QuestionGenerationHistory.DoesNotExist:
        return JsonResponse({'error': 'History not found.'}, status=404)
    
    history_data = {
        'context': history.context,
        'questions': history.questions,
        'generated_at': history.generated_at.isoformat(),
    }
    
    return JsonResponse({'history': history_data})

@login_required(login_url='/login/')
def generate_questions(request):
    context = ""
    questions = []

    if request.method == 'POST':
        context = request.POST.get('context')
        if context:
            questions = generate_questions_from_context(context)
    
    return render(request, 'questions/generate_questions.html', {'context': context, 'questions': questions})


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        # Check if passwords match
        if password == confirm_password:
            # Check if the username or email already exists
            if User.objects.filter(username=username).exists():
                return render(request, 'register.html', {'error': 'Username already exists.'})
            elif User.objects.filter(email=email).exists():
                return render(request, 'register.html', {'error': 'Email already exists.'})
            else:
                # Create and save the new user
                user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
                user.save()
                messages.success(request, 'Your account has been created successfully.')
                return redirect('login')  # Redirect to the login page after successful registration
        else:
            return render(request, 'questions/register.html', {'error': 'Passwords do not match.'})

    return render(request, 'questions/register.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # If user is valid, log them in and redirect to the question generation page
            login(request, user)
            return redirect('welcome')
        else:
            # If the credentials are invalid, show an error message
            return render(request, 'questions/login.html', {'error': 'Invalid username or password.'})
    
    return render(request, 'questions/login.html')


@login_required
def dashboard(request):
    return render(request, 'questions/dashboard.html')

@login_required
@csrf_exempt
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        # Check if the current password is correct
        if not check_password(current_password, user.password):
            return JsonResponse({'success': False, 'error': 'Current password is incorrect.'})

        # Check if new passwords match
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'error': 'New passwords do not match.'})

        # Update the password
        user.set_password(new_password)
        user.save()

        # Update the session to prevent the user from being logged out
        update_session_auth_hash(request, user)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
@csrf_exempt  # Use CSRF exemption for simplicity; ideally, implement CSRF protection
def profile_details(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')

        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email
        user.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
@csrf_exempt  # Use with caution; better to handle CSRF tokens properly
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')

        # Validate input (optional but recommended)
        if not all([first_name, last_name, username, email]):
            return JsonResponse({'success': False, 'error': 'All fields are required.'})

        # Check if the new username is already taken by another user
        if User.objects.filter(username=username).exclude(pk=user.pk).exists():
            return JsonResponse({'success': False, 'error': 'Username is already taken.'})

        # Check if the new email is already taken by another user
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            return JsonResponse({'success': False, 'error': 'Email is already in use.'})

        # Update user details
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email
        user.save()

        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

