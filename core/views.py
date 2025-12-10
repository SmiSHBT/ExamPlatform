import json
import os
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse, HttpResponseForbidden, Http404, FileResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.conf import settings
from pathlib import Path
from .models import Test, Result, FocusLog, Screenshot
from .forms import UploadTestForm
from .decorators import auth_required

def index(request):
    return redirect('tests_list')

def user_login(request):
    if request.method=='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('tests_list')
        else:
            return render(request, 'login.html', {'error':'Invalid credentials'})
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@auth_required
def tests_list(request):
    tests = Test.objects.all()
    return render(request, 'tests_list.html', {'tests':tests})

@auth_required
def test_start(request, test_id):
    t = get_object_or_404(Test, pk=test_id)
    r = Result.objects.create(user=request.user, test=t, answers_json='{}', start_time=timezone.now(), finish_time=timezone.now())
    return render(request, 'test_player.html', {'test':t, 'result':r})

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def save_focus(request, test_id):
    if not request.user.is_authenticated:
        return HttpResponseForbidden('auth required')
    if request.method!='POST':
        return JsonResponse({'status':'error','msg':'POST required'})
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'status':'error','msg':'Invalid JSON'})
    result_id = data.get('result_id')
    event_type = data.get('event_type')
    timestamp = data.get('timestamp')
    extra = data.get('extra','')
    try:
        r = Result.objects.get(pk=result_id, user=request.user)
    except Result.DoesNotExist:
        return JsonResponse({'status':'error','msg':'result not found'})
    timestamp_dt = parse_datetime(timestamp) if timestamp else timezone.now()
    if not timestamp_dt:
        timestamp_dt = timezone.now()
    FocusLog.objects.create(result=r, timestamp=timestamp_dt, event_type=event_type, extra=extra)
    loss_events = ['blur', 'visibility_hidden', 'focusout', 'pagehide']
    r.focus_loss_count = r.focus_logs.filter(event_type__in=loss_events).count()
    r.save(update_fields=['focus_loss_count'])
    return JsonResponse({'status':'ok'})

@auth_required
def test_submit(request, test_id):
    if request.method!='POST':
        return HttpResponseForbidden('POST required')
    result_id = request.POST.get('result_id')
    answers = request.POST.get('answers')
    try:
        r = Result.objects.get(pk=result_id, user=request.user)
    except Result.DoesNotExist:
        return HttpResponseForbidden('result not found')
    if r.test_id != test_id:
        return HttpResponseForbidden('result does not match test')
    r.answers_json = answers
    r.finish_time = timezone.now()
    r.save()
    return redirect('/tests/?msg=submit_success')

@user_passes_test(lambda u: u.is_superuser)
def dashboard(request):
    results = Result.objects.select_related('user','test').all().order_by('-created_at')[:50]
    return render(request, 'dashboard.html', {'results':results})

@user_passes_test(lambda u: u.is_superuser)
def upload_test(request):
    if request.method=='POST':
        form = UploadTestForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            f = form.cleaned_data['file']
            if not f.name.lower().endswith(('.html', '.htm')):
                form.add_error('file', 'Only HTML files are allowed')
                return render(request, 'upload_test.html', {'form':form})
            safe_filename = os.path.basename(f.name)
            upload_dir = Path(settings.MEDIA_ROOT) / 'tests_files'
            upload_dir.mkdir(parents=True, exist_ok=True)
            save_path = upload_dir / safe_filename
            with open(save_path, 'wb') as dest:
                for chunk in f.chunks():
                    dest.write(chunk)
            relative_path = os.path.relpath(save_path, settings.BASE_DIR).replace('\\', '/')
            Test.objects.create(title=title, file_path=relative_path)
            return redirect('dashboard')
    else:
        form = UploadTestForm()
    return render(request, 'upload_test.html', {'form':form})

