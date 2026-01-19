import threading
import time
import pandas as pd

count = 0


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
    
    lock = threading.Lock()
    
    for i in range(30):
        
        global count
        count = 0
        
        ths = []
        
        for i in range(n_thread):
            ths.append(threading.Thread(target=work, args=(n_task, lock)))
        
        start_time = time.perf_counter() 
        
        for th in ths:
            th.start()
            
        for th in ths:
            th.join()
        
        
        end_time = time.perf_counter()
        run_time = end_time - start_time
        throughput = count / run_time
            
        print(f"실행 횟수:{count}")
        print(f"총 실행시간{run_time}")
        print(f"처리율: {throughput}")
        
        data['실행 횟수'].append(count)
        data['총 실행시간'].append(run_time)
        data['처리율'].append(throughput)
        
        
    df = pd.DataFrame(data)
    df.to_excel('/Users/wnwlt/Desktop/실험 결과/lock.xlsx', index=True, sheet_name='lock')    
    

if __name__ == "__main__":
    main()
