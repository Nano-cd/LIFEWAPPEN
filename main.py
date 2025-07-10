import datetime
import json
import os
import time
import re

# --- 新增导入 ---
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress_bar import ProgressBar
from rich.live import Live
import keyboard  # 用于实时键盘输入

# --- 核心设置 ---
SAVE_FILE = "lifewappen_save.json"

# 使用 Rich 的颜色标记，而不是 Colorama
RARITY_COLORS = {
    "普通": "white",
    "稀有": "cyan",
    "史诗": "magenta",
    "传说": "yellow",
}


# --- 类定义 (Badge 类稍作修改以适应 Rich) ---
class Badge:
    def __init__(self, name, category, rarity, description, attribute_bonuses=None):
        self.name = name
        self.category = category
        self.rarity = rarity
        self.description = description
        self.attribute_bonuses = attribute_bonuses if attribute_bonuses else {}

    def get_rich_name(self):
        """返回适用于 Rich 库的带颜色标记的名称字符串"""
        color = RARITY_COLORS.get(self.rarity, "white")
        return f"[{color}]{self.name}[/]"


# LifeWappenProfile 类几乎无变化，仅修改了日志格式
class LifeWappenProfile:
    def __init__(self, name, birth_date_str):
        self.name = name
        self.birth_date = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        self.title = "新手上路"
        self.attributes = {"健康": 60, "心境": 65, "智识": 70, "魅力": 68}
        self.unlocked_badges = {}
        self.activity_log = []

    def calculate_days_survived(self):
        return (datetime.date.today() - self.birth_date).days

    def unlock_badge(self, badge, date=None):
        if badge.name in self.unlocked_badges:
            return False  # 表示未解锁新徽章
        unlock_date = date if date else datetime.date.today().strftime("%Y-%m-%d")
        self.unlocked_badges[badge.name] = {'badge': badge, 'date': unlock_date}
        for attr, value in badge.attribute_bonuses.items():
            if attr in self.attributes:
                self.attributes[attr] += value
        # 日志现在也使用 Rich 格式
        log_entry = f"[{unlock_date}] 获得了 {badge.get_rich_name()} 徽章！"
        self.activity_log.insert(0, log_entry)
        if badge.rarity in ["史诗", "传说"]:
            self.title = badge.name
        return True  # 表示成功解锁

    def add_custom_log(self, log_text):
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        self.activity_log.insert(0, f"[{date_str}] {log_text}")


# --- 徽章数据库 (无变化) ---
ALL_BADGES = {
    "日落观赏者": Badge("日落观赏者", "生活体验", "普通", "在一天结束时，静静欣赏了一次完整的日落。", {"心境": 1}),
    "自炊小当家": Badge("自炊小当家", "生存与基础", "稀有", "独立为自己和他人制作一顿包含三菜一汤的晚餐。",
                        {"健康": 2, "魅力": 1}),
    "会议终结者": Badge("会议终结者", "职业与技能", "史诗", "在冗长的会议中，用一句话将讨论拉回正轨并得出结论。",
                        {"智识": 5, "魅力": 3}),
    "第一桶金": Badge("第一桶金", "职业与技能", "稀有", "获得人生的第一笔工资或劳动报酬。", {"智识": 2}),
    "恋爱骑士": Badge("恋爱骑士", "情感与社交", "史诗", "为伴侣完成一件充满挑战但极具意义的浪漫之事。",
                      {"心境": 5, "魅力": 5}),
    "挚友认证": Badge("挚友认证", "情感与社交", "传说", "拥有一位认识超过10年，且在你需要时总会出现的朋友。",
                      {"心境": 10, "魅力": 2}),
    "舒适圈破坏者": Badge("舒适圈破坏者", "挑战与超越", "史诗", "完成一件你一直非常害怕或抗拒的事情。",
                          {"心境": 8, "智识": 2}),
}


# --- 保存和读取函数 (基本无变化, 仅调整打印信息) ---
def save_profile(profile, filename):
    data_to_save = {
        "name": profile.name,
        "birth_date": profile.birth_date.strftime("%Y-%m-%d"),
        "title": profile.title,
        "attributes": profile.attributes,
        "unlocked_badges": {name: info['date'] for name, info in profile.unlocked_badges.items()},
        "activity_log": profile.activity_log
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)


def load_or_create_profile(filename, default_name, default_birth_date):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        profile = LifeWappenProfile(data["name"], data["birth_date"])
        profile.title = data["title"]
        profile.attributes = data["attributes"]
        profile.activity_log = data["activity_log"]
        for badge_name, unlock_date in data["unlocked_badges"].items():
            if badge_name in ALL_BADGES:
                badge_obj = ALL_BADGES[badge_name]
                # 在加载时直接调用 unlock_badge 以确保属性等也被正确更新
                profile.unlock_badge(badge_obj, date=unlock_date)
        # 清空初次加载时的日志，因为unlock_badge会生成日志
        profile.activity_log = data.get("activity_log", [])
        return profile
    else:
        return LifeWappenProfile(default_name, default_birth_date)