@auth_required
def test_file(request, test_id):
    """Serve test HTML file so it works in production without static hosting issues."""
    t = get_object_or_404(Test, pk=test_id)
    raw_path = t.file_path or ''
    base_dir = Path(settings.BASE_DIR)

    # Resolve absolute path safely
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = (base_dir / raw_path).resolve()
    else:
        candidate = candidate.resolve()

    if not str(candidate).startswith(str(base_dir)):
        return HttpResponseForbidden('Invalid file path')
    if not candidate.exists():
        raise Http404('Test file not found')

    # Force HTML content type for iframe rendering
    return FileResponse(open(candidate, 'rb'), content_type='text/html')

def send_telegram_message(bot_token, chat_id, message, image_path=None):
    if not bot_token or not chat_id:
        print(f"Telegram: Missing bot_token or chat_id. bot_token={bool(bot_token)}, chat_id={bool(chat_id)}")
        return False
    try:
        chat_id = str(chat_id)
        
        if image_path and os.path.exists(image_path):
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': chat_id, 'caption': message}
                response = requests.post(url, files=files, data=data, timeout=10)
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {'chat_id': chat_id, 'text': message}
            response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"Telegram: Message sent successfully")
                return True
            else:
                print(f"Telegram API error: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"Telegram HTTP error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Telegram error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

@csrf_exempt
@auth_required
def save_screenshot(request, test_id):
    if not request.user.is_authenticated:
        return HttpResponseForbidden('auth required')
    if request.method != 'POST':
        return JsonResponse({'status':'error','msg':'POST required'})
    
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'status':'error','msg':'Invalid JSON'})
    
    result_id = data.get('result_id')
    screenshot_data = data.get('screenshot')
    
    try:
        r = Result.objects.get(pk=result_id, user=request.user)
    except Result.DoesNotExist:
        return JsonResponse({'status':'error','msg':'result not found'})
    
    if r.test_id != test_id:
        return JsonResponse({'status':'error','msg':'result does not match test'})
    
    try:
        import base64
        from django.core.files.base import ContentFile
        
        if ',' in screenshot_data:
            format, imgstr = screenshot_data.split(',')
            ext = format.split('/')[-1].split(';')[0]
        else:
            imgstr = screenshot_data
            ext = 'png'
        
        image_data = base64.b64decode(imgstr)
        image_file = ContentFile(image_data, name=f'screenshot_{result_id}_{timezone.now().timestamp()}.{ext}')
        
        screenshots_dir = os.path.join(settings.MEDIA_ROOT, 'screenshots')
        os.makedirs(screenshots_dir, exist_ok=True)
        
        screenshot = Screenshot.objects.create(result=r, image=image_file)
        
        end_time = r.finish_time.strftime('%Y-%m-%d %H:%M:%S') if r.finish_time else 'Not finished'
        message = f"""📸 Screenshot from Test
        
👤 Student: {r.user.username}
📝 Test: {r.test.title}
⏰ End Time: {end_time}
🔴 Focus Loss Count: {r.focus_loss_count}"""
        
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        admin_chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '')
        
        telegram_sent = False
        if bot_token and admin_chat_id:
            try:
                image_path = screenshot.image.path
                print(f"Attempting to send screenshot to Telegram. Image path: {image_path}")
                success = send_telegram_message(bot_token, admin_chat_id, message, image_path)
                if success:
                    screenshot.sent_to_telegram = True
                    screenshot.save()
                    telegram_sent = True
                    print("Screenshot sent to Telegram successfully")
                else:
                    print("Failed to send screenshot to Telegram")
            except Exception as e:
                print(f"Error sending to Telegram: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Telegram not configured: bot_token={bool(bot_token)}, chat_id={bool(admin_chat_id)}")
        
        if telegram_sent:
            return JsonResponse({'status':'ok', 'msg':'Screenshot saved and sent to admin'})
        else:
            return JsonResponse({'status':'ok', 'msg':'Screenshot saved but failed to send to Telegram. Check server logs.'})
    except Exception as e:
        return JsonResponse({'status':'error','msg':f'Error processing screenshot: {str(e)}'})
