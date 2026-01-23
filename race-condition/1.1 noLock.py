import threading
import time
import pandas as pd

# 작업 횟수 카운트 공유자원
count = 0

# 작업 실행할 때마다 count + 1
def work(n_task: int):
    
    global count
    
    for i in range(n_task):
        tmp = count
        time.sleep(0)
        count = tmp +1

def main():
    
    #데이터 엑셀 저장용
    data = {'실행 횟수': []
            , '총 실행 시간': []
            , '처리율': []}
    
    # 스레드 개수
    n_thread = 4
    
    # 스레드 당 일 수
    n_task = 1000000 // n_thread
    
    # 실험을 위해 30번 반복
    for i in range(30):
        
        
        global count
        count = 0
        
        # 스레드 동시에 실행을 위한 리스트
        ths = []
        
        # 스레드 추가
        for i in range(n_thread):
            ths.append(threading.Thread(target=work, args=(n_task,)))
        
        # 작업 시작 시간
        start_time = time.perf_counter()
        
        # 작업 시작
        for th in ths:
            th.start()
        
        # 다 쓴 스레드 종료
        for th in ths:
            th.join()
        
        # 종료 시간
        end_time = time.perf_counter()
        
        # 작업 시간과 처리율
        run_time = end_time - start_time
        throughput = count / run_time
            
        print(f"실행 횟수:{count}")
        print(f"총 실행 시간{run_time}")
        print(f"처리율: {throughput}")
        
        # 엑셀 저장을 위해 추가
        data['실행 횟수'].append(count)
        data['총 실행 시간'].append(run_time)
        data['처리율'].append(throughput)
    
    # 엑셀에 데이터 저장   
    df = pd.DataFrame(data)
    df.to_excel('/Users/wnwlt/Desktop/실험 결과/noLock.xlsx', index=True, sheet_name='noLock')
    

if __name__ == "__main__":
    main()