import threading
import queue
import time
import random
import pandas as pd


def producer(n_tasks: int, q: queue.Queue):
    
    for i in range(n_tasks):
        
        input_time = time.perf_counter()
        
        q.put((i,input_time))
    
def consumer(q: queue.Queue, max_queue_size_observed: list, count: list, latencies: list, lock: threading.Lock):
    
    while True:
        
        current_q_size = q.qsize()
        
        if current_q_size > max_queue_size_observed[0]:
            max_queue_size_observed[0] = current_q_size
        

        time.sleep(random.uniform(0.02, 0.05))
        item, input_time = q.get()
        
        try:
            if item is None:
                break
            else:
                time.sleep(random.uniform(0.02, 0.05))
                output_time = time.perf_counter()
                latency = output_time - input_time
                with lock:
                    count[0] += 1
                    latencies.append(latency)
        finally:
            q.task_done()
            
    

def main():
    
    n_tasks = 2000
    n_thread = 2
    q_size = 128
    lock = threading.Lock()
    
    data = {'실행 횟수': []
            , '총 실행시간': []
            , '처리율': []
            , '상위 5% 지연율': []}
    
    for j in range(30):
        
        max_queue_size_observed = [0]
        count = [0]
        latencies = []
        
        q = queue.Queue(maxsize=q_size)
        
        ths = []
        
        # 생성자부터 시작하면 첫 실행의 지연율이 올라 결과에 영향을 줄 수 있으므로
        # 소비자부터 시작

        th_p = threading.Thread(target=producer, args=(n_tasks, q))
        
        for i in range(n_thread):
            ths.append(threading.Thread(target=consumer, args=(q, max_queue_size_observed, count, latencies, lock)))
        
        start_time = time.perf_counter()
        
        for th in ths:
            th.start()
            
        th_p.start()
            
        th_p.join() 

        for i in range(n_thread):
            q.put((None, None))   
        
        for th in ths:
            th.join()    
            
        q.join()
        
        end_time = time.perf_counter()
        
        run_time = end_time - start_time
        throughput = count[0] / run_time
        latencies.sort()
        p95_latency = latencies[int(0.95 * (len(latencies) - 1))] if latencies else None
        
        
        print(f"총 실행횟수: {count[0]}")
        print(f"촐 실행시간: {run_time}")
        print(f"최대 큐 사이즈:{max_queue_size_observed[0]}")
        print(f"처리율: {throughput}")
        print(f"지연율 상위 5%: {p95_latency}")
        
        data['실행 횟수'].append(count[0])
        data['총 실행시간'].append(run_time)
        data['처리율'].append(throughput)
        data['상위 5% 지연율'].append(p95_latency)
        
    df = pd.DataFrame(data)
    df.to_excel('/Users/wnwlt/Desktop/실험 결과/backpressure_qsize128.xlsx', index=True, sheet_name='backpressure')
    
        


if __name__ == "__main__":
    main()
