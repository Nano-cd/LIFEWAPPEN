import datetime
import json
import os
from colorama import Fore, Style, init

# 初始化 colorama
init(autoreset=True)

# --- 系统核心设置 ---
SAVE_FILE = "lifewappen_save.json"

RARITY_COLORS = {
    "普通": Fore.WHITE,
    "稀有": Fore.BLUE,
    "史诗": Fore.MAGENTA,
    "传说": Fore.YELLOW,
}

# --- 类定义 (与之前版本相同) ---
class Badge:
    """定义一个徽章"""
    def __init__(self, name, category, rarity, description, attribute_bonuses=None):
        self.name = name
        self.category = category
        self.rarity = rarity
        self.description = description
        self.attribute_bonuses = attribute_bonuses if attribute_bonuses else {}

    def get_colored_name(self):
        """返回带颜色的徽章名称"""
        color = RARITY_COLORS.get(self.rarity, Fore.WHITE)
        return f"{color}{self.name}{Style.RESET_ALL}"

class LifeWappenProfile:
    """定义人生徽章角色"""
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
            # 如果徽章已经存在，不重复添加日志和属性
            return

        unlock_date = date if date else datetime.date.today().strftime("%Y-%m-%d")
        self.unlocked_badges[badge.name] = {'badge': badge, 'date': unlock_date}
        
        for attr, value in badge.attribute_bonuses.items():
            if attr in self.attributes:
                self.attributes[attr] += value

        log_entry = f"[{unlock_date}] 获得了 {badge.get_colored_name()} 徽章！"
        self.activity_log.insert(0, log_entry)

        if badge.rarity in ["史诗", "传说"]:
            self.title = badge.name
            
    def add_custom_log(self, log_text):
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        self.activity_log.insert(0, f"[{date_str}] {log_text}")

    def display_card(self):
        # ... (显示代码与之前版本完全相同，为简洁省略)
        card_width = 70
        days_survived = self.calculate_days_survived()
        
        def get_display_width(text):
            width = 0
            for char in text:
                if '\u4e00' <= char <= '\u9fff':
                    width += 2
                else:
                    width += 1
            return width
        
        def format_line(left, right=""):
            padding = card_width - 4 - get_display_width(left) - get_display_width(right)
            return f"║ {left}{' ' * padding}{right} ║"

        print(Fore.CYAN + "╔" + "═" * (card_width - 2) + "╗")
        print(Fore.CYAN + format_line(" LIFEWAPPEN 人生徽章成就系统"))
        print(Fore.CYAN + "╠" + "═" * (card_width - 2) + "╣")
        print(Fore.CYAN + format_line(f"ID: {self.name}", f"称号: {self.title}"))
        print(Fore.CYAN + format_line(f"这个角色已存活 {Style.BRIGHT}{days_survived}{Style.NORMAL} 天", f"解锁 {len(self.unlocked_badges)} 枚徽章"))
        print(Fore.CYAN + "╟" + "─" * (card_width - 2) + "╢")
        print(Fore.CYAN + format_line("核心属性:"))
        for attr, value in self.attributes.items():
            bar_len = int(value / 100 * (card_width / 2.5))
            bar = "█" * bar_len + "-" * (int(card_width / 2.5) - bar_len)
            print(Fore.CYAN + format_line(f"  {attr}: [{Fore.GREEN}{bar}{Fore.CYAN}] {value}/100"))
        print(Fore.CYAN + "╟" + "─" * (card_width - 2) + "╢")
        print(Fore.CYAN + format_line("最近动态:"))
        for log in self.activity_log[:4]:
            plain_log = log.replace(Fore.WHITE, "").replace(Fore.BLUE, "").replace(Fore.MAGENTA, "").replace(Fore.YELLOW, "").replace(Style.RESET_ALL, "")
            padding = card_width - 4 - get_display_width(plain_log)
            print(Fore.CYAN + f"║  {log}{' ' * padding}║")
        print(Fore.CYAN + "╚" + "═" * (card_width - 2) + "╝")