# ==============================================================================
# --- 全新的可视化界面构建 ---
# ==============================================================================
console = Console()


class GameUI:
    def __init__(self, player):
        self.player = player
        self.app_state = "main_menu"  # 控制当前显示的界面
        self.menu_selection = 0
        self.badge_selection = 0
        self.log_scroll_pos = 0
        self.running = True

    def create_header(self):
        """创建游戏顶部的标题栏"""
        title_text = Text("LIFEWAPPEN - 人生徽章成就系统", justify="center", style="bold cyan")
        return Panel(title_text, border_style="blue")

    def create_footer(self, message):
        """创建游戏底部的操作提示栏，类似游戏对话框"""
        return Panel(Text(message, justify="center"), border_style="green", title="[bold]操作提示[/bold]")

    def create_main_menu_layout(self):
        """创建主菜单界面布局"""
        menu_options = [
            "角色卡片",
            "徽章陈列室",
            "人生足迹",
            "解锁新徽章",
            "保存并退出"
        ]

        menu_text = ""
        for i, option in enumerate(menu_options):
            if i == self.menu_selection:
                menu_text += f"\n[reverse bright_yellow]> {option}[/reverse bright_yellow]"
            else:
                menu_text += f"\n  {option}"

        layout = Layout()
        layout.split(
            Layout(self.create_header(), name="header", size=3),
            # --- 核心修复 ---
            Layout(Panel(Text.from_markup(menu_text, justify="center"), title="主菜单", border_style="magenta"),
                   name="main"),
            Layout(self.create_footer("使用 [↑] [↓] 选择, [Enter] 确认, [Esc] 返回/退出"), name="footer", size=3)
        )
        return layout

    def create_profile_layout(self):
        """创建角色卡片界面布局 (宝可梦训练师卡片风格)"""
        days_survived = self.player.calculate_days_survived()

        # 左侧信息
        # 注意：这里的 .append() 方法默认就会解析 markup，所以它之前就是正确的
        left_content = Text()
        left_content.append(f"ID: {self.player.name}\n", style="bold")
        left_content.append(f"称号: {self.player.title}\n\n", style="italic")
        left_content.append(f"这个角色已存活 [bold green]{days_survived}[/] 天\n")
        left_content.append(f"已解锁 [bold magenta]{len(self.player.unlocked_badges)}[/] 枚徽章\n")

        # 右侧属性
        attr_table = Table.grid(padding=(0, 1))
        attr_table.add_column()
        attr_table.add_column(width=30)
        attr_table.add_column()
        for attr, value in self.player.attributes.items():
            bar = ProgressBar(total=100, completed=value, width=25)
            attr_table.add_row(f"{attr}:", bar, f"[bold green]{value}[/]/100")

        card_table = Table.grid(expand=True)
        card_table.add_column(width=30)
        card_table.add_column()
        card_table.add_row(Panel(left_content, title="[bold]基本信息[/]"), Panel(attr_table, title="[bold]核心属性[/]"))

        layout = Layout()
        layout.split(
            Layout(self.create_header(), name="header", size=3),
            Layout(Panel(card_table, title="角色卡片", border_style="cyan"), name="main"),
            Layout(self.create_footer("按 [Esc] 返回主菜单"), name="footer", size=3)
        )
        return layout

    def create_badge_list_layout(self):
        """创建已解锁徽章列表界面"""
        # 注意：Table.add_row() 也会自动解析 markup，所以它之前也是正确的
        table = Table(title="徽章陈列室", border_style="yellow", expand=True)
        table.add_column("解锁日期", justify="center", style="dim")
        table.add_column("徽章名称", style="bold")
        table.add_column("稀有度", justify="center")
        table.add_column("描述", justify="left")

        unlocked = sorted(self.player.unlocked_badges.values(), key=lambda x: x['date'], reverse=True)

        if not unlocked:
            table.add_row("", "[italic gray50]还没有解锁任何徽章...[/]", "", "")
        else:
            for item in unlocked:
                badge = item['badge']
                color = RARITY_COLORS.get(badge.rarity, "white")
                table.add_row(
                    item['date'],
                    badge.get_rich_name(),
                    f"[{color}]{badge.rarity}[/]",
                    badge.description
                )

        layout = Layout()
        layout.split(
            Layout(self.create_header(), name="header", size=3),
            Layout(table, name="main"),
            Layout(self.create_footer("按 [Esc] 返回主菜单"), name="footer", size=3)
        )
        return layout

    def create_log_view_layout(self):
        """创建人生足迹（活动日志）界面"""
        log_content = "\n".join(self.player.activity_log)

        layout = Layout()
        layout.split(
            Layout(self.create_header(), name="header", size=3),
            # --- 核心修复 ---
            Layout(Panel(Text.from_markup(log_content), title="人生足迹", border_style="green"), name="main"),
            Layout(self.create_footer("按 [Esc] 返回主菜单"), name="footer", size=3)
        )
        return layout

    def create_unlock_badge_layout(self):
        """创建解锁新徽章的选择界面"""
        available_badges = [b for b_name, b in ALL_BADGES.items() if b_name not in self.player.unlocked_badges]

        badge_text = ""
        for i, badge in enumerate(available_badges):
            if i == self.badge_selection:
                prefix = "[reverse bright_yellow]> "
                suffix = "[/reverse bright_yellow]"
            else:
                prefix = "  "
                suffix = ""
            badge_text += f"\n{prefix}{badge.get_rich_name()} - [dim]{badge.description}{suffix}"

        if not available_badges:
            badge_text = "\n[bold red]恭喜！所有徽章均已解锁！[/]"

        layout = Layout()
        layout.split(
            Layout(self.create_header(), name="header", size=3),
            # --- 核心修复 ---
            Layout(Panel(Text.from_markup(badge_text), title="选择要解锁的徽章", border_style="magenta"), name="main"),
            Layout(self.create_footer("使用 [↑] [↓] 选择, [Enter] 解锁, [Esc] 返回"), name="footer", size=3)
        )
        return layout

    def show_dialog(self, message, style="bold green", duration=2):
        """显示一个临时的对话框/消息"""
        with console.capture() as capture:
            pass

        console.print(Panel(Text(message, justify="center", style=style),
                            title="[bold]提示[/bold]",
                            border_style="yellow",
                            width=60), justify="center")
        time.sleep(duration)

    def handle_input(self):
        """处理键盘输入"""
        event = keyboard.read_event(suppress=True)
        if event.event_type == keyboard.KEY_DOWN:
            key = event.name

            # --- 主菜单输入 ---
            if self.app_state == "main_menu":
                if key == "up":
                    self.menu_selection = (self.menu_selection - 1) % 5
                elif key == "down":
                    self.menu_selection = (self.menu_selection + 1) % 5
                elif key == "enter":
                    if self.menu_selection == 0:
                        self.app_state = "profile"
                    elif self.menu_selection == 1:
                        self.app_state = "badge_list"
                    elif self.menu_selection == 2:
                        self.app_state = "log_view"
                    elif self.menu_selection == 3:
                        self.app_state = "unlock_badge"
                        self.badge_selection = 0
                    elif self.menu_selection == 4:
                        save_profile(self.player, SAVE_FILE)
                        self.show_dialog("进度已保存！游戏将在2秒后退出...")
                        self.running = False

            # --- 解锁徽章界面输入 ---
            elif self.app_state == "unlock_badge":
                available_badges = [b for b_name, b in ALL_BADGES.items() if b_name not in self.player.unlocked_badges]
                if available_badges:
                    if key == "up":
                        self.badge_selection = (self.badge_selection - 1) % len(available_badges)
                    elif key == "down":
                        self.badge_selection = (self.badge_selection + 1) % len(available_badges)
                    elif key == "enter":
                        badge_to_unlock = available_badges[self.badge_selection]
                        if self.player.unlock_badge(badge_to_unlock):
                            self.show_dialog(f"🎉 恭喜！解锁了 {badge_to_unlock.get_rich_name()} 徽章！🎉")
                        self.app_state = "main_menu"
                if key == "esc":
                    self.app_state = "main_menu"

            # --- 通用返回逻辑 ---
            elif key == "esc":
                if self.app_state != "main_menu":
                    self.app_state = "main_menu"
                else:
                    self.running = False

    def run(self):
        """主循环，使用 Rich.Live 实时更新界面"""
        with Live(self.create_main_menu_layout(), screen=True, auto_refresh=False) as live:
            while self.running:
                if self.app_state == "main_menu":
                    layout = self.create_main_menu_layout()
                elif self.app_state == "profile":
                    layout = self.create_profile_layout()
                elif self.app_state == "badge_list":
                    layout = self.create_badge_list_layout()
                elif self.app_state == "log_view":
                    layout = self.create_log_view_layout()
                elif self.app_state == "unlock_badge":
                    layout = self.create_unlock_badge_layout()

                live.update(layout, refresh=True)
                self.handle_input()


# --- 主程序入口 ---
if __name__ == "__main__":
    console.print("[bold green]正在加载 LifeWappen 系统...[/]")
    player_profile = load_or_create_profile(SAVE_FILE, "亚瑟", "1993-01-20")

    # 为了演示，如果存档是新创建的，自动解锁一些初始徽章
    if not os.path.exists(SAVE_FILE):
        player_profile.unlock_badge(ALL_BADGES["第一桶金"], date="2016-07-01")
        player_profile.add_custom_log("一段新的人生旅程开始了。")
        save_profile(player_profile, SAVE_FILE)  # 保存初始状态

    try:
        game_ui = GameUI(player_profile)
        game_ui.run()
    except Exception as e:
        # 退出时恢复终端状态，防止终端混乱
        console.print(f"\n[bold red]程序发生错误: {e}[/]")
        console.print("[bold yellow]已退出程序。[/]")
    finally:
        console.print("\n[bold cyan]感谢游玩 LifeWappen！期待与你再次相遇。[/]")
