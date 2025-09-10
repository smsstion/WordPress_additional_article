import re
import math

class BackToMainMenu(Exception):
    """自定义异常用于返回主菜单"""
    pass

# 系统配置
SCALE_FACTOR = math.pi * 10**6  # 默认比例尺

# 单位换算系统
linear_units = {
    'cm': 1,
    'm': 100,
    'km': 100000,
    'mm': 0.1,
    'in': 2.54  # 英寸
}

area_units = {
    'cm^2': 1,
    'm^2': 100**2,
    'km^2': (100000)**2,
    'ha': 10000 * 100**2,
    'mi^2': 2.58999e10
}

def set_scale_factor():
    """设置比例尺功能"""
    global SCALE_FACTOR  # 必须在函数顶部声明
    try:
        print("\n当前比例尺：1:{:,}".format(SCALE_FACTOR))
        while True:
            user_input = input("输入新比例尺分母（示例：100000）或 back：").strip()
            if user_input.lower() == 'back':
                raise BackToMainMenu
            
            try:
                new_scale = int(user_input)
                if new_scale > 0:
                    SCALE_FACTOR = new_scale  # 此处直接赋值
                    print(f"✓ 比例尺已更新为 1:{SCALE_FACTOR:,}")
                    return
                print("错误：必须输入正整数")
            except ValueError:
                print("错误：请输入有效数字")
                
    except BackToMainMenu:
        raise
    
def get_numeric_input(prompt, allowed_units):
    """获取带单位的数值输入，支持back返回"""
    while True:
        try:
            user_input = input(prompt).strip()
            if user_input.lower() == 'back':
                raise BackToMainMenu
            
            parts = re.split(r'\s+', user_input)
            value = float(parts[0])
            unit = parts[1]
            
            if unit not in allowed_units:
                raise ValueError(f"无效单位，可用单位：{', '.join(allowed_units)}")
                
            return value, unit
            
        except (ValueError, IndexError):
            print("输入错误！示例：150 cm 或 back 返回")
        except Exception as e:
            print(f"发生错误：{str(e)}")

def classic_conversion():
    """经典比例换算功能"""
    try:
        print("\n=== 经典比例换算（当前比例尺 1:{:,}）===".format(SCALE_FACTOR))
        print("1. 实地 → 图上\n2. 图上 → 实地")
        choice = input("请选择模式 (1/2): ").strip()
        if choice.lower() == 'back':
            raise BackToMainMenu
            
        if choice == '1':
            value, unit = get_numeric_input("输入实地距离（单位 cm/m/km）：", linear_units.keys())
            target = input("输出单位（cm/m/km）：").lower()
            cm_value = value * linear_units[unit]
            result = cm_value / SCALE_FACTOR / linear_units[target]
            print(f"结果：{result:.6f} {target}")
            
        elif choice == '2':
            value, unit = get_numeric_input("输入图上距离（单位 cm/m/km）：", linear_units.keys())
            target = input("输出单位（cm/m/km）：").lower()
            cm_value = value * linear_units[unit]
            result = cm_value * SCALE_FACTOR / linear_units[target]
            print(f"结果：{result:,.2f} {target}")
            
        else:
            print("无效选择！")
            
    except BackToMainMenu:
        raise

def coordinate_conversion():
    """坐标差转实地距离"""
    try:
        print("\n=== 坐标差换算（当前比例尺 1:{:,}）===".format(SCALE_FACTOR))
        dy, dy_unit = get_numeric_input("Δy（示例：20 cm）：", linear_units.keys())
        dx, dx_unit = get_numeric_input("Δx（示例：15 cm）：", linear_units.keys())

        
        # 统一为厘米计算
        dx_cm = dx * linear_units[dx_unit]
        dy_cm = dy * linear_units[dy_unit]
        distance = (dx_cm**2 + dy_cm**2)**0.5
        
        target = input("输出单位（cm/m/km）：").lower()
        result = distance * SCALE_FACTOR / linear_units[target]
        print(f"实地距离：{result:,.2f} {target}")
        
    except BackToMainMenu:
        raise

def area_conversion():
    """面积换算功能"""
    try:
        print("\n=== 面积换算（当前比例尺 1:{:,}）===".format(SCALE_FACTOR))
        print("1. 图上 → 实地\n2. 实地 → 图上")
        mode = input("请选择模式 (1/2): ").strip()
        if mode == 'back':
            raise BackToMainMenu
            
        # 获取面积输入
        def get_area():
            try:
                user_input = input("输入面积（示例：150 cm^2）或长宽（示例：2 cm × 3 m）：").strip()
                if user_input.lower() == 'back':
                    raise BackToMainMenu
                
                # 解析面积输入
                if '×' in user_input or 'x' in user_input or '*' in user_input:
                    parts = re.split(r'\s*[×x*]\s*', user_input)
                    if len(parts) != 2:
                        raise ValueError
                    length, l_unit = re.split(r'\s+', parts[0].strip())
                    width, w_unit = re.split(r'\s+', parts[1].strip())
                    l_cm = float(length) * linear_units[l_unit]
                    w_cm = float(width) * linear_units[w_unit]
                    return l_cm * w_cm  # 返回cm^2
                else:
                    parts = re.split(r'\s+', user_input.strip())
                    return float(parts[0]) * area_units[parts[1]]
                    
            except (ValueError, KeyError):
                print("输入格式错误！示例：'150 cm^2' 或 '2 cm × 3 m'")
                return get_area()
                
        area_cm2 = get_area()
        
        # 执行换算
        scale_sq = SCALE_FACTOR ** 2
        if mode == '1':
            real_area = area_cm2 * scale_sq
        else:
            real_area = area_cm2 / scale_sq
            
        # 选择输出单位
        target = input(f"输出单位（{', '.join(area_units.keys())}）：").strip()
        result = real_area / area_units[target]
        print(f"结果：{result:,.3f} {target}")
        
    except BackToMainMenu:
        raise

def simple_calculator():
    """简单四则运算"""
    try:
        print("\n=== 四则运算 ===")
        while True:
            expr = input("输入公式（示例：136.50/15）或 back：").strip()
            if expr.lower() == 'back':
                raise BackToMainMenu
                
            # 替换中文运算符
            expr = expr.replace('×', '*').replace('÷', '/')
            if not re.match(r'^[\d\s\.\+\-\*/\(\)]+$', expr):
                print("包含非法字符！")
                continue
                
            try:
                result = round(eval(expr), 3)
                print(f"结果：{result:.3f}")
            except ZeroDivisionError:
                print("错误：除数不能为零！")
            except:
                print("计算错误！")
                
    except BackToMainMenu:
        raise

def main():
    """主控制系统"""
    print("测绘计算综合系统")
    print("提示：在任何输入步骤输入 'back' 可返回上级菜单")
    
    while True: 
        print("\n=======================================")
        print("\n主菜单：")
        print("1. 经典比例换算")
        print("2. 坐标差换算")
        print("3. 设置比例尺（当前：1:{:,}）".format(SCALE_FACTOR))
        print("4. 面积换算")
        print("5. 四则运算")
        print("6. 退出系统")
        
        choice = input("请选择功能：").strip()
        
        try:
            if choice == '1':
                classic_conversion()
            elif choice == '2':
                coordinate_conversion()
            elif choice == '3':
                set_scale_factor()
            elif choice == '4':
                area_conversion()
            elif choice == '5':
                simple_calculator()
            elif choice == '6':
                print("感谢使用！")
                break
            else:
                print("无效输入！")
                
        except BackToMainMenu:
            continue

if __name__ == "__main__":
    main()
