import time
import pandas as pd

# CPU에 부하를 주기 위한 연산
def burn_cpu(n: int):
    
    # 연산을 위한 변수
    x = 0
    
    # 선형 합동 생성기 방식의 연산 과 비트 이동 및 XOR 연산
    for i in range(n):
        x = (x * 1664525 + 1013904223) & 0xFFFFFFFF
        x ^= (x >> 16)
    return x


def main():
    
    # 실험 결과를 저장하기 위한 저장소
    data = {'총 실행시간': []}
    
    # 실험 30회 반복 실행
    for i in range(30):
        
        start_time = time.perf_counter()
        
        # 5000번 실행
        for i in range(5000):
            burn_cpu(5000)
        
        end_time = time.perf_counter()
        run_time = end_time - start_time
        
        print(f"실행 끝. 총 소요시간 :{run_time}")
        
        data['총 실행시간'].append(run_time)

    # 엑셀에 저장
    df = pd.DataFrame(data)
    df.to_excel('/Users/wnwlt/Desktop/실험 결과/seq.xlsx', index=True, sheet_name='process')

if __name__ == "__main__":
    
    main()
