import random
def grid_sample_no_overlap(x_range, y_range, N, min_gap, used):
    x0, x1 = x_range
    y0, y1 = y_range

    # min_gap 간격으로 후보 만들기
    xs_cand = list(range(x0, x1+1, min_gap))
    ys_cand = list(range(y0, y1+1, min_gap))

    # 전역 used를 제외한 그리드
    grid = [(x, y)
            for x in xs_cand
            for y in ys_cand
            if (x, y) not in used]
    
    if len(grid) < N:
        raise ValueError(f"후보가 부족합니다: {len(grid)} available < required {N}")

    # ③ 랜덤 샘플링
    chosen = random.sample(grid, N)

    # ④ used에 추가
    for pt in chosen:
        used.add(pt)

    return [[x, y, 0] for x, y in chosen]



PLACEMENT = {
    'blue':{ # x, y, color
        '74전차대대_1중대':{
            # x_range, y_range
            'loc':[[385, 390], [350, 500]], 
            'split': 3,
            'comp':{
                "Sho't_Kal":15,
            },
            'phase': 'P1'
        },
        '75기계화보병대대_1중대':{
            'loc': [[370, 380], [400, 435]], 
            'comp': {
                "M113": 10,
                "M72_LAW":6
                },
            'phase': 'P1'
        },
        '179야포대대_박격포중대':{
            'loc': [[350, 370], [450, 500]], 
            'comp': {
                "60mm_Mortar": 3
                },
            'phase': 'P1'
        },
        '179야포대대_105mm견인포1중대':{
            'loc': [[375, 380], [460, 500]], 
            'comp': {
                "105mm_Howitzer": 3
                },
            'phase': 'P1'
        },
        '74전차대대_1중대':{
            'loc': [[250, 275], [180, 240]], 
            'comp': {
                "Sho't_Kal":5
                },
                'phase': 'P1'
        },
        '179야포대대_105mm견인포2중대':{
            'loc': [[265, 270], [190, 220]], 
            'comp': {
                "105mm_Howitzer": 3
                },
                'phase': 'P1'
        },
        '53전차대대_1중대':{
            'loc': [[100, 120], [330, 380]], 
            'dest': [[470, 500], [380, 400]],        
            'comp': {
                "Sho't_Kal":10
                },
            'phase': 'P2'
            }
    },
    'red':{
        '85보병여단_1보병대대_1중대': {
            'loc': [[650, 700], [350, 420]], 
            'comp':{
                "AK-47":90,
                "RPG-7":6,
                "107mm_B-11_Recoilless_Rifle":1
                }, # 80 50
            'phase': 'P1-1'
        },
        '85보병여단_2보병대대_4중대': {
            'loc': [[700, 750], [350, 420]], 
            'comp': {
                "AK-47":90,
                "RPG-7":6,
                "107mm_B-11_Recoilless_Rifle":1
                },
                'phase': 'P1-1'
        },
        '121기계화보병여단_전차중대': {
            'loc': [[620, 670], [350, 400]], 
            'comp': {
                "T-55": 10,
            }, # 80 50
        'phase': 'P1-1'
        },
        '82기갑여단_5전차대대': {
            'loc': [[620, 670], [440, 520]], 
            'comp': {
                "T-55":50,  
            }, # 80 50
            'phase': 'P2-1'
        },
        '82기갑여단_기보중대':  {
            'loc': [[680, 770], [440, 480]], 
            'comp': {
                "BMP-1":10,
                "RPG-7": 10
                }, # 80 50
            'phase': 'P2-2'
        },
        '82기갑여단_6전차대대': {
            'loc': [[650, 680], [300, 350]], 
            'comp': {
                "T-55":10
                },
            'phase': 'P3'
        },
        '78기갑여단_1전차대대': {
            'loc': [[650, 700], [300, 350]], 
            'comp': {
                "T-55":40
                },
            'phase': 'P3'
        },
        '81기갑여단_7전차대대': {
            'loc': [[720, 770], [300, 350]], 
            'comp': {
                "T-62":40,
            }, 
            'phase': 'P4'
        },
        '121기계화보병여단_3기보대대': {
            'loc': [[770, 790], [350, 420]], 
            'comp': {
                "BMP-1": 40,
                "9M14_Malyutka": 3,
                "RPG-7": 40
                },
            'phase': 'P4' # 80 50
        }
    }
}
