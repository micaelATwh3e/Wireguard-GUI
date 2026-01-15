import subprocess
import ipaddress
import re
from models import db, User, WireGuardConfig, Device
from config import Config
import qrcode
import io
import base64
from datetime import datetime
import time

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
    
    @staticmethod
    def get_peer_statistics():
        """Get statistics for all connected peers"""
        try:
            # Run 'wg show' command to get peer statistics
            result = subprocess.check_output(
                ['wg', 'show', Config.WG_INTERFACE, 'dump'],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            if not result:
                return []
            
            peers = []
            lines = result.split('\n')
            
            # Skip header line (first line is interface info)
            for line in lines[1:]:
                parts = line.split('\t')
                if len(parts) >= 6:
                    public_key = parts[0]
                    preshared_key = parts[1]
                    endpoint = parts[2] if parts[2] != '(none)' else None
                    allowed_ips = parts[3]
                    latest_handshake = int(parts[4]) if parts[4] != '0' else None
                    rx_bytes = int(parts[5])
                    tx_bytes = int(parts[6]) if len(parts) > 6 else 0
                    
                    # Find corresponding user or device
                    device = Device.query.filter_by(wg_public_key=public_key).first()
                    user = None
                    
                    if device:
                        user = device.user
                    else:
                        # Fallback to legacy user config
                        user = User.query.filter_by(wg_public_key=public_key).first()
                    
                    if user or device:
                        # Convert bytes to human readable format
                        def format_bytes(bytes_val):
                            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                                if bytes_val < 1024.0:
                                    return f"{bytes_val:.2f} {unit}"
                                bytes_val /= 1024.0
                            return f"{bytes_val:.2f} PB"
                        
                        # Check if peer is currently connected (handshake within last 3 minutes)
                        is_online = latest_handshake is not None and (time.time() - latest_handshake) < 180
                        
                        peers.append({
                            'username': user.username if user else 'Unknown',
                            'device_name': device.device_name if device else 'Legacy Config',
                            'email': user.email if user else '',
                            'ip_address': device.wg_ip_address if device else (user.wg_ip_address if user else 'N/A'),
                            'public_key': public_key[:16] + '...',  # Truncate for display
                            'endpoint': endpoint,
                            'is_online': is_online,
                            'latest_handshake': latest_handshake,
                            'rx_bytes': rx_bytes,
                            'tx_bytes': tx_bytes,
                            'rx_formatted': format_bytes(rx_bytes),
                            'tx_formatted': format_bytes(tx_bytes),
                            'total_formatted': format_bytes(rx_bytes + tx_bytes)
                        })
            
            return peers
            
        except subprocess.CalledProcessError:
            # Interface might not be up
            return []
        except Exception as e:
            print(f"Error getting peer statistics: {e}")
            return []
    
    @staticmethod
    def create_device_config(user, device_name):
        """Create WireGuard configuration for a specific device"""
        wg_config = WireGuardConfig.query.first()
        if not wg_config:
            raise Exception("WireGuard server not configured")
        
        # Check if user has reached max connections
        active_devices = Device.query.filter_by(user_id=user.id, is_active=True).count()
        if active_devices >= user.max_connections:
            raise Exception(f"User has reached maximum device limit ({user.max_connections})")
        
        # Check if device name already exists for this user
        existing = Device.query.filter_by(user_id=user.id, device_name=device_name).first()
        if existing:
            raise Exception(f"Device '{device_name}' already exists for this user")
        
        # Generate keys for device
        private_key, public_key = WireGuardManager.generate_keypair()
        preshared_key = WireGuardManager.generate_preshared_key()
        ip_address = WireGuardManager.get_next_ip()
        
        # Create device record
        device = Device(
            user_id=user.id,
            device_name=device_name,
            wg_public_key=public_key,
            wg_private_key=private_key,
            wg_preshared_key=preshared_key,
            wg_ip_address=ip_address,
            wg_allowed_ips='0.0.0.0/0',
            is_active=True
        )
        
        db.session.add(device)
        db.session.commit()
        
        # Create client config
        config = f"""[Interface]
PrivateKey = {device.wg_private_key}
Address = {device.wg_ip_address}/32
DNS = {Config.WG_DNS}

[Peer]
PublicKey = {wg_config.server_public_key}
PresharedKey = {device.wg_preshared_key}
Endpoint = {Config.WG_SERVER_PUBLIC_IP}:{Config.WG_SERVER_PORT}
AllowedIPs = {device.wg_allowed_ips}
PersistentKeepalive = 25
"""
        return device, config
    
    @staticmethod
    def get_device_config(device):
        """Get WireGuard configuration for an existing device"""
        wg_config = WireGuardConfig.query.first()
        if not wg_config:
            raise Exception("WireGuard server not configured")
        
        config = f"""[Interface]
PrivateKey = {device.wg_private_key}
Address = {device.wg_ip_address}/32
DNS = {Config.WG_DNS}

[Peer]
PublicKey = {wg_config.server_public_key}
PresharedKey = {device.wg_preshared_key}
Endpoint = {Config.WG_SERVER_PUBLIC_IP}:{Config.WG_SERVER_PORT}
AllowedIPs = {device.wg_allowed_ips}
PersistentKeepalive = 25
"""
        return config
    
    @staticmethod
    def update_server_config_with_devices():
        """Update WireGuard server configuration with all active devices"""
        wg_config = WireGuardConfig.query.first()
        if not wg_config:
            raise Exception("WireGuard server not configured")
        
        # Get all active devices
        devices = Device.query.filter_by(is_active=True).all()
        
        # Also get legacy users (those with wg_public_key but no devices)
        legacy_users = User.query.filter(
            User.is_active == True,
            User.is_admin == False,
            User.wg_public_key.isnot(None),
            ~User.id.in_([d.user_id for d in devices])
        ).all()
        
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
        
        # Add each device as a peer
        for device in devices:
            if device.user.is_active:
                config += f"""# {device.user.username} - {device.device_name}
[Peer]
PublicKey = {device.wg_public_key}
PresharedKey = {device.wg_preshared_key}
AllowedIPs = {device.wg_ip_address}/32

"""
        
        # Add legacy user configs
        for user in legacy_users:
            if user.wg_public_key and user.wg_ip_address:
                config += f"""# {user.username} (Legacy)
[Peer]
PublicKey = {user.wg_public_key}
PresharedKey = {user.wg_preshared_key}
AllowedIPs = {user.wg_ip_address}/32

"""
        
        return config
    
    @staticmethod
    def apply_server_config_with_devices():
        """Apply the server configuration to WireGuard with device support"""
        try:
            config = WireGuardManager.update_server_config_with_devices()
            
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
    
    @staticmethod
    def update_device_connection_status():
        """Update connection status for all devices based on WireGuard stats"""
        try:
            result = subprocess.check_output(
                ['wg', 'show', Config.WG_INTERFACE, 'dump'],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            if not result:
                # No peers connected, mark all as disconnected
                Device.query.update({Device.is_connected: False})
                db.session.commit()
                return
            
            connected_keys = set()
            lines = result.split('\n')
            
            # Skip header line
            for line in lines[1:]:
                parts = line.split('\t')
                if len(parts) >= 5:
                    public_key = parts[0]
                    latest_handshake = int(parts[4]) if parts[4] != '0' else None
                    
                    # Check if handshake is recent (within 3 minutes)
                    if latest_handshake and (time.time() - latest_handshake) < 180:
                        connected_keys.add(public_key)
                        
                        # Update device
                        device = Device.query.filter_by(wg_public_key=public_key).first()
                        if device:
                            device.is_connected = True
                            device.last_handshake = datetime.fromtimestamp(latest_handshake)
            
            # Mark disconnected devices
            all_devices = Device.query.all()
            for device in all_devices:
                if device.wg_public_key not in connected_keys:
                    device.is_connected = False
            
            db.session.commit()
            
        except Exception as e:
            print(f"Error updating device connection status: {e}")
    
    @staticmethod
    def get_user_connected_device_count(user_id):
        """Get count of currently connected devices for a user"""
        WireGuardManager.update_device_connection_status()
        return Device.query.filter_by(user_id=user_id, is_connected=True).count()
