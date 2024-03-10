import queue
import re
import socket
import threading
import requests
import os
import time


from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages

from requests.exceptions import RequestException

# Define allowed wordlists for finding directories
WORDLISTS = {
    'small1k.txt': 'small1k.txt',
    'common4-5k.txt': 'common4-5k.txt',
    'medium20k.txt': 'medium20k.txt',
    'big23k.txt': 'big23k.txt',
    'testing.txt': 'testing.txt',
}

# Define allowed wordlists for scanning subdomains
SUBDOMAIN_WORDLISTS = {
    'subdomains-500.txt': 'subdomains-500.txt',
    'subdomains-1000.txt': 'subdomains-1000.txt',
    'subdomains-5000.txt': 'subdomains-5000.txt',
    'subdomains-10000.txt': 'subdomains-10000.txt',
}

DEFAULT_THREADS = 50
REQUEST_TIMEOUT = 2

def format_size(size_bytes):
    size_kb = size_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.2f} KB"
    size_mb = size_kb / 1024
    if size_mb < 1024:
        return f"{size_mb:.2f} MB"
    size_gb = size_mb / 1024
    if size_gb < 1024:
        return f"{size_gb:.2f} GB"
    size_tb = size_gb / 1024
    return f"{size_tb:.2f} TB"

def is_valid_url(url):
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def is_valid_domain(url):

    regex = re.compile(
        r'^(?!:\/\/)([a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.)+[a-zA-Z]{2,}$'
    )
    return re.match(regex, url) is not None

def home(request):
    return render(request, 'index.html')

def show_directories(request):  
    return render(request, 'directories.html')

def show_subdomains(request):
    return render(request, 'subdomains.html')




def find_directories(request):
    if request.method == 'POST':
        start_time = time.time()
        host = request.POST.get('host')
        threads = int(request.POST.get('threads', DEFAULT_THREADS))
        ext = request.POST.get('ext', '')
        wordlist = request.POST.get('wordlist')

        if not host:
            messages.error(request, "URL is required.")
            return render(request, 'directories.html')
        
        if not is_valid_url(host):
            messages.error(request, "Invalid URL format.")
            return render(request, 'directories.html')

        if not wordlist or wordlist not in WORDLISTS:
            messages.error(request, "Invalid wordlist option.")
            return render(request, 'directories.html')

        wordlist_folder = 'wordlist/'
        wordlist_file = WORDLISTS[wordlist]
        file_path = os.path.join(wordlist_folder, wordlist_file)

        try:
            requests.get(host, timeout=REQUEST_TIMEOUT)
        except RequestException as e:
            return render(request, 'directories.html', {'result': str(e)})

        q = queue.Queue()
        results = []

        def ifast(q):
            session = requests.Session()
            while True:
                url = q.get()
                try:
                    response = session.get(url, allow_redirects=False, timeout=REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        size_bytes = len(response.content)
                        size_formatted = format_size(size_bytes)
                        results.append({'url': url, 'size': size_formatted})
                except RequestException as e:
                    pass
                q.task_done()

        with open(file_path, 'r') as wordlist:
            for word in wordlist.read().splitlines():
                url = f"{host}/{word}"
                if ext:
                    url += ext
                q.put(url)

        for _ in range(threads):
            t = threading.Thread(target=ifast, args=(q,))
            t.daemon = True
            t.start()

        q.join()

        execution_time = time.time() - start_time
        messages.info(request, f"Scan completed in {execution_time:.2f} seconds")
        
        endpoints_count = len(results)
        messages.info(request, f"Found {endpoints_count} endpoints")
        
        return render(request, 'directories.html', {'result': results})
    
    else:
        return render(request, '404.html')

def find_subdomains(request):
    if request.method == 'POST':
        start_time = time.time()
        host = request.POST.get('host', '')
        threads = int(request.POST.get('threads', '1'))
        wordlist = request.POST.get('wordlist')

        if not host:
            messages.error(request, "URL is required.")
            return render(request, 'subdomains.html')
        
        if not is_valid_domain(host):
            messages.error(request, "Invalid domain format.")
            return render(request, 'subdomains.html')

        if not wordlist or wordlist not in SUBDOMAIN_WORDLISTS:
            messages.error(request, "Invalid wordlist option.")
            return render(request, 'subdomains.html')

        wordlist_folder = 'wordlist/'
        wordlist_file = SUBDOMAIN_WORDLISTS[wordlist]
        file_path = os.path.join(wordlist_folder, wordlist_file)

        q = queue.Queue()

        with open(file_path, 'r') as file:
            subdomains = file.read().splitlines()
            for subdomain in subdomains:
                q.put(subdomain)

        results = []

        def subfast():
            nonlocal results
            while not q.empty():
                subdomain = q.get()
                for protocol in ['http', 'https']:  # Check both HTTP and HTTPS
                    url = f"{protocol}://{subdomain}.{host}"
                    try:
                        response = requests.get(url, allow_redirects=False, timeout=REQUEST_TIMEOUT)
                        if response.status_code == 200:
                            # Get IP address of the subdomain
                            ip_address = socket.gethostbyname(f"{subdomain}.{host}")
                            results.append({'url': url, 'ip': ip_address})
                    except (RequestException, socket.gaierror) as e:
                        pass
                q.task_done()

        threads_list = []
        for _ in range(threads):
            t = threading.Thread(target=subfast, daemon=True)
            t.start()
            threads_list.append(t)

        for t in threads_list:
            t.join()

        execution_time = time.time() - start_time
        messages.info(request, f"Subdomain scan completed in {execution_time:.2f} seconds")

        subdomain_count = len(results)
        messages.info(request, f"Found {subdomain_count} subdomains")
        return render(request, 'subdomains.html', {'results': results,
                                                    'subdomain_count': subdomain_count})
    else:
        return render(request, '404.html')
