import json
import os

ROSTER_FILE = "gym_roster.json"

def load_roster():
    """读取 JSON 数据文件，如果不存在则返回空字典"""
    if not os.path.exists(ROSTER_FILE):
        return {}
    with open(ROSTER_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_roster(roster):
    """将数据保存回 JSON 文件，使用缩进方便阅读"""
    with open(ROSTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(roster, f, indent=4, ensure_ascii=False)

def get_target_plan(exercise_data):
    """根据当前状态生成目标计划提示文本"""
    state = exercise_data["current_state"]
    weight = exercise_data["current_weight"]
    base_sets = exercise_data["base_sets"]
    base_reps = exercise_data["base_reps"]

    if state == "A":
        return f"状态 A: 目标是完成 {base_sets} 组，并且每组至少 {base_reps} 次。当前重量：{weight}kg"
    elif state == "B":
        target_reps = (base_sets * base_reps) + 3
        return f"状态 B: 目标是所有组累积完成 {target_reps} 次以上（可尝试增加组数或每组次数）。当前重量：{weight}kg"
    elif state == "C":
        return f"状态 C: 目标是完成 {base_sets + 1} 组，并且每组至少 {base_reps} 次。当前重量：{weight}kg"
    elif state == "D":
        return f"状态 D (Deload / 减载阶段): 请完成 2 组恢复性训练。当前重量（已减低 10%）：{weight}kg"
    else:
        return "未知状态"

def process_workout(exercise_data, reps_input):
    """依据本次实际训练次数更新状态机"""
    state = exercise_data["current_state"]
    weight = exercise_data["current_weight"]
    base_sets = exercise_data["base_sets"]
    base_reps = exercise_data["base_reps"]
    increment = exercise_data.get("weight_increment", 2.5)
    
    # 将每组次数相加得到本次训练总容量（总次数）
    total_reps = sum(reps_input)
    
    print("\n--- 训练状态分析 ---")
    
    if state == "A":
        # 统计有几个组数达到或超过基础次数要求
        successful_sets = sum(1 for r in reps_input if r >= base_reps)
        if successful_sets >= base_sets:
            # 状态 A 成功：维持状态 A
            exercise_data["current_weight"] += increment
            exercise_data["current_state"] = "A"
            exercise_data["stuck_counter"] = 0
            print(f"【分析结果】太棒了！您跑通了状态 A。下次重量将增加 {increment}kg。")
        else:
            # 状态 A 失败：进入状态 B
            exercise_data["current_state"] = "B"
            exercise_data["stuck_counter"] = 0
            exercise_data["previous_total_reps"] = total_reps
            print("【分析结果】未达成基础组数与次数。已进入状态 B，接下来要挑战增加总容量。")

    elif state == "B":
        # 状态 B 目标总次数 = (基础组数 * 基础次数) + 3
        target_reps = (base_sets * base_reps) + 3
        if total_reps >= target_reps:
            # 状态 B 成功：重回状态 A
            exercise_data["current_weight"] += increment
            exercise_data["current_state"] = "A"
            exercise_data["stuck_counter"] = 0
            print(f"【分析结果】不可思议！状态 B 目标达成。您的力量有所增强，下次进入状态 A 并增加重量 {increment}kg。")
        else:
            # 状态 B 未达成目标：检查总次数是否比上次有增长
            previous_reps = exercise_data.get("previous_total_reps", 0)
            if total_reps <= previous_reps:
                # 如果没有增长，或者倒退，则卡点记录 + 1
                exercise_data["stuck_counter"] += 1
            else:
                # 只要比上一次总次数增加，说明在进步，卡点计数清零
                exercise_data["stuck_counter"] = 0
            
            # 更新为本次训练总次数供下次比较
            exercise_data["previous_total_reps"] = total_reps
            
            if exercise_data["stuck_counter"] >= 2:
                # 如果连续两次卡点（即两次未增长），进入状态 C
                exercise_data["current_state"] = "C"
                exercise_data["stuck_counter"] = 0
                print("【分析结果】状态 B 连续两次没有增量出现卡点，将进入状态 C，下次通过增加挑战组数来突破平颈期。")
            else:
                print(f"【分析结果】今天总次数是 {total_reps}，上次是 {previous_reps}。您还在此状态，继续保持状态 B！")

    elif state == "C":
        # 目标是增加 1 组，比如原先 3 组的话现在目标是 4 组达到基础次数 base_reps
        target_sets_c = base_sets + 1
        successful_sets = sum(1 for r in reps_input if r >= base_reps)
        if successful_sets >= target_sets_c:
            # 状态 C 成功：回到状态 A
            exercise_data["current_weight"] += increment
            exercise_data["current_state"] = "A"
            exercise_data["stuck_counter"] = 0
            print(f"【分析结果】恭喜突破！状态 C 目标达成，下次增加重量 {increment}kg 并回到常规组数状态 A。")
        else:
            # 状态 C 失败：进入状态 D（减载层 Deload）
            # 新重量减少 10%，并尝试以 increment 倍数向下舍入或对齐
            new_weight = weight * 0.9
            new_weight = round(new_weight / increment) * increment
            exercise_data["current_weight"] = new_weight
            exercise_data["current_state"] = "D"
            exercise_data["stuck_counter"] = 0
            print(f"【分析结果】状态 C 失败。触发 Deload（减载）机制，下次将以减轻后的重量 ({new_weight}kg) 进行仅仅 2 组的休息恢复性训练。")

    elif state == "D":
        # 只要执行完状态 D 的训练内容，无论表现如何，下次都会回到状态 A (继续保持减轻后的重量) 重新积累。
        exercise_data["current_state"] = "A"
        exercise_data["stuck_counter"] = 0
        print("【分析结果】减载 (Deload) 训练已完成。您得到了充分的休息与恢复，下次将重新从状态 A 开始。")
        
    return exercise_data

def main():
    print("=== 欢迎使用核心健身训练进展追踪系统 (Triple Progression CLI) ===")
    roster = load_roster()
    if not roster:
        print("无法找到或读取花名册 gym_roster.json 文件。")
        return

    users = list(roster.keys())
    print("\n请选择您的用户档案:")
    for i, user in enumerate(users):
        print(f"[{i+1}] {user}")
    print("[0] ➕ 添加新用户")
    
    try:
        user_choice = int(input("\n请输入数字选择 (输入 0 添加新用户): "))
        if user_choice == 0:
            new_user = input("请输入新用户的名称：\n> ").strip()
            if new_user and new_user not in roster:
                roster[new_user] = {}
                save_roster(roster)
                print(f"\n✅ 新用户 【{new_user}】 已创建！")
                selected_user = new_user
            else:
                print("用户名无效或已存在。退出程序。")
                return
        else:
            selected_user = users[user_choice - 1]
    except (ValueError, IndexError):
        print("输入无效。将退出程序。")
        return

    exercises = list(roster[selected_user].keys())
    print(f"\n你好，{selected_user}！请选择本次训练的动作:")
    for i, ex in enumerate(exercises):
        print(f"[{i+1}] {ex}")
    print("[0] ➕ 添加新动作")
        
    try:
        ex_choice = int(input("\n请输入数字选择 (输入 0 添加新动作): "))
        if ex_choice == 0:
            new_ex = input("请输入新动作的名称：\n> ").strip()
            if not new_ex or new_ex in roster[selected_user]:
                print("动作名称无效或已存在。退出程序。")
                return
            
            sets_input = input("请输入该动作的专属基准组数 (Base Sets，默认 3)：\n> ").strip()
            reps_input = input("请输入该动作的专属每组次数 (Base Reps，默认 8)：\n> ").strip()
            
            base_sets = int(sets_input) if sets_input.isdigit() and int(sets_input) > 0 else 3
            base_reps = int(reps_input) if reps_input.isdigit() and int(reps_input) > 0 else 8
            
            inc_input = input("请输入该动作每次进阶的最小加重量（步长）。例如：杠铃可填 2.5，固定器械请根据插销差值填写（默认直接回车为 2.5）：\n> ").strip()
            try:
                weight_increment = float(inc_input) if inc_input else 2.5
            except ValueError:
                weight_increment = 2.5
            
            roster[selected_user][new_ex] = {
                "current_weight": None,
                "weight_increment": weight_increment,
                "base_sets": base_sets,
                "base_reps": base_reps,
                "current_state": "A",
                "stuck_counter": 0,
                "previous_total_reps": 0
            }
            save_roster(roster)
            print("\n✅ 新动作已加入！")
            selected_exercise = new_ex
        else:
            selected_exercise = exercises[ex_choice - 1]
    except (ValueError, IndexError):
        print("输入无效。将退出程序。")
        return

    exercise_data = roster[selected_user][selected_exercise]
    
    # 冷启动检测：如果是首次记录该动作，重量为 None（对应 JSON 的 null）
    if exercise_data.get("current_weight") is None:
        while True:
            print("\n⚠️ 发现记录为空：检测到您是首次记录该动作。")
            weight_str = input("为了定制您的专属计划，请输入您目前该动作的起始训练重量（单位：kg）：\n> ")
            try:
                initial_weight = float(weight_str.strip())
                if initial_weight < 0:
                    print("重量不能为负数，请重新输入。")
                    continue
                
                # 保存合法初始重量
                exercise_data["current_weight"] = initial_weight
                
                # 步长补录逻辑
                inc_input = input("请输入该动作每次进阶的最小加重量（步长）。例如：杠铃可填 2.5，固定器械请根据插销差值填写（默认直接回车为 2.5）：\n> ").strip()
                try:
                    exercise_data["weight_increment"] = float(inc_input) if inc_input else 2.5
                except ValueError:
                    exercise_data["weight_increment"] = 2.5
                
                # 基准容量修改逻辑
                base_sets = exercise_data["base_sets"]
                base_reps = exercise_data["base_reps"]
                print(f"\n当前该动作的系统默认目标是 {base_sets} 组 x {base_reps} 次。是否需要修改？(y/n)")
                modify_base = input("> ").strip().lower()
                
                if modify_base == 'y' or modify_base == 'yes':
                    while True:
                        try:
                            new_sets = int(input("请输入您的专属基准组数 (Base Sets)：\n> ").strip())
                            new_reps = int(input("请输入您的专属每组次数 (Base Reps)：\n> ").strip())
                            if new_sets > 0 and new_reps > 0:
                                exercise_data["base_sets"] = new_sets
                                exercise_data["base_reps"] = new_reps
                                print(f"✅ 系统目标已更新为 {new_sets} 组 x {new_reps} 次。")
                                break
                            else:
                                print("组数和次数必须大于 0，请重新输入。")
                        except ValueError:
                            print("输入格式有误，请输入纯数字整数。")
                
                # 立即存回本地防止意外丢失
                roster[selected_user][selected_exercise] = exercise_data
                save_roster(roster)
                print(f"\n✅ 起始重量已成功设置为 {initial_weight}kg！让我们开始针对性训练吧。")
                break
            except ValueError:
                print("输入格式有误，请输入纯数字（例如：60 或 62.5）。")
    
    while True:
        print("\n请如实输入您今天完成的每一组次数。")
        print("示例：如果做了 3 组，分别是 8 次、8 次、7 次，请输入：8 8 7")
        reps_str = input("> ")
        
        try:
            # 将用户输入的连续字符串拆分成整数列表
            reps_input = [int(r) for r in reps_str.strip().split()]
            if not reps_input:
                raise ValueError
            
            # 防呆校验: 判断输入的组数与目标状态所需组数是否匹配
            current_state = exercise_data["current_state"]
            # 若是状态 C，目标组数是 base_sets + 1，状态 D 是强制 2 组，其余均按 base_sets 算
            expected_sets = exercise_data["base_sets"]
            if current_state == "C":
                expected_sets += 1
            elif current_state == "D":
                expected_sets = 2
                
            if len(reps_input) != expected_sets:
                print(f"\n⚠️ 输入错误：您的计划目标是 {expected_sets} 组，但您输入了 {len(reps_input)} 组的数据。")
                print("请重新输入，或检查是否少录入了某组。")
                continue
            
            # 若校验通过，跳出输入循环
            break
            
        except ValueError:
            print("\n输入有误，请确保输入的是用空格隔开的数字（且不能为空）。请重新输入！")
        
    # 将本次训练送入状态机评估得出之后的状态
    updated_data = process_workout(exercise_data, reps_input)
    
    # 覆盖原有数据并保存回配置文件 JSON
    roster[selected_user][selected_exercise] = updated_data
    save_roster(roster)
    
    print("\n============== 下次预告 ==============")
    print("最新计划已保存。您下一次此部位的训练指示如下：")
    print(get_target_plan(updated_data))
    print("=======================================\n")

if __name__ == "__main__":
    # 若在终端中直接作为脚本运行即可触发主函数
    main()