# --- 徽章数据库 (与之前版本相同) ---
ALL_BADGES = {
    "日落观赏者": Badge("日落观赏者", "生活体验", "普通", "在一天结束时，静静欣赏了一次完整的日落。", {"心境": 1}),
    "自炊小当家": Badge("自炊小当家", "生存与基础", "稀有", "独立为自己和他人制作一顿包含三菜一汤的晚餐。", {"健康": 2, "魅力": 1}),
    "会议终结者": Badge("会议终结者", "职业与技能", "史诗", "在冗长的会议中，用一句话将讨论拉回正轨并得出结论。", {"智识": 5, "魅力": 3}),
    "第一桶金": Badge("第一桶金", "职业与技能", "稀有", "获得人生的第一笔工资或劳动报酬。", {"智识": 2}),
    "恋爱骑士": Badge("恋爱骑士", "情感与社交", "史诗", "为伴侣完成一件充满挑战但极具意义的浪漫之事。", {"心境": 5, "魅力": 5}),
    "挚友认证": Badge("挚友认证", "情感与社交", "传说", "拥有一位认识超过10年，且在你需要时总会出现的朋友。", {"心境": 10, "魅力": 2}),
    "舒适圈破坏者": Badge("舒适圈破坏者", "挑战与超越", "史诗", "完成一件你一直非常害怕或抗拒的事情。", {"心境": 8, "智识": 2}),
}

# --- 新增：保存和读取函数 ---
def save_profile(profile, filename):
    """将角色数据保存到JSON文件"""
    data_to_save = {
        "name": profile.name,
        "birth_date": profile.birth_date.strftime("%Y-%m-%d"),
        "title": profile.title,
        "attributes": profile.attributes,
        # 只保存已解锁徽章的名称和日期，不保存整个对象
        "unlocked_badges": {name: info['date'] for name, info in profile.unlocked_badges.items()},
        "activity_log": profile.activity_log
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)
    print(f"\n{Fore.GREEN}进度已保存到 {filename}{Style.RESET_ALL}")

def load_or_create_profile(filename, default_name, default_birth_date):
    """从JSON文件加载角色数据，如果文件不存在则创建新角色"""
    if os.path.exists(filename):
        print(f"{Fore.GREEN}检测到存档文件，正在读取进度...{Style.RESET_ALL}\n")
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 创建角色实例并填充数据
        profile = LifeWappenProfile(data["name"], data["birth_date"])
        profile.title = data["title"]
        profile.attributes = data["attributes"]
        profile.activity_log = data["activity_log"]
        
        # 重新构建已解锁的徽章字典
        for badge_name, unlock_date in data["unlocked_badges"].items():
            if badge_name in ALL_BADGES:
                badge_obj = ALL_BADGES[badge_name]
                profile.unlocked_badges[badge_name] = {'badge': badge_obj, 'date': unlock_date}
        return profile
    else:
        print(f"{Fore.YELLOW}未找到存档，正在创建新角色...{Style.RESET_ALL}\n")
        return LifeWappenProfile(default_name, default_birth_date)

# --- 主程序入口 (已更新) ---
if __name__ == "__main__":
    # 1. 尝试加载或创建新角色
    player = load_or_create_profile(SAVE_FILE, "艾利克斯", "1995-08-15")
    
    # 2. 显示当前状态
    print("--- 当前状态 ---")
    player.display_card()
    
    # 3. 可以在这里添加新的操作，比如解锁新徽章
    # 例如，今天你完成了一顿大餐，可以取消下面这行的注释来解锁它
    # player.unlock_badge(ALL_BADGES["自炊小当家"])
    
    # 示例：添加一个自定义日志
    # player.add_custom_log("今天心情很好，去公园散了步。")
    
    # 4. 在所有操作完成后，显示最终卡片
    print("\n--- 最新状态 ---")
    player.display_card()

    # 5. 保存最终的角色状态到文件
    save_profile(player, SAVE_FILE)
