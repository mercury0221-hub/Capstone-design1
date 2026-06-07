"""PuLP + CBC 격자 기반 방 배치 최적화: 이진 변수 생성, 비겹침/면적 제약, 풀이."""

import json

import pulp


def create_variables(cfg):
    """격자 셀 × 방 조합마다 이진 변수를 생성한다.

    Args:
        cfg: constraints.json을 파싱한 dict (grid, rooms 포함).

    Returns:
        dict: 키 (i, j, k) → LpVariable(cat='Binary').
            i = 행 인덱스 (0 ~ H-1), j = 열 인덱스 (0 ~ W-1), k = 방 id(str).
            값이 1이면 셀 (i, j)가 방 k에 속함을 의미한다.
    """
    width = cfg["grid"]["width"]
    height = cfg["grid"]["height"]
    room_ids = [room["name"] for room in cfg["rooms"]]

    x = {}
    for i in range(height):
        for j in range(width):
            for k in room_ids:
                x[(i, j, k)] = pulp.LpVariable(f"x_{i}_{j}_{k}", cat="Binary")
    return x


def solve(cfg):
    """비겹침 제약 하에서 Feasible한 방 배치를 탐색한다.

    Args:
        cfg: constraints.json을 파싱한 dict.

    Returns:
        tuple (status, grid):
            status: pulp 풀이 상태 코드 (pulp.LpStatus[status]로 문자열화).
            grid: 2D 리스트, grid[i][j] = 해당 셀이 배정된 방 id(str) 또는 None.
    """
    width = cfg["grid"]["width"]
    height = cfg["grid"]["height"]
    room_ids = [room["name"] for room in cfg["rooms"]]

    prob = pulp.LpProblem("co_layout_mvp", pulp.LpMinimize)
    x = create_variables(cfg)

    # 비겹침 제약: 각 셀은 정확히 하나의 방에만 속한다.
    for i in range(height):
        for j in range(width):
            prob += pulp.lpSum(x[(i, j, k)] for k in room_ids) == 1

    # 면적 제약: 각 방의 셀 합계 == targetArea.
    for room in cfg["rooms"]:
        k = room["name"]
        target = room["targetArea"]
        prob += (
            pulp.lpSum(x[(i, j, k)] for i in range(height) for j in range(width))
            == target
        )

    # 목적함수 없음 (Feasible 해만 탐색).
    prob += 0

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    # 결과를 2D 그리드로 변환.
    grid = [[None for _ in range(width)] for _ in range(height)]
    for i in range(height):
        for j in range(width):
            for k in room_ids:
                if pulp.value(x[(i, j, k)]) == 1:
                    grid[i][j] = k
                    break

    return prob.status, grid


if __name__ == "__main__":
    with open("constraints.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    x = create_variables(cfg)

    width = cfg["grid"]["width"]
    height = cfg["grid"]["height"]
    n_rooms = len(cfg["rooms"])
    print(
        f"변수 생성 완료: {height}×{width} 격자 × {n_rooms}개 방 = {len(x)}개"
    )

    status, grid = solve(cfg)
    print(f"풀이 상태: {pulp.LpStatus[status]}")

    if pulp.LpStatus[status] != "Optimal":
        total_target = sum(r["targetArea"] for r in cfg["rooms"])
        grid_area = width * height
        print(
            f"[확인] targetArea 합={total_target}, 격자 면적={grid_area} "
            f"({'일치' if total_target == grid_area else '불일치 → Infeasible 원인'})"
        )

    # 방별 실제 할당 셀 수 검증.
    counts = {room["name"]: 0 for room in cfg["rooms"]}
    for row in grid:
        for cell in row:
            if cell is not None:
                counts[cell] += 1
    for room in cfg["rooms"]:
        k, target = room["name"], room["targetArea"]
        mark = "✓" if counts[k] == target else "✗"
        print(f"{k}: {counts[k]}셀 (목표: {target}) {mark}")

    print("배치 결과 (방 id 첫 글자):")
    for row in grid:
        print(" ".join((cell[0] if cell else ".") for cell in row))
