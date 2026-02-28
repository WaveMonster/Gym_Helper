import json
from main import process_workout

# Test State A pass
data_a = {"current_weight": 60.0, "base_sets": 3, "base_reps": 8, "current_state": "A", "stuck_counter": 0, "previous_total_reps": 0}
res_a = process_workout(data_a.copy(), [8, 8, 8])
assert res_a["current_state"] == "A"
assert res_a["current_weight"] == 62.5

# Test State A fail
res_a_fail = process_workout(data_a.copy(), [8, 8, 7])
assert res_a_fail["current_state"] == "B"
assert res_a_fail["current_weight"] == 60.0
assert res_a_fail["previous_total_reps"] == 23

# Test State B pass
data_b = {"current_weight": 60.0, "base_sets": 3, "base_reps": 8, "current_state": "B", "stuck_counter": 0, "previous_total_reps": 23}
res_b = process_workout(data_b.copy(), [9, 9, 9]) # sum 27
assert res_b["current_state"] == "A"
assert res_b["current_weight"] == 62.5

# Test State B stuck once
res_b_fail = process_workout(data_b.copy(), [8, 8, 7]) # sum 23
assert res_b_fail["current_state"] == "B"
assert res_b_fail["stuck_counter"] == 1

# Test State B stuck twice
data_b_stuck = res_b_fail.copy()
res_b_fail2 = process_workout(data_b_stuck.copy(), [8, 8, 7]) # sum 23 again
assert res_b_fail2["current_state"] == "C"

# Test State C pass
data_c = {"current_weight": 60.0, "base_sets": 3, "base_reps": 8, "current_state": "C", "stuck_counter": 0, "previous_total_reps": 0}
res_c = process_workout(data_c.copy(), [8, 8, 8, 8]) # 4 sets >= 8
assert res_c["current_state"] == "A"
assert res_c["current_weight"] == 62.5

# Test State C fail -> D
res_c_fail = process_workout(data_c.copy(), [8, 8, 8, 7])
assert res_c_fail["current_state"] == "D"
assert res_c_fail["current_weight"] == 55.0 # 60 * 0.9 = 54 -> round / 2.5 * 2.5 = 55.0

# Test State D
data_d = {"current_weight": 55.0, "base_sets": 3, "base_reps": 8, "current_state": "D", "stuck_counter": 0, "previous_total_reps": 0}
res_d = process_workout(data_d.copy(), [8, 8])
assert res_d["current_state"] == "A"
assert res_d["current_weight"] == 55.0

print("All tests passed!")