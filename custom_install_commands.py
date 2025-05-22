import os
import shutil
import inspect
from setuptools.command.install import install

# Common Zephyr paths
ZEPHYR_SCRIPTS_PATH = os.path.join(os.path.expanduser("~"), "zephyrproject/zephyr/scripts/west_commands")
WEST_COMMANDS_YML = os.path.join(os.path.expanduser("~"), "zephyrproject/zephyr/scripts/west-commands.yml")
WEST_COMMANDS_YML_BACKUP = WEST_COMMANDS_YML + ".original"
FLASH_ORIGINAL = os.path.join(ZEPHYR_SCRIPTS_PATH, "flash.py.original")
FLASH_NEW = os.path.join(ZEPHYR_SCRIPTS_PATH, "flash.py")
MONITOR_NEW = os.path.join(ZEPHYR_SCRIPTS_PATH, "monitor.py")

# Helper functions for modularization
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def backup_file(src, backup):
    if os.path.exists(src) and not os.path.exists(backup):
        shutil.copy(src, backup)

def move_file(src, dst):
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.move(src, dst)

def copy_file(src, dst):
    shutil.copy(src, dst)

def append_yaml_monitor(yml_path):
    yaml_content = """
  - file: scripts/west_commands/monitor.py
    commands:
      - name: monitor
        class: Monitor
        help: open a serial monitor (only on linux, depends on picocom)
"""
    if os.path.exists(yml_path):
        with open(yml_path, "a") as yml_file:
            yml_file.write(yaml_content)

def remove_file(path):
    if os.path.exists(path):
        os.remove(path)

# Custom installation script
class CustomInstallCommand(install):
    def run(self):
        install.run(self)
        
        # diretório onde este script está
        current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        
        # caminhos completos para os arquivos fonte
        flash_src = os.path.join(current_dir, "flash.py")
        monitor_src = os.path.join(current_dir, "monitor.py")
        
        print(f"Instalando de: {current_dir}")
        
        ensure_dir(ZEPHYR_SCRIPTS_PATH)
        if os.path.exists(FLASH_ORIGINAL):
            copy_file(flash_src, FLASH_NEW)
            copy_file(monitor_src, MONITOR_NEW)
            return
            
        backup_file(WEST_COMMANDS_YML, WEST_COMMANDS_YML_BACKUP)
        move_file(FLASH_NEW, FLASH_ORIGINAL)
        copy_file(flash_src, FLASH_NEW)
        copy_file(monitor_src, MONITOR_NEW)
        append_yaml_monitor(WEST_COMMANDS_YML)


