#!/usr/bin/env python3
import sys
import json
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from analyzer import analyze_job
import scanner_web

console = Console()

def run_interactive_analysis():
    console.print(Panel.fit(
        "[bold cyan]🔍 Быстрый экспресс-анализ ТЗ / Заказа[/bold cyan]\n"
        "Вставьте текст заказа (из Telegram, Kwork, Авито, FL.ru) и нажмите Enter (для завершения отправьте пустую строку):",
        border_style="cyan"
    ))
    
    lines = []
    while True:
        try:
            line = input()
            if not line and lines:
                break
            lines.append(line)
        except EOFError:
            break
            
    full_text = "\n".join(lines).strip()
    if not full_text:
        console.print("[yellow]Текст не введен.[/yellow]")
        return
        
    analysis = analyze_job(full_text)
    
    if analysis["status"] == "REJECT":
        console.print(Panel(
            f"[bold red]❌ СТОП-ЛИСТ: НЕ БРАТЬ В РАБОТУ[/bold red]\n\n"
            f"[bold]Причина:[/bold] {analysis['reason']}\n\n"
            f"[dim]Слишком высокие риски: старый легаси-код, сомнительные тематики или токсичные условия.[/dim]",
            border_style="red"
        ))
        return

    if analysis["status"] == "SKIP":
        console.print(Panel(
            f"[yellow]⚠️ ЗАДАЧА ВНЕ ФОКУСА[/yellow]\n\n"
            f"{analysis['reason']}",
            border_style="yellow"
        ))
        return

    console.print(Panel(
        f"[bold green]✅ ЗАДАЧА ПОДХОДИТ ДЛЯ РАБОТЫ (Категория: {analysis['category'].upper()})[/bold green]\n"
        f"Оценка уверенности: [bold cyan]{analysis['score']}%[/bold cyan]\n\n"
        f"[bold white]Готовый отклик (скопируйте и отправьте заказчику):[/bold white]\n"
        f"[green]{'-'*50}[/green]\n"
        f"{analysis['proposal']}\n"
        f"[green]{'-'*50}[/green]",
        border_style="green"
    ))

async def run_live_scan():
    console.print("[bold cyan]📡 Сканирование открытых каналов заказов в Telegram...[/bold cyan]")
    leads = await scanner_web.scan_all_channels()
    
    if not leads:
        console.print("[yellow]На данный момент новых свежих постов не найдено, либо проверьте интернет-соединение.[/yellow]")
        return
        
    console.print(f"[bold green]Найдено подходящих заказов: {len(leads)}[/bold green]\n")
    
    for i, lead in enumerate(leads[:10], 1):
        preview = lead["text"][:200].replace("\n", " ") + "..."
        console.print(Panel(
            f"[bold cyan]Заказ #{i} | Категория: {lead['category']} | Источник: @{lead['channel']}[/bold cyan]\n"
            f"🔗 [link={lead['link']}]{lead['link']}[/link]\n\n"
            f"[bold]Описание:[/bold] {preview}\n\n"
            f"[bold green]Сгенерированный отклик:[/bold green]\n{lead['proposal']}",
            border_style="blue"
        ))

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        asyncio.run(run_live_scan())
    else:
        run_interactive_analysis()

if __name__ == "__main__":
    main()
