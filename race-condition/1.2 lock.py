import threading
import time
import pandas as pd

count = 0

# 작업 내용
def work(n_task: int, lock: threading.Lock):
    
    global count
    
    for i in range(n_task):
        with lock:
            tmp = count
            time.sleep(0)
            count = tmp +1

def main():
    
    #데이터 엑셀에 저장용
    data = {'실행 횟수': []
            , '총 실행시간': []
            , '처리율': []}
    
    n_thread = 4
    n_task = 1000000 // n_thread
    
    # 공유 자원 접근을 위한 lock 선언
    lock = threading.Lock()
    
    for i in range(30):
        
        global count
        count = 0
        
        ths = []
        
        # 스레드 생성
        for i in range(n_thread):
            ths.append(threading.Thread(target=work, args=(n_task, lock)))
        
        # 시작시간
        start_time = time.perf_counter() 
        
        # 스레드 실행
        for th in ths:
            th.start()
            
        for th in ths:
            th.join()
        
        # 작업 시간과 처리율
        end_time = time.perf_counter()
        run_time = end_time - start_time
        throughput = count / run_time
            
        print(f"실행 횟수:{count}")
        print(f"총 실행시간{run_time}")
        print(f"처리율: {throughput}")
        
        # 엑셀 저장을 위해 추가
        data['실행 횟수'].append(count)
        data['총 실행시간'].append(run_time)
        data['처리율'].append(throughput)
    
    # 엑셀에 저장    
        
    df = pd.DataFrame(data)
    df.to_excel('/Users/wnwlt/Desktop/실험 결과/lock.xlsx', index=True, sheet_name='lock')    
    

if __name__ == "__main__":
    main()