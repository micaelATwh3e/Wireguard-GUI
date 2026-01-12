import subprocess
import ipaddress
import re
from models import db, User, WireGuardConfig
from config import Config
import qrcode
import io
import base64

class WireGuardManager:
    """Manages WireGuard configuration and user setup"""
    
    @staticmethod
    def get_default_interface():
        """Detect the default network interface"""
        try:
            result = subprocess.check_output(['ip', 'route', 'show', 'default']).decode()
            match = re.search(r'dev\s+(\S+)', result)
            if match:
                return match.group(1)
        except Exception:
            pass
        return Config.WG_NETWORK_INTERFACE
    
    @staticmethod
    def generate_keypair():
        """Generate a WireGuard key pair"""
        try:
            wg_cmd = '/usr/bin/wg'
            private_key = subprocess.check_output([wg_cmd, 'genkey']).decode().strip()
            public_key = subprocess.check_output(
                [wg_cmd, 'pubkey'],
                input=private_key.encode()
            ).decode().strip()
            return private_key, public_key
        except Exception as e:
            raise Exception(f"Failed to generate keys: {e}")
    
    @staticmethod
    def generate_preshared_key():
        """Generate a preshared key for additional security"""
        try:
            wg_cmd = '/usr/bin/wg'
            psk = subprocess.check_output([wg_cmd, 'genpsk']).decode().strip()
            return psk
        except Exception as e:
            raise Exception(f"Failed to generate preshared key: {e}")
    
    @staticmethod
    def get_next_ip():
        """Get the next available IP address"""
        wg_config = WireGuardConfig.query.first()
        if not wg_config:
            raise Exception("WireGuard configuration not initialized")
        
        # Increment last IP
        wg_config.last_ip_assigned += 1
        next_octet = wg_config.last_ip_assigned
        
        # Server IP is .1, so clients start from .2
        if next_octet <= 1:
            next_octet = 2
            wg_config.last_ip_assigned = 2
        
        # Check if we're running out of IPs (assuming /24 subnet)
        if next_octet > 254:
            raise Exception("No more IP addresses available in subnet")
        
        db.session.commit()
        
        # Construct IP from subnet
        network = ipaddress.ip_network(Config.WG_SUBNET)
        ip_address = str(network.network_address + next_octet)
        
        return ip_address
    
    @staticmethod
    def create_user_config(user):
        """Create WireGuard configuration for a user"""
        wg_config = WireGuardConfig.query.first()
        if not wg_config:
            raise Exception("WireGuard server not configured")
        
        # Generate keys for user if not exist
        if not user.wg_private_key or not user.wg_public_key:
            private_key, public_key = WireGuardManager.generate_keypair()
            user.wg_private_key = private_key
            user.wg_public_key = public_key
        
        # Generate preshared key if not exist
        if not user.wg_preshared_key:
            user.wg_preshared_key = WireGuardManager.generate_preshared_key()
        
        # Assign IP if not exist
        if not user.wg_ip_address:
            user.wg_ip_address = WireGuardManager.get_next_ip()
        
        db.session.commit()
        
        # Create client config
        config = f"""[Interface]
PrivateKey = {user.wg_private_key}
Address = {user.wg_ip_address}/32
DNS = {Config.WG_DNS}

[Peer]
PublicKey = {wg_config.server_public_key}
PresharedKey = {user.wg_preshared_key}
Endpoint = {Config.WG_SERVER_PUBLIC_IP}:{Config.WG_SERVER_PORT}
AllowedIPs = {user.wg_allowed_ips}
PersistentKeepalive = 25
"""
        return config
    
    @staticmethod
    def generate_qr_code(config_text):
        """Generate QR code for config"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(config_text)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    
    @staticmethod
    def update_server_config():
        """Update WireGuard server configuration with all active users"""
        wg_config = WireGuardConfig.query.first()
        if not wg_config:
            raise Exception("WireGuard server not configured")
        
        # Get all active users
        users = User.query.filter_by(is_active=True, is_admin=False).all()
        
        # Get default network interface
        net_interface = WireGuardManager.get_default_interface()
        
        # Build server config
        config = f"""[Interface]
Address = {Config.WG_SERVER_IP}/24
ListenPort = {Config.WG_SERVER_PORT}
PrivateKey = {wg_config.server_private_key}
PostUp = iptables -A FORWARD -i {Config.WG_INTERFACE} -j ACCEPT; iptables -t nat -A POSTROUTING -o {net_interface} -j MASQUERADE
PostDown = iptables -D FORWARD -i {Config.WG_INTERFACE} -j ACCEPT; iptables -t nat -D POSTROUTING -o {net_interface} -j MASQUERADE

"""
        
        # Add each user as a peer
        for user in users:
            if user.wg_public_key and user.wg_ip_address:
                config += f"""# {user.username}
[Peer]
PublicKey = {user.wg_public_key}
PresharedKey = {user.wg_preshared_key}
AllowedIPs = {user.wg_ip_address}/32

"""
        
        return config
    
    @staticmethod
    def apply_server_config():
        """Apply the server configuration to WireGuard"""
        try:
            config = WireGuardManager.update_server_config()
            
            # Write to temp file
            config_path = f'/etc/wireguard/{Config.WG_INTERFACE}.conf'
            with open(config_path, 'w') as f:
                f.write(config)
            
            # Restart WireGuard interface
            subprocess.run(['wg-quick', 'down', Config.WG_INTERFACE], 
                         stderr=subprocess.DEVNULL)
            subprocess.run(['wg-quick', 'up', Config.WG_INTERFACE], check=True)
            
            return True
        except Exception as e:
            raise Exception(f"Failed to apply server config: {e}")
