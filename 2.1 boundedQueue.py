import threading
import queue
import time
import random
import pandas as pd


def producer(n_tasks: int, in_q: queue.Queue):
    
    for i in range(n_tasks):
        
        input_time = time.perf_counter()
        producer_enlapsed_time = time.perf_counter() - input_time
        in_q.put((i,input_time, producer_enlapsed_time))
        
    
def consumer(in_q: queue.Queue, out_q: queue.Queue):
    
    out_count = 0
    out_latencies = []
    out_producer_enlapsed_time = 0
    out_consumer_enlapsed_time = 0
    out_accum_queue_size_observed = 0
    
    while True:
        
        current_q_size = in_q.qsize()
        out_accum_queue_size_observed += current_q_size

        time.sleep(random.uniform(0.02, 0.05))
        item, input_time, producer_enlapsed_time = in_q.get()
        
        try:
            if item is None:
                break
            else:
                output_time = time.perf_counter()
                
                time.sleep(random.uniform(0.02, 0.05))
                
                consumer_enlapsed_time = time.perf_counter() - output_time
                
                latency = output_time - input_time
                
                out_count += 1
                out_latencies.append(latency)
                out_producer_enlapsed_time += producer_enlapsed_time
                out_consumer_enlapsed_time += consumer_enlapsed_time
        finally:
            in_q.task_done()
            
    out_q.put((out_count, out_latencies, out_accum_queue_size_observed, out_producer_enlapsed_time, out_consumer_enlapsed_time))
    

def main():
    
    n_tasks = 2000
    n_thread = 2
    q_size = 128
    
    data = {'실행 횟수': []
            , '총 실행시간': []
            , '평균 큐 사이즈': []
            , '생산자 처리율': []
            , '소비자 처리율' : []
            , '처리율': []
            , '상위 5% 지연율': []}
    
    for j in range(30):
        
        count = 0
        latencies = []
        accum_queue_size_observed = 0
        producer_enlapsed_time = 0
        consumer_enlapsed_time = 0
        
        in_q = queue.Queue(maxsize=q_size)
        out_q = queue.Queue()
        
        ths = []
        
        # 생성자부터 시작하면 첫 실행의 지연율이 올라 결과에 영향을 줄 수 있으므로
        # 소비자부터 시작

        th_p = threading.Thread(target=producer, args=(n_tasks, in_q))
        
        for i in range(n_thread):
            ths.append(threading.Thread(target=consumer, args=(in_q, out_q)))
        
        start_time = time.perf_counter()
        
        for th in ths:
            th.start()
            
        th_p.start()
            
        th_p.join() 

        for i in range(n_thread):
            in_q.put((None, None, None))   
        
        for th in ths:
            th.join()    
        
        in_q.join()
        
        end_time = time.perf_counter()
        
        for out in range(n_thread):
            
            out_count, out_latencies, out_accum_queue_size_observed, out_producer_enlapsed_time, out_consumer_enlapsed_time = out_q.get()
            
            count += out_count
            latencies += out_latencies
            accum_queue_size_observed += out_accum_queue_size_observed

            producer_enlapsed_time += out_producer_enlapsed_time
            consumer_enlapsed_time += out_consumer_enlapsed_time
            out_q.task_done()
                 
        out_q.join()
        
        avg_queue_size_observed = accum_queue_size_observed / n_tasks
        
        producer_throughput = n_tasks / producer_enlapsed_time
        consumer_throughput = n_tasks / consumer_enlapsed_time
        
        run_time = end_time - start_time
        throughput = count / run_time
        
        latencies.sort()
        p95_latency = latencies[int(0.95 * (len(latencies) - 1))] if latencies else None
        
        
        print(f"총 실행횟수: {count}")
        print(f"총 실행시간: {run_time}")
        print(f"평균 큐 사이즈:{avg_queue_size_observed}")
        print(f"생산자 처리율: {producer_throughput}")
        print(f"소비자 처리율: {consumer_throughput}")
        print(f"처리율: {throughput}")
        print(f"지연율 상위 5%: {p95_latency}")
        
        data['실행 횟수'].append(count)
        data['총 실행시간'].append(run_time)
        data['평균 큐 사이즈'].append(avg_queue_size_observed)
        data['생산자 처리율'].append(producer_throughput)
        data['소비자 처리율'].append(consumer_throughput)
        data['처리율'].append(throughput)
        data['상위 5% 지연율'].append(p95_latency)
        
    df = pd.DataFrame(data)
    df.to_excel('/Users/wnwlt/Desktop/실험 결과/backpressure_qsize128.xlsx', index=True, sheet_name='backpressure')
    
        


if __name__ == "__main__":
    main()