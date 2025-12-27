"""Test real Pi-hole connection and save response to HTML file."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import aiohttp
from rich import print
from rich.pretty import pprint


OUTPUT_DIR = Path(__file__).parent / "pihole_output"
OUTPUT_DIR.mkdir(exist_ok=True)


async def test_real_connection(
    host: str = "http://192.168.1.100",
    password: str = "",
    timeout: int = 10
) -> dict:
    """Connect to Pi-hole and save response."""
    host = host.rstrip("/").replace("https://", "").replace("http://", "").strip()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "host": host,
        "auth": {},
        "devices": {},
        "dhcp_leases": {},
    }
    
    timeout_cfg = aiohttp.ClientTimeout(total=timeout, connect=5)
    
    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        # 1. Аутентификация
        print(f"\n[bold]1. Authenticating with Pi-hole at {host}...[/bold]")
        auth_url = f"http://{host}/api/auth"
        auth_payload = {"password": password} if password else {}
        
        async with session.post(auth_url, json=auth_payload) as resp:
            results["auth"]["status"] = resp.status
            results["auth"]["url"] = auth_url
            results["auth"]["payload"] = auth_payload
            
            if resp.status == 200:
                data = await resp.json()
                results["auth"]["response"] = data
                sid = data.get("session", {}).get("sid")
                results["auth"]["sid"] = sid
                print(f"   OK Auth successful, SID: {sid[:16]}...")
            else:
                text = await resp.text()
                results["auth"]["error"] = text
                print(f"   FAIL Auth failed: HTTP {resp.status}")
                return results
            
            headers = {"X-FTL-SID": sid}
        
        # 2. Получение устройств
        print(f"\n[bold]2. Getting network devices...[/bold]")
        devices_url = f"http://{host}/api/network/devices?max_devices=999&max_addresses=24"
        results["devices"]["url"] = devices_url
        results["devices"]["headers"] = {"X-FTL-SID": sid[:16] + "..."}
        
        async with session.get(devices_url, headers=headers) as resp:
            results["devices"]["status"] = resp.status
            if resp.status == 200:
                data = await resp.json()
                results["devices"]["response"] = data
                print(f"   OK Got {len(data.get('clients', []))} devices")
            else:
                text = await resp.text()
                results["devices"]["error"] = text
                print(f"   FAIL: HTTP {resp.status}")
        
        # 3. Получение DHCP leases
        print(f"\n[bold]3. Getting DHCP leases...[/bold]")
        leases_url = f"http://{host}/api/dhcp/leases"
        results["dhcp_leases"]["url"] = leases_url
        
        async with session.get(leases_url, headers=headers) as resp:
            results["dhcp_leases"]["status"] = resp.status
            if resp.status == 200:
                data = await resp.json()
                results["dhcp_leases"]["response"] = data
                print(f"   OK Got DHCP data")
            else:
                text = await resp.text()
                results["dhcp_leases"]["error"] = text
                print(f"   FAIL: HTTP {resp.status}")
    
    return results


def save_to_html(results: dict, filename: str = "pihole_response.html") -> Path:
    """Save API response to HTML file for viewing."""
    
    def status_class(status: int) -> str:
        return "success" if status == 200 else "error"
    
    # Экранируем фигурные скобки для JSON - используем маркеры
    auth_json = json.dumps(results['auth'].get('response', {}), indent=2)
    devices_json = json.dumps(results['devices'].get('response', {}), indent=2)
    leases_json = json.dumps(results['dhcp_leases'].get('response', {}), indent=2)
    full_json = json.dumps(results, indent=2, default=str)
    
    # Заменяем { и } на экранированные версии для HTML
    auth_json = auth_json.replace("{", "&#123;").replace("}", "&#125;")
    devices_json = devices_json.replace("{", "&#123;").replace("}", "&#125;")
    leases_json = leases_json.replace("{", "&#123;").replace("}", "&#125;")
    full_json = full_json.replace("{", "&#123;").replace("}", "&#125;")
    
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pi-hole API Response - {results['host']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1e1e1e; color: #d4d4d4; }}
        h1, h2, h3 {{ color: #569cd6; }}
        pre {{ background: #2d2d2d; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .success {{ color: #4ec9b0; }}
        .error {{ color: #f14c4c; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
        th, td {{ border: 1px solid #3c3c3c; padding: 8px; text-align: left; }}
        th {{ background: #333; }}
    </style>
</head>
<body>
    <h1>Pi-hole API Response</h1>
    <p><strong>Host:</strong> {results['host']}</p>
    <p><strong>Timestamp:</strong> {results['timestamp']}</p>
    
    <div class="section">
        <h2>1. Authentication</h2>
        <p>Status: <span class="{status_class(results['auth']['status'])}">{results['auth']['status']}</span></p>
        <p>SID: <code>{results['auth'].get('sid', 'N/A')}</code></p>
        <h3>Full Response:</h3>
        <pre>{auth_json}</pre>
    </div>
    
    <div class="section">
        <h2>2. Network Devices</h2>
        <p>Status: <span class="{status_class(results['devices']['status'])}">{results['devices']['status']}</span></p>
        <pre>{devices_json}</pre>
    </div>
    
    <div class="section">
        <h2>3. DHCP Leases</h2>
        <p>Status: <span class="{status_class(results['dhcp_leases']['status'])}">{results['dhcp_leases']['status']}</span></p>
        <pre>{leases_json}</pre>
    </div>
    
    <div class="section">
        <h2>Raw JSON (Full Response)</h2>
        <pre>{full_json}</pre>
    </div>
</body>
</html>"""
    
    filepath = OUTPUT_DIR / filename
    filepath.write_text(html, encoding="utf-8")
    print(f"\n[bold green]OK Saved to: {filepath}[/bold green]")
    return filepath


def save_to_json(results: dict, filename: str = "pihole_response.json") -> Path:
    """Save API response to JSON file."""
    filepath = OUTPUT_DIR / filename
    filepath.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"[bold green]OK JSON saved to: {filepath}[/bold green]")
    return filepath


async def main():
    """Run connection test."""
    print("[bold]Pi-hole Connection Test[/bold]")
    print("=" * 50)
    
    # Настройки подключения
    HOST = "http://192.168.1.100"  # Измените на ваш Pi-hole
    PASSWORD = ""  # Ваш пароль, если есть
    
    try:
        results = await test_real_connection(host=HOST, password=PASSWORD)
        
        print("\n" + "=" * 50)
        print("[bold]Summary:[/bold]")
        pprint(results)
        
        save_to_html(results)
        save_to_json(results)
        
        print("\n[bold green]Done![/bold green]")
        
    except Exception as err:
        print(f"[bold red]Error: {err}[/bold red]")
        raise


if __name__ == "__main__":
    asyncio.run(main())