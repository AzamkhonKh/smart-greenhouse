"""
Create initial admin user for FastAPI Admin
"""

import asyncio
import bcrypt
from tortoise import Tortoise
from tortoise_models import Admin


async def create_admin_user():
    """Create initial admin user"""
    
    # Initialize Tortoise ORM
    await Tortoise.init(
        db_url="postgres://greenhouse_user:greenhouse_pass@localhost:5432/greenhouse",
        modules={"models": ["tortoise_models"]}
    )
    
    # Generate schema if needed
    await Tortoise.generate_schemas()
    
    # Check if admin user already exists
    existing_admin = await Admin.filter(username="admin").first()
    if existing_admin:
        print("Admin user already exists")
        await Tortoise.close_connections()
        return
    
    # Hash password
    password = "admin_password"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create admin user
    admin_user = await Admin.create(
        username="admin",
        password=hashed_password,
        email="admin@greenhouse.local",
        is_active=True,
        is_superuser=True
    )
    
    print(f"Admin user created: {admin_user.username}")
    print(f"Email: {admin_user.email}")
    print(f"Password: {password}")
    
    # Close connections
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(create_admin_user())
