"""
Update Security Group to Allow Your Current IP

This script adds your current public IP to the security group
so you can access MLflow from your current network.
"""

import boto3
import requests
from dotenv import load_dotenv

load_dotenv()

def update_security_group_for_my_ip():
    """Add current IP to security group for port 5000 access"""
    
    print("\n" + "="*70)
    print("🔒 Updating Security Group for Your Current IP")
    print("="*70)
    
    # Get current public IP
    print("\n📍 Getting your current public IP...")
    try:
        my_ip = requests.get('https://api.ipify.org').text
        print(f"   Your current IP: {my_ip}")
    except Exception as e:
        print(f"   ❌ Error getting IP: {e}")
        return
    
    # Connect to EC2
    ec2 = boto3.client('ec2', region_name='me-central-1')
    
    # Find the instance
    print("\n🔍 Finding your instance...")
    response = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    
    if not response['Reservations']:
        print("❌ No running instances found")
        return
    
    instance = response['Reservations'][0]['Instances'][0]
    public_ip = instance.get('PublicIpAddress')
    sg_id = instance['SecurityGroups'][0]['GroupId']
    
    print(f"   Instance IP: {public_ip}")
    print(f"   Security Group: {sg_id}")
    
    # Add rule for port 5000 from current IP
    print(f"\n🔧 Adding rule for port 5000 from your IP...")
    try:
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                'IpProtocol': 'tcp',
                'FromPort': 5000,
                'ToPort': 5000,
                'IpRanges': [{'CidrIp': f'{my_ip}/32', 'Description': f'MLflow UI from {my_ip}'}]
            }]
        )
        print(f"   ✅ Rule added successfully!")
    except Exception as e:
        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
            print(f"   ℹ️  Rule already exists for your IP")
        else:
            print(f"   ❌ Error: {e}")
            return
    
    # Also add SSH if needed
    print(f"\n🔧 Adding rule for SSH (port 22) from your IP...")
    try:
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': f'{my_ip}/32', 'Description': f'SSH from {my_ip}'}]
            }]
        )
        print(f"   ✅ SSH rule added successfully!")
    except Exception as e:
        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
            print(f"   ℹ️  SSH rule already exists for your IP")
        else:
            print(f"   ⚠️  Note: {e}")
    
    print(f"\n" + "="*70)
    print("✅ Security Group Updated!")
    print("="*70)
    print(f"\n🌐 Try accessing MLflow now: http://{public_ip}:5000")
    print(f"🔑 SSH access: ssh -i ./pem_keys/mlflow_instance_me_central_1.pem ubuntu@{public_ip}")
    print(f"\n💡 Note: If you change networks, run this script again")
    print("="*70 + "\n")


if __name__ == "__main__":
    update_security_group_for_my_ip()
