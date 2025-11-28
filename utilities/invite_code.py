import secrets
import string

def generate_invite_code(length=8):
    """Generate a random alphanumeric invite code"""
    alphabet = string.ascii_uppercase + string.digits
    # Remove ambiguous characters
    alphabet = alphabet.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))
