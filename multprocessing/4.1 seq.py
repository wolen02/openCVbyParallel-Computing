import time
import pandas as pd

def burn_cpu(n: int):
    x = 0
    for i in range(n):
        x = (x * 1664525 + 1013904223) & 0xFFFFFFFF
        x ^= (x >> 16)
    return x


def main():
    
    data = {'총 실행시간': []}
    
    for i in range(30):
        
        start_time = time.perf_counter()
        
        for i in range(5000):
            burn_cpu(5000)
        
        end_time = time.perf_counter()
        run_time = end_time - start_time
        
        print(f"실행 끝. 총 소요시간 :{run_time}")
        
        data['총 실행시간'].append(run_time)

    df = pd.DataFrame(data)
    df.to_excel('/Users/wnwlt/Desktop/실험 결과/seq.xlsx', index=True, sheet_name='process')

if __name__ == "__main__":
    
    main()
