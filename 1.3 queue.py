import threading
import time
import queue
import pandas as pd


def work(n_task: int, q: queue.Queue):
    
    tmp = 0
    
    for i in range(n_task):
        time.sleep(0)
        tmp += 1
    
    q.put(tmp)

def main():
    
    n_thread = 4
    n_task = 1000000 // n_thread
    
    #데이터 엑셀에 저장용
    data = {'실행 횟수': []
            , '총 실행시간': []
            , '처리율': []}
    
    for i in range(30):
        
        count = 0
        
        q = queue.Queue()
        
        ths = []
        
        for i in range(n_thread):
            ths.append(threading.Thread(target=work, args=(n_task, q)))
        
        start_time = time.perf_counter() 
        
        for th in ths:
            th.start()
            
        for th in ths:
            th.join()
        
        
        end_time = time.perf_counter()
        run_time = end_time - start_time  

        
        for i in range(n_thread):
            count += q.get()
            
        throughput = count / run_time
            
        print(f"실행 횟수:{count}")
        print(f"총 실행 시간{run_time}")
        print(f"처리율: {throughput}")
        
        data['실행 횟수'].append(count)
        data['총 실행시간'].append(run_time)
        data['처리율'].append(throughput)
        
    df = pd.DataFrame(data)
    df.to_excel('/Users/wnwlt/Desktop/실험 결과/queue.xlsx', index=True, sheet_name='queue')
        
    

if __name__ == "__main__":
    main()