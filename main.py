"""실행 진입점: constraints.json을 읽어 solver로 최적화하고 renderer로 평면도 PNG를 출력한다."""

import json

import pulp

from renderer import draw_layout
from solver import solve

OUTPUT_PATH = "output/layout.png"


def main():
    print("=== Co-Layout MVP ===")

    print("[1/3] 제약조건 로드...", end=" ")
    with open("constraints.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    print("완료")

    print("[2/3] 최적화 (CBC)...", end=" ")
    status, grid = solve(cfg)
    status_str = pulp.LpStatus[status]
    print(f"완료 (status: {status_str})")

    print("[3/3] 도면 생성...", end=" ")
    draw_layout(grid, cfg, OUTPUT_PATH)
    print("완료")

    print("---------------------")
    print(f"{OUTPUT_PATH} 저장됨")
    print("=====================")


if __name__ == "__main__":
    main()
