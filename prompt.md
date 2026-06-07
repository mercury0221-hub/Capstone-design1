# Co-Layout MVP 구현 프롬프트 기록

Co-Layout 논문(arXiv:2511.12474)의 (b) Optimization 파트를 MVP로 구현하기 위해
사용한 프롬프트들을 순서대로 기록한다.

---

## 목표 (MVP)

JSON 제약조건을 입력받아 **PuLP + CBC**로 격자 기반 방 배치를 최적화하고,
**matplotlib**으로 컬러 평면도 PNG 1장을 출력한다.

**MVP 범위 (구현)**
- JSON 입력 파싱
- 이진 변수 생성 (각 셀이 어느 방에 속하는지)
- 비겹침 제약 (각 셀은 하나의 방에만)
- 면적 제약 (각 방의 셀 수 = 목표 면적)
- matplotlib 컬러 평면도 PNG 출력

**제외 (구현하지 않음)**
- 인접 제약, 복도 연결성, 목적 함수, 가구 배치, Coarse-to-Fine
- LLM 에이전트, Blender 렌더링

---

## Step 1 — 파일 구조 스캐폴딩

```
co_layout_mvp/
├── main.py          # 실행 진입점
├── constraints.json # 입력 파일
├── solver.py        # 변수 + 제약 + CBC 풀이
├── renderer.py      # matplotlib 도면 출력
└── output/          # 결과 저장 폴더
```

> 빈 파일 + 한 줄 docstring만 생성. 실제 로직은 작성하지 않음.

---

## Step 2 — constraints.json 작성

- grid: width 10, height 8 (총 80셀)
- rooms 4개:
  - living(거실):   targetArea 30, color `#B5D4F4`
  - bedroom(침실):  targetArea 20, color `#CECBF6`
  - kitchen(주방):  targetArea 16, color `#C0DD97`
  - bathroom(욕실): targetArea 14, color `#FAC775`

**가장 중요한 규칙**: `targetArea 합계 == grid.width × grid.height`
30 + 20 + 16 + 14 = 80 = 10 × 8 ✓ (안 맞으면 무조건 Infeasible)

**검증**:
```
python -c "import json; d=json.load(open('constraints.json')); print('합계:', sum(r['targetArea'] for r in d['rooms']), '/ 격자:', d['grid']['width']*d['grid']['height'])"
```

---

## Step 3 — solver.py: 이진 변수 생성

`create_variables(cfg)`
- cfg: constraints.json을 파싱한 dict
- 반환: dict x, 키는 `(i, j, k)` 튜플
  - i: 행 인덱스 (0 ~ H-1)
  - j: 열 인덱스 (0 ~ W-1)
  - k: 방 id 문자열
- `x[(i,j,k)] = LpVariable(..., cat='Binary')`
  의미: 셀(i,j)가 방k에 속하면 1, 아니면 0
- 검증: `"변수 생성 완료: 10×8 격자 × 4개 방 = 320개"`

---

## Step 4 — solver.py: 비겹침 제약 + 풀이 로직

`solve(cfg)`
1. `LpProblem` 생성 (LpMinimize)
2. `create_variables(cfg)`로 변수 x 생성
3. 비겹침 제약: 각 셀 (i,j)는 정확히 하나의 방에만 속함
   `prob += lpSum(x[(i,j,k)] for k in room_ids) == 1`
4. 목적함수는 `prob += 0` (Feasible 해만 탐색)
5. `prob.solve(PULP_CBC_CMD(msg=0))`
6. 결과를 2D 리스트 grid로 변환 — `grid[i][j]` = value(x)가 1인 방의 id
- 검증: `LpStatus` 출력 + grid 텍스트 출력 (각 셀에 방 id 첫 글자)

---

## Step 5 — solver.py: 면적 제약

각 방 k의 셀 합계 == targetArea:
```python
for room in cfg['rooms']:
    k = room['name']           # (스펙은 room['id'], 실제 JSON 키는 name)
    target = room['targetArea']
    prob += lpSum(x[(i,j,k)] for i in range(H) for j in range(W)) == target
```
- 검증: 방별 실제 할당 셀 수 출력 → `"living: 30셀 (목표: 30) ✓"` ...
- Infeasible이면 targetArea 합과 격자 면적(W×H)이 같은지 가장 먼저 확인

---

## Step 6 — renderer.py + main.py 연결

`renderer.py: draw_layout(grid, cfg, output_path="output/layout.png")`
1. 각 방을 cfg의 color 값으로 채우기 (imshow)
2. 방 이름(name)을 각 방 영역 중심에 텍스트 표시
3. 격자선을 옅은 회색으로 표시
4. 범례(방 이름 + 색상)를 우측에 배치
5. 제목: `"Co-Layout MVP Result"`
6. dpi=150으로 `output/layout.png` 저장

`main.py: 전체 흐름`
1. constraints.json 로드
2. `status, grid = solve(cfg)`  (solve는 (status, grid) 튜플 반환)
3. `draw_layout(grid, cfg)`
4. 진행 상황 print

**출력 형식**
```
=== Co-Layout MVP ===
[1/3] 제약조건 로드... 완료
[2/3] 최적화 (CBC)... 완료 (status: Optimal)
[3/3] 도면 생성... 완료
---------------------
output/layout.png 저장됨
=====================
```

---

## 실행 메모 (이 환경 기준)

- `python`이 아니라 **`py`** 런처로 실행해야 함.
- 한글 출력이 깨지면 `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` 환경변수를 붙인다.
  예: `PYTHONUTF8=1 PYTHONIOENCODING=utf-8 py main.py`
- PuLP는 venv에 이미 설치되어 있음.

## 알려진 한계 (= 의도된 MVP 제외 범위)

면적은 정확히 30/20/16/14로 맞지만, **방이 직사각형 한 덩어리로 모이지 않음**
(일부 방이 여러 조각으로 분리됨). 한 덩어리로 모으려면 인접 제약 + 목적함수
(rectangularity / shape)가 추가로 필요하다.
