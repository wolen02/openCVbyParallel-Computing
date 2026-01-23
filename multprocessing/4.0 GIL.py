from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import time
import pandas as pd

# CPU에 부하를 주기 위한 연산
def burn_cpu(n: int):
    
    # 연산을 위한 변수
    x = 0
    
    # 작업 횟수를 계산하기 위한 변수
    tmp_count = 0
    
    for i in range(n):
        x = (x * 1664525 + 1013904223) & 0xFFFFFFFF
        x ^= (x >> 16)
        tmp_count += 1
    return tmp_count


def main():
    
    n_tasks = 5000
    n_worker = 8
    
    # 실험 결과를 저장하기 위한 저장소
    data = {'총 실행횟수': []
            , '총 실행시간': []
            , '작업 제출 오버헤드시간': []
            , '연산 시간': []
            , '처리율': []}
    
    # 실험 30회 반복 실행
    for i in range(30):
    
        count = 0

        start_time = time.perf_counter()
        
        # CPU bound 연산 멀티 스레드로 실행
        with ThreadPoolExecutor(max_workers=n_worker) as ex:
            futures = [ex.submit(burn_cpu, 5000) for i in range(n_tasks)]
            submit_done_time = time.perf_counter()
           
           # 끝난 작업 제출 
            for future in as_completed(futures):
                count += future.result()
                    
        # 지표       
        end_time = time.perf_counter()
        submit_overhead = submit_done_time - start_time
        execution_and_collection_time = end_time - submit_done_time
        run_time = end_time - start_time
        
        throughput = count/run_time

        print(f"총 실행횟수: {count}")    
        print(f"총 실행시간: {run_time}")
        print(f"작업 제출 오버헤드시간 :{submit_overhead}")
        print(f"연산 시간: {execution_and_collection_time}")
        print(f"처리율: {throughput}")

        data['총 실행횟수'].append(count)
        data['총 실행시간'].append(run_time)
        data['작업 제출 오버헤드시간'].append(submit_overhead)
        data['연산 시간'].append(execution_and_collection_time)
        data['처리율'].append(throughput)
    
    # 엑셀에 저장    
    df = pd.DataFrame(data)
    df.to_excel('/Users/wnwlt/Desktop/실험 결과/GIL_8.xlsx', index=True, sheet_name='process')
    

if __name__ == "__main__":
    
    main()
