#!/usr/bin/env python3
"""
Простой скрипт для проверки состояния API
"""
import httpx
import asyncio

async def check_api():
    """Проверяем состояние API"""
    base_url = "https://kyrsach-0x7m.onrender.com"
    
    print("Проверка API...")
    
    async with httpx.AsyncClient() as client:
        # Проверяем основные эндпоинты
        endpoints = [
            "/api/categories",
            "/api/events", 
            "/api/direct-categories",
            "/api/direct-events",
            "/api-test"
        ]
        
        for endpoint in endpoints:
            try:
                response = await client.get(f"{base_url}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code != 200:
                    print(f"  Ошибка: {response.text[:200]}")
            except Exception as e:
                print(f"{endpoint}: Ошибка запроса - {e}")
        
        # Проверяем конкретное событие
        try:
            response = await client.get(f"{base_url}/api/events/1")
            print(f"/api/events/1: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Событие: {data.get('title', 'N/A')}")
        except Exception as e:
            print(f"/api/events/1: Ошибка запроса - {e}")

if __name__ == "__main__":
    asyncio.run(check_api()) 