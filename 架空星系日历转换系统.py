from datetime import datetime, timedelta
import math

# 天文常数和日历配置
EARTH_YEAR_DAYS = 365.2564
B_YEAR_DAYS = 438.3077
RATIO_SCHEME1 = B_YEAR_DAYS / EARTH_YEAR_DAYS
B_MONTHS = 18
BASE_MONTH_DAYS = {m: 25 if m % 3 == 0 else 24 for m in range(1, B_MONTHS+1)}
WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

class AdvancedCalendarConverter:
    def __init__(self):
        self.earth_epoch = datetime(1, 1, 1)
        self.b_epoch_weekday = 0  # 行星B元年1月1日为星期一

    def get_b_calendar(self, year):
        """生成行星B年份日历（含闰日规则）"""
        leap_day = 1 if year % 3 == 0 else 0
        calendar = []
        for month in range(1, B_MONTHS+1):
            days = BASE_MONTH_DAYS[month]
            if month == 1:
                days += leap_day
            calendar.append((month, days))
        return calendar

    def validate_earth_datetime(self, datetime_str):
        """验证地球日期时间合法性"""
        try:
            # 尝试解析日期时间
            parts = datetime_str.split()
            date_part = parts[0]
            
            # 验证日期部分
            dt_date = datetime.strptime(date_part, "%Y-%m-%d")
            if not (1 <= dt_date.year <= 9999):
                return False
            
            # 验证时间部分（如果存在）
            if len(parts) > 1:
                time_part = parts[1]
                time_parts = time_part.split(':')
                if len(time_parts) != 3:
                    return False
                hour, minute, second = map(int, time_parts)
                if hour < 0 or hour > 23 or minute < 0 or minute > 59 or second < 0 or second > 59:
                    return False
            
            return True
        except:
            return False

    def validate_b_datetime(self, datetime_str):
        """验证行星B日期时间合法性"""
        try:
            # 分离日期和时间部分
            parts = datetime_str.split()
            date_part = parts[0]
            
            # 验证日期部分
            if len(date_part) != 10 or date_part[4] != '-' or date_part[7] != '-':
                return False
            year = int(date_part[:4])
            month = int(date_part[5:7])
            day = int(date_part[8:10])
            if month < 1 or month > 18 or day < 1:
                return False
            
            calendar = self.get_b_calendar(year)
            if day > calendar[month-1][1]:
                return False
            
            # 验证时间部分（如果存在）
            if len(parts) > 1:
                time_part = parts[1]
                time_parts = time_part.split(':')
                if len(time_parts) != 3:
                    return False
                hour, minute, second = map(int, time_parts)
                if hour < 0 or hour > 23 or minute < 0 or minute > 59 or second < 0 or second > 59:
                    return False
            
            return True
        except:
            return False

    def b_datetime_to_seconds(self, b_datetime_str):
        """行星B日期时间转总秒数"""
        # 分离日期和时间部分
        parts = b_datetime_str.split()
        date_part = parts[0]
        time_part = parts[1] if len(parts) > 1 else "00:00:00"
        
        # 解析时间部分
        hour, minute, second = map(int, time_part.split(':'))
        
        # 计算日期部分的总天数
        year, month, day = map(int, date_part.split('-'))
        total_days = 0
        for y in range(1, year):
            calendar = self.get_b_calendar(y)
            total_days += sum(days for _, days in calendar)
        calendar = self.get_b_calendar(year)
        for m in range(1, month):
            total_days += calendar[m-1][1]
        total_days += day - 1
        
        # 转换为总秒数
        total_seconds = total_days * 86400 + hour * 3600 + minute * 60 + second
        return total_seconds

    def get_b_weekday(self, b_date_str):
        """获取行星B日期的星期"""
        # 只使用日期部分计算星期
        parts = b_date_str.split()
        date_part = parts[0]
        total_days = self.b_datetime_to_seconds(f"{date_part} 00:00:00") // 86400
        return WEEKDAYS[(self.b_epoch_weekday + total_days) % 7]

    def get_earth_weekday(self, datetime_str):
        """获取地球日期的星期"""
        # 只使用日期部分计算星期
        parts = datetime_str.split()
        date_part = parts[0]
        dt = datetime.strptime(date_part, "%Y-%m-%d")
        return WEEKDAYS[dt.weekday()]

    def days_to_b_date(self, total_days):
        """总天数转行星B日期（带星期）"""
        year = 1
        while True:
            calendar = self.get_b_calendar(year)
            year_days = sum(days for _, days in calendar)
            if total_days < year_days:
                break
            total_days -= year_days
            year += 1
        
        for month, days in calendar:
            if total_days < days:
                date_str = f"{year:04d}-{month:02d}-{int(total_days)+1:02d}"
                return f"{date_str} {self.get_b_weekday(date_str)}"
            total_days -= days
        raise ValueError("天数转换异常")

    def scheme1_earth_to_b(self, earth_datetime):
        """方案一：地球→行星B（年内比例）"""
        try:
            # 解析日期时间
            parts = earth_datetime.split()
            date_part = parts[0]
            time_part = parts[1] if len(parts) > 1 else "00:00:00"
            
            dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
            
            year_start = datetime(dt.year, 1, 1)
            delta = dt - year_start
            # 计算年内经过的秒数
            earth_seconds = delta.total_seconds()
            # 转换为行星B时间
            b_seconds = earth_seconds * RATIO_SCHEME1
            # 转换为天数
            b_days = round(b_seconds / 86400)
            return self.days_to_b_date_by_year(dt.year, b_days)
        except Exception as e:
            return f"转换失败：{str(e)}"

    def days_to_b_date_by_year(self, year, days):
        """指定年份的天数转换"""
        calendar = self.get_b_calendar(year)
        total = 0
        for month, month_days in calendar:
            total += month_days
            if days <= total:
                day = days - (total - month_days)
                date_str = f"{year:04d}-{month:02d}-{int(day):02d}"
                return f"{date_str} {self.get_b_weekday(date_str)}"
        raise ValueError("超出年份天数范围")

    def scheme1_b_to_earth(self, b_datetime):
        """方案一：行星B→地球（年内比例）"""
        try:
            # 分离日期部分
            parts = b_datetime.split()
            date_part = parts[0]
            
            year, month, day = map(int, date_part.split('-'))
            calendar = self.get_b_calendar(year)
            b_days = sum(md for _, md in calendar[:month-1]) + day
            earth_days = round(b_days / RATIO_SCHEME1)
            
            try:
                base_date = datetime(year, 1, 1)
                target_date = base_date + timedelta(days=earth_days-1)
                if target_date.year != year:
                    return f"{year:04d}-12-31 {self.get_earth_weekday(f'{year}-12-31')}"
                return f"{target_date.strftime('%Y-%m-%d')} {self.get_earth_weekday(target_date.strftime('%Y-%m-%d'))}"
            except ValueError:
                return f"{year:04d}-12-31 {self.get_earth_weekday(f'{year}-12-31')}"
        except Exception as e:
            return f"转换失败：{str(e)}"

    def scheme2_earth_to_b(self, earth_datetime):
        """方案二：地球→行星B（绝对天数）"""
        try:
            # 解析日期时间
            parts = earth_datetime.split()
            date_part = parts[0]
            time_part = parts[1] if len(parts) > 1 else "00:00:00"
            
            dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
            
            delta = dt - self.earth_epoch
            total_days = delta.days
            return self.days_to_b_date(total_days)
        except Exception as e:
            return f"转换失败：{str(e)}"

    def scheme2_b_to_earth(self, b_datetime):
        """方案二：行星B→地球（绝对天数）"""
        try:
            total_seconds = self.b_datetime_to_seconds(b_datetime)
            total_days = total_seconds // 86400
            target_date = self.earth_epoch + timedelta(days=total_days)
            return f"{target_date.strftime('%Y-%m-%d')} {self.get_earth_weekday(target_date.strftime('%Y-%m-%d'))}"
        except OverflowError:
            return "超出公元历法范围"
        except Exception as e:
            return f"转换失败：{str(e)}"
            
    def calculate_interval(self, start_datetime, end_datetime, is_b_calendar=False, output_calendar=None):
        """
        计算两个日期之间的间隔（日期级别）
        :param start_datetime: 起始日期 (YYYY-MM-DD)
        :param end_datetime: 结束日期 (YYYY-MM-DD)
        :param is_b_calendar: 输入是否为行星B日历
        :param output_calendar: 输出日历类型 ('earth' 或 'b')，为None时使用输入日历
        :return: 包含多种间隔表示的字典
        """
        # 只取日期部分
        start_date = start_datetime.split()[0] if ' ' in start_datetime else start_datetime
        end_date = end_datetime.split()[0] if ' ' in end_datetime else end_datetime
        
        # 计算总秒数间隔
        if is_b_calendar:
            # 行星B日期转总天数
            start_days = self.b_date_to_days(start_date)
            end_days = self.b_date_to_days(end_date)
            total_days = end_days - start_days
            total_seconds = total_days * 86400
        else:
            # 地球日期转datetime对象
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            delta = end_dt - start_dt
            total_days = delta.days
            total_seconds = total_days * 86400
        
        # 确定输出日历类型
        if output_calendar is None:
            output_calendar = 'b' if is_b_calendar else 'earth'
        
        # 计算并返回各种间隔表示
        return {
            'total_days': total_days,
            'detailed_interval': self.get_detailed_interval(total_seconds, output_calendar),
            'time_interval': self.get_time_interval(total_seconds),
            'total_hours': total_seconds / 3600.0
        }
        
    def calculate_precise_interval(self, start_datetime, end_datetime, is_b_calendar=False, output_calendar=None):
        """
        计算两个日期时间之间的精确间隔（支持时分秒）
        :param start_datetime: 起始日期时间 (YYYY-MM-DD [HH:MM:SS])
        :param end_datetime: 结束日期时间 (YYYY-MM-DD [HH:MM:SS])
        :param is_b_calendar: 输入是否为行星B日历
        :param output_calendar: 输出日历类型 ('earth' 或 'b')，为None时使用输入日历
        :return: 包含多种间隔表示的字典
        """
        # 计算总秒数间隔
        if is_b_calendar:
            # 行星B日期时间转总秒数
            start_seconds = self.b_datetime_to_seconds(start_datetime)
            end_seconds = self.b_datetime_to_seconds(end_datetime)
        else:
            # 地球日期时间转总秒数
            start_dt = self.parse_earth_datetime(start_datetime)
            end_dt = self.parse_earth_datetime(end_datetime)
            start_seconds = (start_dt - self.earth_epoch).total_seconds()
            end_seconds = (end_dt - self.earth_epoch).total_seconds()
        
        total_seconds = end_seconds - start_seconds
        
        # 确定输出日历类型
        if output_calendar is None:
            output_calendar = 'b' if is_b_calendar else 'earth'
        
        # 计算并返回各种间隔表示
        return {
            'total_days': total_seconds / 86400.0,
            'detailed_interval': self.get_detailed_interval(total_seconds, output_calendar),
            'time_interval': self.get_time_interval(total_seconds),
            'total_hours': total_seconds / 3600.0
        }
    
    def b_date_to_days(self, b_date_str):
        """行星B日期转总天数"""
        # 只取日期部分
        b_date_str = b_date_str.split()[0] if ' ' in b_date_str else b_date_str
        
        year, month, day = map(int, b_date_str.split('-'))
        total_days = 0
        # 累计往年天数
        for y in range(1, year):
            calendar = self.get_b_calendar(y)
            total_days += sum(days for _, days in calendar)
        # 处理当年天数
        calendar = self.get_b_calendar(year)
        for m in range(1, month):
            total_days += calendar[m-1][1]
        total_days += day - 1
        return total_days
    
    def parse_earth_datetime(self, datetime_str):
        """解析地球日期时间字符串"""
        parts = datetime_str.split()
        if len(parts) > 1:
            return datetime.strptime(f"{parts[0]} {parts[1]}", "%Y-%m-%d %H:%M:%S")
        else:
            return datetime.strptime(datetime_str, "%Y-%m-%d")
    
    def get_detailed_interval(self, total_seconds, calendar_type):
        """
        获取详细的年/月/周/日/时/分/秒间隔
        :param total_seconds: 总秒数
        :param calendar_type: 日历类型 ('earth' 或 'b')
        :return: 格式化的字符串
        """
        # 计算总天数（含小数）
        total_days = total_seconds / 86400.0
        
        # 根据日历类型设置年、月长度
        if calendar_type == 'b':
            year_days = B_YEAR_DAYS
            month_days = year_days / B_MONTHS
        else:  # earth
            year_days = EARTH_YEAR_DAYS
            month_days = year_days / 12
        
        # 计算年、月、周、日（整数部分）
        years = int(total_days // year_days)
        remaining_days = total_days % year_days
        
        months = int(remaining_days // month_days)
        remaining_days = remaining_days % month_days
        
        weeks = int(remaining_days // 7)
        days = int(remaining_days % 7)
        
        # 计算剩余时间（小数部分）的时、分、秒
        fractional_day = remaining_days - int(remaining_days)
        fractional_seconds = fractional_day * 86400
        
        hours = int(fractional_seconds // 3600)
        minutes = int((fractional_seconds % 3600) // 60)
        seconds = int(fractional_seconds % 60)
        
        # 格式化输出
        return (f"{years:02d}年{months:02d}月{weeks:02d}周"
                f"{days:02d}日{hours:02d}时{minutes:02d}分{seconds:02d}秒")
    
    def get_time_interval(self, total_seconds):
        """
        获取时/分/秒间隔（总小时数，可超过24小时）
        :param total_seconds: 总秒数
        :return: 格式化的字符串
        """
        # 计算总小时数
        total_hours = total_seconds / 3600.0
        
        # 计算完整小时数
        hours = int(total_hours)
        # 计算剩余分钟数
        fractional_hours = total_hours - hours
        minutes = int(fractional_hours * 60)
        # 计算剩余秒数
        fractional_minutes = fractional_hours * 60 - minutes
        seconds = int(fractional_minutes * 60)
        
        # 格式化输出
        return f"{hours:02d}时{minutes:02d}分{seconds:02d}秒"


def main():
    converter = AdvancedCalendarConverter()
    print("星际日历转换系统（增强版）")
    print("="*40)
    print("支持功能：")
    print("1. 计算星期 → 输入: w [e|b] [日期]")
    print("2. 方案一转换(年内比例) → 输入: s1 [e|b] [日期]")
    print("3. 方案二转换(绝对天数) → 输入: s2 [e|b] [日期]")
    print("4. 日期间隔计算（日期级别） → 输入: i [e|b] [起始日期] [终止日期] [输出日历(e|b)]")
    print("5. 精确日期间隔计算（支持时分秒） → 输入: i5 [e|b] [起始日期时间] [终止日期时间] [输出日历(e|b)]")
    print("退出请输入 exit")
    print("\n日期时间格式说明：")
    print("- 日期和时间用空格分隔，例如：2023-01-01 08:00:00")
    print("- 如果只提供日期，时间默认为00:00:00")
    print("- 行星B日期格式：0001-01-01，月份范围1-18，日期范围根据月份变化")
    print("\n简化输入说明：")
    print("e = earth, b = b, w = weekday, s1 = scheme1, s2 = scheme2, i = interval, i5 = interval5")
    print("间隔计算可指定输出日历（可选参数）：")
    print("  i e 2023-01-01 2023-12-31 → 使用地球日历输出")
    print("  i e 2023-01-01 2023-12-31 b → 使用行星B日历输出")
    print("  i5 e 2023-01-01 08:00:00 2023-01-02 18:30:15 → 精确计算地球日期间隔")
    print("  i5 b 0001-01-01 00:00:00 0001-01-02 12:30:45 e → 精确计算行星B日期间隔并输出为地球日历格式")

    while True:
        user_input = input("\n> ").strip()
        if user_input.lower() in ('exit', 'quit'):
            break

        # 分割输入，允许空格分隔日期和时间
        parts = []
        current_part = []
        in_quote = False
        
        for char in user_input:
            if char == '"' or char == "'":
                in_quote = not in_quote
            elif char == ' ' and not in_quote:
                if current_part:
                    parts.append(''.join(current_part))
                    current_part = []
            else:
                current_part.append(char)
        
        if current_part:
            parts.append(''.join(current_part))
        
        if not parts:
            continue
            
        try:
            # 映射简化命令
            cmd_map = {
                'w': 'weekday',
                's1': 'scheme1',
                's2': 'scheme2',
                'i': 'interval',
                'i5': 'interval5'
            }
            
            # 映射日历类型
            cal_map = {
                'e': 'earth',
                'b': 'b'
            }
            
            command = cmd_map.get(parts[0].lower(), parts[0].lower())
            calendar_type = cal_map.get(parts[1].lower(), parts[1].lower()) if len(parts) > 1 else None
            
            # 计算星期模式
            if command == 'weekday' and len(parts) >= 3:
                datetime_str = parts[2]
                if calendar_type == 'earth':
                    if converter.validate_earth_datetime(datetime_str):
                        weekday = converter.get_earth_weekday(datetime_str)
                        print(f"🌍 {datetime_str} 是 {weekday}")
                    else:
                        print("错误：无效的地球日期时间")
                elif calendar_type == 'b':
                    if converter.validate_b_datetime(datetime_str):
                        weekday = converter.get_b_weekday(datetime_str)
                        print(f"🪐 {datetime_str} 是 {weekday}")
                    else:
                        print("错误：无效的行星B日期时间")
                else:
                    print("错误：请指定日历类型 (e 或 b)")
            
            # 转换模式
            elif command in ('scheme1', 'scheme2') and len(parts) >= 3:
                datetime_str = parts[2]
                if calendar_type == 'earth':
                    if not converter.validate_earth_datetime(datetime_str):
                        print("错误：无效的地球日期时间")
                        continue
                    if command == 'scheme1':
                        result = converter.scheme1_earth_to_b(datetime_str)
                        print(f"方案一转换：🌍 → 🪐\n{datetime_str} → {result}")
                    else:
                        result = converter.scheme2_earth_to_b(datetime_str)
                        print(f"方案二转换：🌍 → 🪐\n{datetime_str} → {result}")
                elif calendar_type == 'b':
                    if not converter.validate_b_datetime(datetime_str):
                        print("错误：无效的行星B日期时间")
                        continue
                    if command == 'scheme1':
                        result = converter.scheme1_b_to_earth(datetime_str)
                        print(f"方案一转换：🪐 → 🌍\n{datetime_str} → {result}")
                    else:
                        result = converter.scheme2_b_to_earth(datetime_str)
                        print(f"方案二转换：🪐 → 🌍\n{datetime_str} → {result}")
                else:
                    print("错误：请指定日历类型 (e 或 b)")
            
            # 日期间隔计算（功能4 - 日期级别）
            elif command == 'interval' and len(parts) >= 4:
                start_datetime = parts[2]
                end_datetime = parts[3]
                output_calendar = cal_map.get(parts[4].lower(), parts[4].lower()) if len(parts) > 4 else None
                
                if calendar_type == 'earth':
                    if not (converter.validate_earth_datetime(start_datetime) and 
                            converter.validate_earth_datetime(end_datetime)):
                        print("错误：无效的地球日期时间")
                        continue
                    
                    # 计算并显示间隔
                    interval = converter.calculate_interval(start_datetime, end_datetime, False, output_c极endar)
                    print(f"🌍 地球日期间隔: {start_datetime} 到 {end_datetime}")
                    self_calendar = output_calendar if output_calendar else 'earth'
                    
                    print(f"1. 总天数: {interval['total_days']} 天")
                    print(f"2. {self_calendar}日历分解: {interval['detailed_interval']}")
                    print(f"3. 时间间隔: {interval['time_interval']} (总小时数)")
                    print(f"4. 总小时数: {interval['total_hours']:.2f} 小时")
                    
                    # 同时显示对方日历的分解
                    other_calendar = 'b' if self_calendar == 'earth' else 'earth'
                    other_interval = converter.calculate_interval(
                        start_datetime, end_datetime, False, other_calendar)
                    print(f"\n{other_calendar}日历分解: {other_interval['detailed_interval']}")
                
                elif calendar_type == 'b':
                    if not (converter.validate_b_datetime(start_datetime) and 
                            converter.validate_b_datetime(end_datetime)):
                        print("错误：无效的行星B日期时间")
                        continue
                    
                    # 计算并显示间隔
                    interval = converter.calculate_interval(start_datetime, end_datetime, True, output_calendar)
                    print(f"🪐 行星B日期间隔: {start_datetime} 到 {end_datetime}")
                    self_calendar = output_calendar if output_calendar else 'b'
                    
                    print(f"1. 总天数: {interval['total_days']} 天")
                    print(f"2. {极lf_calendar}日历分解: {interval['detailed_interval']}")
                    print(f"3. 时间间隔: {interval['time_interval']} (总小时数)")
                    print(f"4. 总小时数: {interval['total_hours']:.2f} 小时")
                    
                    # 同时显示对方日历的分解
                    other_calendar = 'earth' if self_calendar == 'b' else 'b'
                    other_interval = converter.calculate_interval(
                        start_datetime, end_datetime, True, other_calendar)
                    print(f"\n{other_calendar}日历分解: {other_interval['detailed_interval']}")
                else:
                    print("错误：请指定日历类型 (e 或 b)")
            
            # 精确日期间隔计算（功能5 - 支持时分秒）
            elif command == 'interval5' and len(parts) >= 4:
                start_datetime = parts[2]
                end_datetime = parts[3]
                output_calendar = cal_map.get(parts[4].lower(), parts[4].lower()) if len(parts) > 4 else None
                
                if calendar_type == 'earth':
                    if not (converter.validate_earth_datetime(start_datetime) and 
                            converter.validate_earth_datetime(end_datetime)):
                        print("错误：无效的地球日期时间")
                        continue
                    
                    # 计算并显示间隔
                    interval = converter.calculate_precise_interval(start_datetime, end_datetime, False, output_calendar)
                    print(f"🌍 地球精确日期间隔: {start_datetime} 到 {end_datetime}")
                    self_calendar = output_calendar if output_calendar else 'earth'
                    
                    print(f"1. 总天数: {interval['total_days']:.6f} 天")
                    print(f"2. {self_calendar}日历分解: {interval['detailed_interval']}")
                    print(f"3. 时间间隔: {interval['time_interval']} (总小时数)")
                    print(f"4. 总小时数: {interval['total_hours']:.2极} 小时")
                    
                    # 同时显示对方日历的分解
                    other_calendar = 'b' if self_calendar == 'earth' else 'earth'
                    other_interval = converter.calculate_precise_interval(
                        start_datetime, end_datetime, False, other_calendar)
                    print(f"\n{other_calendar}日历分解: {other_interval['detailed_interval']}")
                
                elif calendar_type == 'b':
                    if not (converter.validate_b_datetime(start_datetime) and 
                            converter.validate_b_datetime(end_datetime)):
                        print("错误：无效的行星B日期时间")
                        continue
                    
                    # 计算并显示间隔
                    interval = converter.calculate_precise_interval(start_datetime, end_datetime, True, output_calendar)
                    print(f"🪐 行星B精确日期间隔: {start_datetime} 到 {end_datetime}")
                    self_calendar = output_calendar if output_calendar else 'b'
                    
                    print(f"1. 总天数: {interval['total_days']:.6f} 天")
                    print(f"2. {self_calendar}日历分解: {interval['detailed_interval']}")
                    print(f"3. 时间间隔: {interval['time_interval']} (总小时数)")
                    print(f"4. 总小时数: {interval['total_hours']:.2f} 小时")
                    
                    # 同时显示对方日历的分解
                    other_calendar = 'earth' if self_calendar == 'b' else 'b'
                    other_interval = converter.calculate_precise_interval(
                        start_datetime, end_datetime, True, other_calendar)
                    print(f"\n{other_calendar}日历分解: {other_interval['detailed_interval']}")
                else:
                    print("错误：请指定日历类型 (e 或 b)")
            
            else:
                print("未知指令，请输入帮助信息中的有效指令")

        except Exception as e:
            print(f"处理出错：{str(e)}")

    print("程序已退出")

if __name__ == "__main__":
    main()
