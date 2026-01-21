from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
import time
import pandas as pd

# CPU에 부하를 주기 위한 연산
def burn_cpu(n: int):
    
    # 작업 횟수를 계산하기 위한 변수
    tmp_count = 0
    
    # 연산을 위한 변수
    x = 0
 
    # 선형 합동 생성기 방식의 연산 과 비트 이동 및 XOR 연산
    for i in range(n):
        x = (x * 1664525 + 1013904223) & 0xFFFFFFFF
        x ^= (x >> 16)
        tmp_count += 1
        
    return tmp_count

# 연산 시간을 확인하기 위한 함수
def job(n: int):
    
    #연산 시작 시간
    t0 = time.perf_counter()
    
    out = burn_cpu(n)
    
    #연산 종료 시간
    t1 = time.perf_counter()
    return out, (t1 - t0)

# batch 단위로 실행 하기 위한 함수
def job_batch(batch_size: int, n: int):
    
    total_count = 0
    total_compute = 0
    
    for _ in range(batch_size):
        
        out, t = job(n)
        total_count += out
        total_compute += t
        
    return total_count, total_compute

# 마지막 배치가 덜 찰 수 있으니 개수 리스트로 생성
def chunks(n: int, batch_size: int):

    full = n // batch_size
    rem = n % batch_size
    sizes = [batch_size] * full
    if rem:
        sizes.append(rem)
    return sizes

def main():
    
    # 총 작업 수
    n_tasks = 5000
    # 프로세스 수
    n_worker = 4
    
    # 실험 결과를 저장하기 위한 저장소
    data = {'총 실행횟수': []
            , '총 실행시간': []
            , '평균 연산 시간': []
            , '오버헤드 시간': []
            , '처리율': []}
    
    # 실험 30회 반복 실행
    for i in range(30):
        
        # 작업이 누락 없이 진행 됐는 지 확인하기 위한 변수
        count = 0
        
        # 누적 연산 시간
        accum_compute_time = 0
        
        # batch 사이즈
        batch_size = 2

        # 작업 시작 시간
        start_time = time.perf_counter()
        
        # 멀티 프로세스 구동
        with ProcessPoolExecutor(max_workers=n_worker) as ex:
            futures = [ex.submit(job_batch, batch_size, n_tasks) for k in chunks(n_tasks, batch_size)]            
            
            for future in as_completed(futures):
                out, submit_time = future.result()
                count += out
                accum_compute_time += submit_time
                
                    
        # 작업이 끝난 시간
        end_time = time.perf_counter()
        
        # 총 실행시간
        run_time = end_time - start_time
        
        # 연산 시간
        avg_accum_compute_time = accum_compute_time / n_worker
        
        #오버헤드 시간
        overhead_time = run_time - avg_accum_compute_time        
        
        # 처리율
        throughput = count/run_time

        print(f"총 실행횟수: {count}")    
        print(f"총 실행시간: {run_time}")
        print(f"평균 연산 시간: {avg_accum_compute_time}")        
        print(f"오버헤드 시간 :{overhead_time}")
        print(f"처리율: {throughput}")

        data['총 실행횟수'].append(count)
        data['총 실행시간'].append(run_time)
        data['평균 연산 시간'].append(avg_accum_compute_time)
        data['오버헤드 시간'].append(overhead_time)
        data['처리율'].append(throughput)
    
    # 실험 결과 엑셀에 저장    
    df = pd.DataFrame(data)
    df.to_excel('/Users/wnwlt/Desktop/실험 결과/batchMultiprocess2.xlsx', index=True, sheet_name='process')
    

if __name__ == "__main__":
    
    main()
