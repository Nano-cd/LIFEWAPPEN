import datetime
from colorama import Fore, Style, init

# 初始化 colorama，让颜色在所有终端都能正常工作
init(autoreset=True)

# --- 系统核心设置 ---

# 徽章稀有度颜色映射
RARITY_COLORS = {
    "普通": Fore.WHITE,
    "稀有": Fore.BLUE,
    "史诗": Fore.MAGENTA,
    "传说": Fore.YELLOW,
}

# --- 类定义 ---

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
        
        # 核心属性
        self.attributes = {
            "健康": 60,
            "心境": 65,
            "智识": 70,
            "魅力": 68,
        }
        
        self.unlocked_badges = {} # 存储解锁的徽章和日期: {'徽章名': {'badge': Badge_obj, 'date': '...'} }
        self.activity_log = [] # 记录最近的活动

    def calculate_days_survived(self):
        """计算存活天数"""
        return (datetime.date.today() - self.birth_date).days

    def unlock_badge(self, badge, date=None):
        """解锁一个新徽章"""
        if badge.name in self.unlocked_badges:
            print(f"提示：你已经解锁过【{badge.name}】了。")
            return

        unlock_date = date if date else datetime.date.today().strftime("%Y-%m-%d")
        self.unlocked_badges[badge.name] = {'badge': badge, 'date': unlock_date}
        
        # 更新属性
        for attr, value in badge.attribute_bonuses.items():
            if attr in self.attributes:
                self.attributes[attr] += value

        # 更新日志
        log_entry = f"[{unlock_date}] 获得了 {badge.get_colored_name()} 徽章！"
        self.activity_log.insert(0, log_entry) # 插入到最前面

        # 更新称号 (简单逻辑：基于最新获得的史诗或传说徽章)
        if badge.rarity in ["史诗", "传说"]:
            self.title = badge.name
            
    def add_custom_log(self, log_text):
        """添加自定义的日志条目"""
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        self.activity_log.insert(0, f"[{date_str}] {log_text}")


    def display_card(self):
        """在终端打印出角色ID卡片"""
        card_width = 70
        days_survived = self.calculate_days_survived()
        
        # --- 辅助函数，处理中英文对齐 ---
        def get_display_width(text):
            width = 0
            for char in text:
                if '\u4e00' <= char <= '\u9fff': # 判断是否为中文字符
                    width += 2
                else:
                    width += 1
            return width
        
        def format_line(left, right=""):
            padding = card_width - 4 - get_display_width(left) - get_display_width(right)
            return f"║ {left}{' ' * padding}{right} ║"

        # --- 开始打印卡片 ---
        print(Fore.CYAN + "╔" + "═" * (card_width - 2) + "╗")
        print(Fore.CYAN + format_line(f" LIFEWAPPEN 人生徽章成就系统"))
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
        for log in self.activity_log[:4]: # 最多显示最近4条
            # 移除颜色代码来计算真实宽度
            plain_log = log.replace(Fore.WHITE, "").replace(Fore.BLUE, "").replace(Fore.MAGENTA, "").replace(Fore.YELLOW, "").replace(Style.RESET_ALL, "")
            padding = card_width - 4 - get_display_width(plain_log)
            print(Fore.CYAN + f"║  {log}{' ' * padding}║")

        print(Fore.CYAN + "╚" + "═" * (card_width - 2) + "╝")


# --- 徽章数据库 ---
ALL_BADGES = {
    # 生存与基础
    "日落观赏者": Badge("日落观赏者", "生活体验", "普通", "在一天结束时，静静欣赏了一次完整的日落。", {"心境": 1}),
    "自炊小当家": Badge("自炊小当家", "生存与基础", "稀有", "独立为自己和他人制作一顿包含三菜一汤的晚餐。", {"健康": 2, "魅力": 1}),
    # 职业与技能
    "会议终结者": Badge("会议终结者", "职业与技能", "史诗", "在冗长的会议中，用一句话将讨论拉回正轨并得出结论。", {"智识": 5, "魅力": 3}),
    "第一桶金": Badge("第一桶金", "职业与技能", "稀有", "获得人生的第一笔工资或劳动报酬。", {"智识": 2}),
    # 情感与社交
    "恋爱骑士": Badge("恋爱骑士", "情感与社交", "史诗", "为伴侣完成一件充满挑战但极具意义的浪漫之事。", {"心境": 5, "魅力": 5}),
    "挚友认证": Badge("挚友认证", "情感与社交", "传说", "拥有一位认识超过10年，且在你需要时总会出现的朋友。", {"心境": 10, "魅力": 2}),
    # 挑战与超越
    "舒适圈破坏者": Badge("舒适圈破坏者", "挑战与超越", "史诗", "完成一件你一直非常害怕或抗拒的事情。", {"心境": 8, "智识": 2}),
}


# --- 主程序入口 ---
if __name__ == "__main__":
    # 1. 创建你的角色档案 (修改这里的名字和生日)
    player = LifeWappenProfile("艾利克斯", "1995-08-15")

    # 2. 解锁你的成就！
    player.unlock_badge(ALL_BADGES["第一桶金"], date="2018-07-01")
    player.unlock_badge(ALL_BADGES["日落观赏者"])
    player.unlock_badge(ALL_BADGES["会议终结者"])
    player.unlock_badge(ALL_BADGES["恋爱骑士"])
    player.unlock_badge(ALL_BADGES["舒适圈破坏者"])
    
    # 3. 添加一些自定义的记录
    player.add_custom_log("累计解锁 158 次日落观赏成就")

    # 4. 显示你的最终ID卡片
    player.display_card()
