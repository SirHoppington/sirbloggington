from flask import Blueprint, request, abort
import subprocess
from app.User.user_model import User
from app.Subscriber.subscriber_model import Subscriber
from app import db
import hmac
import hashlib
import os 
admin = Blueprint('admin', __name__)


GITHUB_SECRET: str = os.getenv('GITHUB_SECRET', 'PLACEHOLDER')

@admin.route('/github-webhook', methods=['POST'])
def signup_post():

    if request.method == 'POST':
        if not verify_signature(request):
            abort(403)
        data = request.json
        if 'ref' in data and data['ref'] == 'refs/heads/main':
            # Pull the latest code from GitHub
            subprocess.run(['git', 'pull'])
            # Rebuild and restart the Docker containers
            subprocess.run(['docker-compose', 'down'])
            subprocess.run(['docker-compose', 'up', '-d', '--build'])
            return 'Updated successfully', 200
        return 'No action taken', 200
    

def verify_signature(request):
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        return False
    sha_name, signature = signature.split('=')
    if sha_name != 'sha256':
        return False

    mac = hmac.new(GITHUB_SECRET.encode(), msg=request.data, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)